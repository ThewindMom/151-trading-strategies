"""
Strategy 11.7: Duration-Hedged MBS Trading
Mortgage-backed securities with duration hedging via Treasury futures.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/structured", tags=["structured"])


class MBSTradingRequest(BaseModel):
    mbs_price: float = Field(..., description="Current MBS price")
    mbs_coupon: float = Field(..., description="MBS coupon rate (annual)")
    mbs_duration: float = Field(..., description="Effective duration of MBS")
    mbs_convexity: float = Field(..., description="Negative convexity of MBS")
    treasury_yield: float = Field(..., description="Comparable Treasury yield")
    treasury_duration: float = Field(..., description="Treasury futures duration")
    prepayment_speed: float = Field(100.0, description="PSA prepayment speed")
    spread_threshold: float = Field(50.0, description="OAS threshold for entry (bps)")


class MBSTradingResponse(BaseModel):
    strategy: str = "mbs_trading"
    signal: int = Field(..., description="1=long MBS hedged, -1=avoid, 0=neutral")
    oas_spread: float = Field(..., description="Option-adjusted spread (bps)")
    hedge_ratio: float = Field(..., description="Treasury futures hedge ratio")
    duration_adjusted_return: float = Field(..., description="Expected return after hedge")
    prepayment_risk: str = Field(..., description="Prepayment risk level")


@router.post("/mbs-trading", response_model=MBSTradingResponse)
def mbs_trading(req: MBSTradingRequest):
    nominal_spread = (req.mbs_coupon - req.treasury_yield) * 10000
    convexity_cost = abs(req.mbs_convexity) * 10
    oas_spread = nominal_spread - convexity_cost

    hedge_ratio = req.mbs_duration / req.treasury_duration if req.treasury_duration > 0 else 0

    duration_adjusted_return = oas_spread / 100

    if req.prepayment_speed > 200:
        prepayment_risk = "high"
    elif req.prepayment_speed > 100:
        prepayment_risk = "moderate"
    else:
        prepayment_risk = "low"

    if oas_spread > req.spread_threshold and prepayment_risk != "high":
        signal = 1
    elif oas_spread < 0 or prepayment_risk == "high":
        signal = -1
    else:
        signal = 0

    return MBSTradingResponse(
        signal=signal,
        oas_spread=float(oas_spread),
        hedge_ratio=float(hedge_ratio),
        duration_adjusted_return=float(duration_adjusted_return),
        prepayment_risk=prepayment_risk,
    )
