"""
Strategy 11.4: CDO Carry (Tranche Hedging)
Hedge tranche positions using other tranches to isolate specific risk exposures.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class TranchePosition(BaseModel):
    name: str = Field(..., description="Tranche name")
    spread: float = Field(..., description="Current spread (bps)")
    delta: float = Field(..., description="Sensitivity to credit spread moves")
    attachment: float = Field(..., description="Attachment point")
    detachment: float = Field(..., description="Detachment point")
    notional: float = Field(..., description="Position notional")
    is_long: bool = Field(True, description="True if long position")


class CDOTrancheHedgingRequest(BaseModel):
    positions: list[TranchePosition] = Field(..., description="Current tranche positions")
    hedge_candidates: list[TranchePosition] = Field(..., description="Available hedging tranches")
    target_delta: float = Field(0.0, description="Target portfolio delta")
    max_hedge_cost: float = Field(50, description="Max acceptable hedge cost (bps)")
    correlation: float = Field(0.3, description="Default correlation")


class HedgeRecommendation(BaseModel):
    hedge_tranche: str
    hedge_notional: float
    hedge_direction: str
    cost_bps: float
    delta_reduction: float


class CDOTrancheHedgingResponse(BaseModel):
    strategy: str = "cdo_tranche_hedging"
    signal: int = Field(..., description="1=implement hedge, 0=no action needed")
    current_delta: float = Field(..., description="Current portfolio delta")
    target_delta: float = Field(..., description="Target delta")
    hedge_recommendations: list[HedgeRecommendation]
    residual_delta: float = Field(..., description="Delta after hedging")
    total_hedge_cost: float = Field(..., description="Total cost of hedge (bps)")
    net_carry_after_hedge: float = Field(..., description="Net carry after hedge costs")


@router.post("/cdo-tranche-hedging", response_model=CDOTrancheHedgingResponse)
def cdo_tranche_hedging(req: CDOTrancheHedgingRequest):
    current_delta = sum(
        p.delta * p.notional * (1 if p.is_long else -1)
        for p in req.positions
    )
    
    current_carry = sum(
        p.spread * p.notional / 10000 * (1 if p.is_long else -1)
        for p in req.positions
    )
    
    delta_to_hedge = current_delta - req.target_delta
    
    recommendations = []
    remaining_delta = delta_to_hedge
    total_hedge_cost = 0.0
    
    sorted_candidates = sorted(
        req.hedge_candidates,
        key=lambda c: c.spread / c.delta if c.delta > 0 else float('inf')
    )
    
    for candidate in sorted_candidates:
        if abs(remaining_delta) < 0.01:
            break
        
        if candidate.delta <= 0:
            continue
        
        hedge_notional = abs(remaining_delta) / candidate.delta
        hedge_direction = "short" if delta_to_hedge > 0 else "long"
        
        cost_bps = candidate.spread if hedge_direction == "short" else -candidate.spread
        
        if cost_bps > req.max_hedge_cost:
            continue
        
        delta_reduction = candidate.delta * hedge_notional
        
        recommendations.append(HedgeRecommendation(
            hedge_tranche=candidate.name,
            hedge_notional=float(hedge_notional),
            hedge_direction=hedge_direction,
            cost_bps=float(cost_bps),
            delta_reduction=float(delta_reduction),
        ))
        
        remaining_delta -= delta_reduction * (1 if delta_to_hedge > 0 else -1)
        total_hedge_cost += abs(cost_bps * hedge_notional / 10000)
    
    residual_delta = current_delta - sum(r.delta_reduction * (1 if r.hedge_direction == "short" else -1) for r in recommendations)
    net_carry = current_carry - total_hedge_cost
    
    signal = 1 if recommendations and total_hedge_cost <= req.max_hedge_cost else 0
    
    return CDOTrancheHedgingResponse(
        signal=signal,
        current_delta=float(current_delta),
        target_delta=req.target_delta,
        hedge_recommendations=recommendations,
        residual_delta=float(residual_delta),
        total_hedge_cost=float(total_hedge_cost),
        net_carry_after_hedge=float(net_carry),
    )
