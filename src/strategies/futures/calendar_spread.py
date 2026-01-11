"""
Strategy 10.2: Calendar Spread
Long near-term, short far-term futures (or vice versa) to capture term structure changes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/futures", tags=["futures"])


class CalendarSpreadRequest(BaseModel):
    symbol: str = Field(..., description="Underlying futures symbol")
    near_price: float = Field(..., description="Near-term contract price")
    far_price: float = Field(..., description="Far-term contract price")
    near_days_to_expiry: int = Field(..., description="Days to near contract expiry")
    far_days_to_expiry: int = Field(..., description="Days to far contract expiry")
    spot_price: float = Field(None, description="Optional: current spot price")
    carry_cost: float = Field(0.05, description="Annual carry cost (storage + financing)")
    historical_spread_mean: float = Field(None, description="Optional: historical mean spread")
    historical_spread_std: float = Field(None, description="Optional: historical spread std dev")


class CalendarSpreadResponse(BaseModel):
    strategy: str = "calendar_spread"
    signal: int = Field(..., description="1=long near/short far, -1=short near/long far, 0=neutral")
    current_spread: float = Field(..., description="Current spread (near - far)")
    spread_annualized: float = Field(..., description="Annualized spread rate")
    theoretical_spread: float = Field(..., description="Theoretical fair spread based on carry")
    spread_zscore: float = Field(None, description="Z-score vs historical (if provided)")
    contango: bool = Field(..., description="True if market in contango (far > near)")
    roll_yield: float = Field(..., description="Expected roll yield if holding to near expiry")


@router.post("/calendar-spread", response_model=CalendarSpreadResponse)
def calendar_spread(req: CalendarSpreadRequest):
    current_spread = req.near_price - req.far_price
    
    days_between = req.far_days_to_expiry - req.near_days_to_expiry
    if days_between > 0:
        spread_annualized = (current_spread / req.near_price) * (365 / days_between)
    else:
        spread_annualized = 0.0
    
    if req.spot_price:
        base_price = req.spot_price
    else:
        base_price = req.near_price
    
    near_theoretical = base_price * (1 + req.carry_cost * req.near_days_to_expiry / 365)
    far_theoretical = base_price * (1 + req.carry_cost * req.far_days_to_expiry / 365)
    theoretical_spread = near_theoretical - far_theoretical
    
    contango = req.far_price > req.near_price
    
    if days_between > 0:
        roll_yield = (req.far_price - req.near_price) / req.near_price * (365 / days_between)
    else:
        roll_yield = 0.0
    
    spread_zscore = None
    if req.historical_spread_mean is not None and req.historical_spread_std is not None:
        if req.historical_spread_std > 0:
            spread_zscore = (current_spread - req.historical_spread_mean) / req.historical_spread_std
    
    signal = 0
    if spread_zscore is not None:
        if spread_zscore > 2.0:
            signal = -1
        elif spread_zscore < -2.0:
            signal = 1
    else:
        mispricing = current_spread - theoretical_spread
        threshold = abs(theoretical_spread) * 0.2 if theoretical_spread != 0 else base_price * 0.01
        if mispricing > threshold:
            signal = -1
        elif mispricing < -threshold:
            signal = 1
    
    return CalendarSpreadResponse(
        signal=signal,
        current_spread=float(current_spread),
        spread_annualized=float(spread_annualized),
        theoretical_spread=float(theoretical_spread),
        spread_zscore=float(spread_zscore) if spread_zscore is not None else None,
        contango=contango,
        roll_yield=float(roll_yield),
    )
