"""
Strategy 17.3: Liquidity Management
Optimal cash buffer sizing and allocation across liquidity tiers.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/cash", tags=["cash"])


class CashFlowData(BaseModel):
    expected_outflows_monthly: float = Field(..., description="Expected monthly cash outflows")
    outflow_volatility: float = Field(..., description="Standard deviation of monthly outflows")
    expected_inflows_monthly: float = Field(..., description="Expected monthly cash inflows")
    inflow_volatility: float = Field(..., description="Standard deviation of monthly inflows")


class LiquidityTier(BaseModel):
    tier_name: str = Field(..., description="Tier name (e.g., 'overnight', 't+1', 't+7')")
    yield_rate: float = Field(..., description="Annual yield rate (%)")
    liquidity_days: int = Field(..., description="Days to liquidate")
    current_allocation: float = Field(..., description="Current allocation amount")


class LiquidityManagementRequest(BaseModel):
    cash_flows: CashFlowData
    liquidity_tiers: list[LiquidityTier]
    total_portfolio_value: float = Field(..., description="Total portfolio value")
    confidence_level: float = Field(0.95, description="Confidence level for stress scenarios")
    stress_months: int = Field(3, description="Months of coverage for stress scenario")
    opportunity_cost_weight: float = Field(0.5, description="Weight on opportunity cost vs safety")


class TierAllocation(BaseModel):
    tier_name: str
    current_allocation: float
    optimal_allocation: float
    adjustment: float
    yield_contribution: float


class LiquidityManagementResponse(BaseModel):
    strategy: str = "liquidity_management"
    signal: int = Field(..., description="1=increase cash, -1=deploy cash, 0=maintain")
    tier_allocations: list[TierAllocation]
    optimal_cash_buffer: float
    current_cash_buffer: float
    buffer_adequacy_ratio: float
    expected_yield: float
    stress_coverage_months: float


@router.post("/liquidity-management", response_model=LiquidityManagementResponse)
def liquidity_management(req: LiquidityManagementRequest):
    cf = req.cash_flows
    
    net_outflow = cf.expected_outflows_monthly - cf.expected_inflows_monthly
    net_volatility = np.sqrt(cf.outflow_volatility**2 + cf.inflow_volatility**2)
    
    z_score = 1.645 if req.confidence_level == 0.95 else 2.326
    stress_outflow = net_outflow + z_score * net_volatility
    
    min_buffer = max(0, stress_outflow * req.stress_months)
    
    tier_yields = np.array([t.yield_rate for t in req.liquidity_tiers])
    tier_days = np.array([t.liquidity_days for t in req.liquidity_tiers])
    
    liquidity_weights = 1 / (tier_days + 1)
    yield_weights = tier_yields / (np.sum(tier_yields) + 0.001)
    
    combined_weights = (
        req.opportunity_cost_weight * yield_weights +
        (1 - req.opportunity_cost_weight) * liquidity_weights
    )
    combined_weights = combined_weights / np.sum(combined_weights)
    
    optimal_allocations = min_buffer * combined_weights
    
    overnight_idx = next((i for i, t in enumerate(req.liquidity_tiers) if t.liquidity_days == 0), 0)
    overnight_min = cf.expected_outflows_monthly * 0.5
    if optimal_allocations[overnight_idx] < overnight_min:
        deficit = overnight_min - optimal_allocations[overnight_idx]
        optimal_allocations[overnight_idx] = overnight_min
        other_indices = [i for i in range(len(optimal_allocations)) if i != overnight_idx]
        if other_indices:
            for i in other_indices:
                optimal_allocations[i] -= deficit / len(other_indices)
            optimal_allocations = np.maximum(optimal_allocations, 0)
    
    current_total = sum(t.current_allocation for t in req.liquidity_tiers)
    optimal_total = float(np.sum(optimal_allocations))
    
    tier_allocations = []
    for i, t in enumerate(req.liquidity_tiers):
        yield_contrib = optimal_allocations[i] * (t.yield_rate / 100)
        tier_allocations.append(TierAllocation(
            tier_name=t.tier_name,
            current_allocation=t.current_allocation,
            optimal_allocation=float(optimal_allocations[i]),
            adjustment=float(optimal_allocations[i] - t.current_allocation),
            yield_contribution=float(yield_contrib),
        ))
    
    expected_yield = sum(ta.yield_contribution for ta in tier_allocations)
    buffer_adequacy = current_total / min_buffer if min_buffer > 0 else float('inf')
    stress_coverage = current_total / stress_outflow if stress_outflow > 0 else float('inf')
    
    if buffer_adequacy < 0.8:
        signal = 1
    elif buffer_adequacy > 1.5:
        signal = -1
    else:
        signal = 0
    
    return LiquidityManagementResponse(
        signal=signal,
        tier_allocations=tier_allocations,
        optimal_cash_buffer=optimal_total,
        current_cash_buffer=current_total,
        buffer_adequacy_ratio=float(buffer_adequacy),
        expected_yield=float(expected_yield),
        stress_coverage_months=float(stress_coverage),
    )
