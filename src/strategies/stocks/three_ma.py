"""
Strategy 3.13: Three Moving Averages
Using 3 MAs to filter false signals.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class ThreeMARequest(BaseModel):
    prices: list[float]
    short_period: int = Field(5)
    medium_period: int = Field(20)
    long_period: int = Field(50)
    ma_type: str = Field("sma")


class ThreeMAResponse(BaseModel):
    strategy: str = "three_ma"
    signal: int
    short_ma: float
    medium_ma: float
    long_ma: float
    trend: str


def calc_ma(prices: np.ndarray, period: int, ma_type: str) -> float:
    if ma_type.lower() == "ema":
        alpha = 2 / (period + 1)
        ema = prices[0]
        for p in prices[1:]:
            ema = alpha * p + (1 - alpha) * ema
        return float(ema)
    return float(np.mean(prices[-period:]))


@router.post("/three-ma", response_model=ThreeMAResponse)
def three_ma(req: ThreeMARequest):
    prices = np.array(req.prices)
    short_ma = calc_ma(prices, req.short_period, req.ma_type)
    medium_ma = calc_ma(prices, req.medium_period, req.ma_type)
    long_ma = calc_ma(prices, req.long_period, req.ma_type)

    if short_ma > medium_ma > long_ma:
        signal = 1
        trend = "strong_uptrend"
    elif short_ma < medium_ma < long_ma:
        signal = -1
        trend = "strong_downtrend"
    elif short_ma > medium_ma and medium_ma < long_ma:
        signal = 0
        trend = "consolidating"
    else:
        signal = 0
        trend = "mixed"

    return ThreeMAResponse(
        signal=signal,
        short_ma=short_ma,
        medium_ma=medium_ma,
        long_ma=long_ma,
        trend=trend,
    )
