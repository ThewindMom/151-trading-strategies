"""
Strategy 3.12: Two Moving Averages
Signal based on short-term MA crossing a long-term MA.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class TwoMARequest(BaseModel):
    prices: list[float] = Field(..., description="Price series")
    short_period: int = Field(10, description="Short MA period")
    long_period: int = Field(50, description="Long MA period")
    ma_type: str = Field("sma", description="sma or ema")


class TwoMAResponse(BaseModel):
    strategy: str = "two_ma"
    signal: int
    short_ma: float
    long_ma: float
    crossover: str = Field(..., description="golden_cross, death_cross, or none")


def calc_ma(prices: np.ndarray, period: int, ma_type: str) -> float:
    if ma_type.lower() == "ema":
        alpha = 2 / (period + 1)
        ema = prices[0]
        for p in prices[1:]:
            ema = alpha * p + (1 - alpha) * ema
        return float(ema)
    return float(np.mean(prices[-period:]))


@router.post("/two-ma", response_model=TwoMAResponse)
def two_ma(req: TwoMARequest):
    prices = np.array(req.prices)
    short_ma = calc_ma(prices, req.short_period, req.ma_type)
    long_ma = calc_ma(prices, req.long_period, req.ma_type)

    prev_prices = prices[:-1]
    prev_short_ma = calc_ma(prev_prices, req.short_period, req.ma_type)
    prev_long_ma = calc_ma(prev_prices, req.long_period, req.ma_type)

    crossover = "none"
    if prev_short_ma <= prev_long_ma and short_ma > long_ma:
        crossover = "golden_cross"
    elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
        crossover = "death_cross"

    signal = 1 if short_ma > long_ma else -1

    return TwoMAResponse(
        signal=signal,
        short_ma=short_ma,
        long_ma=long_ma,
        crossover=crossover,
    )
