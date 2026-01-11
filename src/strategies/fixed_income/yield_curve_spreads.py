"""
Strategy 5.13: Yield Curve Spreads (Flatteners and Steepeners)
Trading the slope of the yield curve through long/short positions at different maturities.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class CurveBond(BaseModel):
    cusip: str
    maturity_years: float
    yield_to_maturity: float
    duration: float
    dv01: float = Field(..., description="Dollar value of 01 per $1M face")


class YieldCurveSpreadsRequest(BaseModel):
    short_end_bond: CurveBond = Field(..., description="Short maturity bond (e.g., 2Y)")
    long_end_bond: CurveBond = Field(..., description="Long maturity bond (e.g., 10Y)")
    current_spread: float = Field(..., description="Current yield spread in bps")
    historical_spread_mean: float = Field(..., description="Historical mean spread in bps")
    historical_spread_std: float = Field(..., description="Historical spread std dev in bps")
    notional: float = Field(10_000_000)
    trade_type: str = Field("auto", description="flattener, steepener, or auto")


class SpreadLeg(BaseModel):
    cusip: str
    position: str
    notional: float
    dv01_contribution: float


class YieldCurveSpreadsResponse(BaseModel):
    strategy: str = "yield_curve_spreads"
    trade_type: str
    current_spread: float
    z_score: float
    spread_direction: str
    short_notional: float
    long_notional: float
    hedge_ratio: float
    legs: list[SpreadLeg]
    target_spread: float
    expected_pnl_per_bp: float


@router.post("/yield-curve-spreads", response_model=YieldCurveSpreadsResponse)
def yield_curve_spreads(req: YieldCurveSpreadsRequest):
    z_score = (req.current_spread - req.historical_spread_mean) / req.historical_spread_std if req.historical_spread_std > 0 else 0
    
    if req.trade_type == "auto":
        if z_score > 1.0:
            trade_type = "flattener"
            spread_direction = "expect_tightening"
        elif z_score < -1.0:
            trade_type = "steepener"
            spread_direction = "expect_widening"
        else:
            trade_type = "neutral"
            spread_direction = "no_clear_signal"
    else:
        trade_type = req.trade_type
        spread_direction = "expect_tightening" if trade_type == "flattener" else "expect_widening"
    
    long_dv01 = req.long_end_bond.dv01
    short_dv01 = req.short_end_bond.dv01
    
    hedge_ratio = long_dv01 / short_dv01 if short_dv01 > 0 else 1.0
    
    long_notional = req.notional
    short_notional = long_notional * hedge_ratio
    
    if trade_type == "flattener":
        legs = [
            SpreadLeg(
                cusip=req.short_end_bond.cusip,
                position="short",
                notional=short_notional,
                dv01_contribution=-short_dv01 * (short_notional / 1_000_000),
            ),
            SpreadLeg(
                cusip=req.long_end_bond.cusip,
                position="long",
                notional=long_notional,
                dv01_contribution=long_dv01 * (long_notional / 1_000_000),
            ),
        ]
    elif trade_type == "steepener":
        legs = [
            SpreadLeg(
                cusip=req.short_end_bond.cusip,
                position="long",
                notional=short_notional,
                dv01_contribution=short_dv01 * (short_notional / 1_000_000),
            ),
            SpreadLeg(
                cusip=req.long_end_bond.cusip,
                position="short",
                notional=long_notional,
                dv01_contribution=-long_dv01 * (long_notional / 1_000_000),
            ),
        ]
    else:
        legs = []
    
    target_spread = req.historical_spread_mean
    
    spread_dv01 = long_dv01 * (long_notional / 1_000_000)
    expected_pnl_per_bp = spread_dv01
    
    return YieldCurveSpreadsResponse(
        trade_type=trade_type,
        current_spread=req.current_spread,
        z_score=z_score,
        spread_direction=spread_direction,
        short_notional=short_notional,
        long_notional=long_notional,
        hedge_ratio=hedge_ratio,
        legs=legs,
        target_spread=target_spread,
        expected_pnl_per_bp=expected_pnl_per_bp,
    )
