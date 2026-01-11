"""
Strategy 15.2: Active Distressed Investing
Activist approach to distressed companies - acquiring controlling positions to influence restructuring.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/distressed", tags=["distressed"])


class ActiveDistressedRequest(BaseModel):
    current_price: float = Field(..., description="Current security price (cents on dollar)")
    target_ownership_pct: float = Field(..., description="Target ownership percentage (0-100)")
    total_debt_outstanding: float = Field(..., description="Total debt outstanding ($M)")
    enterprise_value: float = Field(..., description="Estimated enterprise value ($M)")
    operational_improvement_pct: float = Field(..., description="Expected operational improvement (%)")
    restructuring_timeline_months: float = Field(..., description="Expected restructuring timeline")
    legal_advisory_costs: float = Field(..., description="Legal/advisory costs ($M)")
    current_ebitda: float = Field(..., description="Current EBITDA ($M)")
    target_ebitda_multiple: float = Field(6.0, description="Target exit EBITDA multiple")


class ActiveDistressedResponse(BaseModel):
    strategy: str = "active_distressed"
    signal: int = Field(..., description="1=pursue activist position, -1=avoid, 0=neutral")
    position_cost: float = Field(..., description="Cost to acquire target position ($M)")
    implied_recovery: float = Field(..., description="Implied recovery value (cents on dollar)")
    upside_with_activism: float = Field(..., description="Upside from operational changes (%)")
    irr_estimate: float = Field(..., description="Estimated IRR (%)")
    control_premium: float = Field(..., description="Value of control/influence ($M)")


@router.post("/active-distressed", response_model=ActiveDistressedResponse)
def active_distressed(req: ActiveDistressedRequest):
    position_cost = (req.target_ownership_pct / 100) * req.total_debt_outstanding * (req.current_price / 100)
    total_investment = position_cost + req.legal_advisory_costs

    base_recovery = (req.enterprise_value / req.total_debt_outstanding) * 100 if req.total_debt_outstanding > 0 else 0

    improved_ebitda = req.current_ebitda * (1 + req.operational_improvement_pct / 100)
    improved_ev = improved_ebitda * req.target_ebitda_multiple
    improved_recovery = (improved_ev / req.total_debt_outstanding) * 100 if req.total_debt_outstanding > 0 else 0

    implied_recovery = min(100, improved_recovery)

    upside_with_activism = ((improved_recovery - base_recovery) / base_recovery * 100) if base_recovery > 0 else 0

    exit_value = (req.target_ownership_pct / 100) * req.total_debt_outstanding * (implied_recovery / 100)
    total_return = (exit_value - total_investment) / total_investment if total_investment > 0 else 0

    years = req.restructuring_timeline_months / 12
    irr_estimate = ((1 + total_return) ** (1 / years) - 1) * 100 if years > 0 and total_return > -1 else 0

    control_premium = (improved_ev - req.enterprise_value) * (req.target_ownership_pct / 100)

    if irr_estimate > 25 and implied_recovery > req.current_price * 1.5:
        signal = 1
    elif irr_estimate < 10 or implied_recovery < req.current_price:
        signal = -1
    else:
        signal = 0

    return ActiveDistressedResponse(
        signal=signal,
        position_cost=float(position_cost),
        implied_recovery=float(implied_recovery),
        upside_with_activism=float(upside_with_activism),
        irr_estimate=float(irr_estimate),
        control_premium=float(control_premium),
    )
