"""
Strategy 11.6: CDO Curve Trades
Trade across CDO tranches to capture relative value from spread curve movements.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class TrancheCurvePoint(BaseModel):
    name: str = Field(..., description="Tranche name")
    attachment: float = Field(..., description="Attachment point")
    detachment: float = Field(..., description="Detachment point")
    current_spread: float = Field(..., description="Current spread (bps)")
    historical_spread: float = Field(..., description="Historical average spread (bps)")
    spread_duration: float = Field(..., description="Spread duration (years)")


class CDOCurveTradesRequest(BaseModel):
    tranches: list[TrancheCurvePoint] = Field(..., description="Tranches across the capital structure")
    expected_spread_move: float = Field(0, description="Expected parallel spread move (bps)")
    curve_steepening: float = Field(0, description="Expected curve steepening (bps, equity vs senior)")
    holding_period_days: int = Field(90, description="Holding period")
    max_position_size: float = Field(10_000_000, description="Max position per tranche")


class CurveTradeRecommendation(BaseModel):
    trade_type: str
    long_tranche: str
    short_tranche: str
    long_notional: float
    short_notional: float
    expected_pnl: float
    carry: float
    spread_dv01: float


class CDOCurveTradesResponse(BaseModel):
    strategy: str = "cdo_curve_trades"
    signal: int = Field(..., description="1=execute curve trade, 0=no trade")
    curve_trades: list[CurveTradeRecommendation]
    best_trade: str = Field(..., description="Best curve trade description")
    total_expected_pnl: float = Field(..., description="Total expected P&L")
    curve_richness: list[float] = Field(..., description="Rich/cheap score per tranche")
    steepness: float = Field(..., description="Current curve steepness (equity - senior spread)")


@router.post("/cdo-curve-trades", response_model=CDOCurveTradesResponse)
def cdo_curve_trades(req: CDOCurveTradesRequest):
    sorted_tranches = sorted(req.tranches, key=lambda t: t.attachment)
    
    richness = []
    for t in sorted_tranches:
        rich_cheap = (t.current_spread - t.historical_spread) / t.historical_spread * 100 if t.historical_spread > 0 else 0
        richness.append(float(rich_cheap))
    
    if len(sorted_tranches) >= 2:
        steepness = sorted_tranches[0].current_spread - sorted_tranches[-1].current_spread
    else:
        steepness = 0.0
    
    trades = []
    
    for i, t1 in enumerate(sorted_tranches):
        for j, t2 in enumerate(sorted_tranches):
            if i >= j:
                continue
            
            rich_diff = richness[i] - richness[j]
            
            if abs(rich_diff) < 5:
                continue
            
            if rich_diff > 0:
                long_t, short_t = t2, t1
                long_rich, short_rich = richness[j], richness[i]
            else:
                long_t, short_t = t1, t2
                long_rich, short_rich = richness[i], richness[j]
            
            duration_ratio = short_t.spread_duration / long_t.spread_duration if long_t.spread_duration > 0 else 1
            long_notional = req.max_position_size
            short_notional = long_notional * duration_ratio
            
            carry = (long_t.current_spread - short_t.current_spread) * long_notional / 10000 * (req.holding_period_days / 365)
            
            spread_convergence = (abs(rich_diff) / 100) * (long_t.current_spread + short_t.current_spread) / 2
            spread_pnl = spread_convergence * long_notional / 10000 * long_t.spread_duration
            
            expected_pnl = carry + spread_pnl * 0.5
            
            spread_dv01 = long_notional * long_t.spread_duration / 10000
            
            trades.append(CurveTradeRecommendation(
                trade_type="relative_value",
                long_tranche=long_t.name,
                short_tranche=short_t.name,
                long_notional=float(long_notional),
                short_notional=float(short_notional),
                expected_pnl=float(expected_pnl),
                carry=float(carry),
                spread_dv01=float(spread_dv01),
            ))
    
    if req.curve_steepening != 0:
        if len(sorted_tranches) >= 2:
            equity = sorted_tranches[0]
            senior = sorted_tranches[-1]
            
            if req.curve_steepening > 0:
                long_t, short_t = equity, senior
            else:
                long_t, short_t = senior, equity
            
            directional_pnl = abs(req.curve_steepening) * req.max_position_size / 10000 * equity.spread_duration
            
            trades.append(CurveTradeRecommendation(
                trade_type="curve_steepener" if req.curve_steepening > 0 else "curve_flattener",
                long_tranche=long_t.name,
                short_tranche=short_t.name,
                long_notional=float(req.max_position_size),
                short_notional=float(req.max_position_size),
                expected_pnl=float(directional_pnl),
                carry=float((long_t.current_spread - short_t.current_spread) * req.max_position_size / 10000 * req.holding_period_days / 365),
                spread_dv01=float(req.max_position_size * equity.spread_duration / 10000),
            ))
    
    trades.sort(key=lambda t: t.expected_pnl, reverse=True)
    
    total_pnl = sum(t.expected_pnl for t in trades[:3])
    best_trade = f"Long {trades[0].long_tranche}, Short {trades[0].short_tranche}" if trades else "No trade"
    
    signal = 1 if trades and trades[0].expected_pnl > 0 else 0
    
    return CDOCurveTradesResponse(
        signal=signal,
        curve_trades=trades[:5],
        best_trade=best_trade,
        total_expected_pnl=float(total_pnl),
        curve_richness=richness,
        steepness=float(steepness),
    )
