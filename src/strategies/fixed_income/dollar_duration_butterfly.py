"""
Strategy 5.6: Dollar Duration Butterfly
Combination of barbell and bullet to be duration-neutral, profiting from curve convexity changes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class ButterflyBond(BaseModel):
    cusip: str
    price: float
    yield_to_maturity: float
    maturity_years: float
    duration: float
    convexity: float
    dv01: float = Field(..., description="Dollar value of 01 (per $1M face)")


class DollarDurationButterflyRequest(BaseModel):
    short_wing: ButterflyBond = Field(..., description="Short maturity bond")
    body: ButterflyBond = Field(..., description="Medium maturity bond (body)")
    long_wing: ButterflyBond = Field(..., description="Long maturity bond")
    notional: float = Field(10_000_000, description="Notional for the body position")
    position_type: str = Field("sell_body", description="sell_body or buy_body")


class ButterflyLeg(BaseModel):
    cusip: str
    position: str
    notional: float
    dv01_contribution: float


class DollarDurationButterflyResponse(BaseModel):
    strategy: str = "dollar_duration_butterfly"
    position_type: str
    net_dv01: float
    net_convexity: float
    breakeven_shift: float
    legs: list[ButterflyLeg]
    expected_pnl_parallel_shift: float
    expected_pnl_curve_steepen: float
    expected_pnl_curve_flatten: float


@router.post("/dollar-duration-butterfly", response_model=DollarDurationButterflyResponse)
def dollar_duration_butterfly(req: DollarDurationButterflyRequest):
    body_notional = req.notional
    body_dv01 = req.body.dv01 * (body_notional / 1_000_000)
    
    wing_dv01_each = body_dv01 / 2
    
    short_notional = wing_dv01_each / (req.short_wing.dv01 / 1_000_000)
    long_notional = wing_dv01_each / (req.long_wing.dv01 / 1_000_000)
    
    short_dv01 = req.short_wing.dv01 * (short_notional / 1_000_000)
    long_dv01 = req.long_wing.dv01 * (long_notional / 1_000_000)
    
    if req.position_type == "sell_body":
        body_sign = -1
        wing_sign = 1
    else:
        body_sign = 1
        wing_sign = -1
    
    net_dv01 = wing_sign * short_dv01 + body_sign * body_dv01 + wing_sign * long_dv01
    
    short_convexity = req.short_wing.convexity * (short_notional / 1_000_000)
    body_convexity = req.body.convexity * (body_notional / 1_000_000)
    long_convexity = req.long_wing.convexity * (long_notional / 1_000_000)
    
    net_convexity = wing_sign * short_convexity + body_sign * body_convexity + wing_sign * long_convexity
    
    legs = [
        ButterflyLeg(
            cusip=req.short_wing.cusip,
            position="long" if wing_sign > 0 else "short",
            notional=short_notional,
            dv01_contribution=wing_sign * short_dv01,
        ),
        ButterflyLeg(
            cusip=req.body.cusip,
            position="short" if req.position_type == "sell_body" else "long",
            notional=body_notional,
            dv01_contribution=body_sign * body_dv01,
        ),
        ButterflyLeg(
            cusip=req.long_wing.cusip,
            position="long" if wing_sign > 0 else "short",
            notional=long_notional,
            dv01_contribution=wing_sign * long_dv01,
        ),
    ]
    
    parallel_shift_bps = 25
    expected_pnl_parallel = net_dv01 * parallel_shift_bps + 0.5 * net_convexity * (parallel_shift_bps ** 2) / 10000
    
    if req.position_type == "sell_body":
        expected_pnl_steepen = net_convexity * 1000
        expected_pnl_flatten = -net_convexity * 500
    else:
        expected_pnl_steepen = -net_convexity * 1000
        expected_pnl_flatten = net_convexity * 500
    
    breakeven_shift = abs(net_dv01 / net_convexity) * 100 if net_convexity != 0 else 0
    
    return DollarDurationButterflyResponse(
        position_type=req.position_type,
        net_dv01=net_dv01,
        net_convexity=net_convexity,
        breakeven_shift=breakeven_shift,
        legs=legs,
        expected_pnl_parallel_shift=expected_pnl_parallel,
        expected_pnl_curve_steepen=expected_pnl_steepen,
        expected_pnl_curve_flatten=expected_pnl_flatten,
    )
