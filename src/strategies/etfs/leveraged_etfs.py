"""
Strategy 4.5: Leveraged ETFs (LETFs)
Exploiting negative drift by shorting 2x/3x inverse pairs.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/etfs", tags=["etfs"])


class LeveragedETFsRequest(BaseModel):
    bull_prices: list[float] = Field(..., description="Bull LETF price series (e.g., 3x)")
    bear_prices: list[float] = Field(..., description="Bear LETF price series (e.g., -3x)")
    underlying_prices: list[float] = Field(..., description="Underlying index prices")
    lookback: int = Field(20)


class LeveragedETFsResponse(BaseModel):
    strategy: str = "leveraged_etfs"
    signal: str = Field(..., description="short_both, long_both, or neutral")
    bull_decay: float
    bear_decay: float
    combined_decay: float
    hedge_ratio: float


@router.post("/leveraged-etfs", response_model=LeveragedETFsResponse)
def leveraged_etfs(req: LeveragedETFsRequest):
    bull = np.array(req.bull_prices[-req.lookback:])
    bear = np.array(req.bear_prices[-req.lookback:])
    underlying = np.array(req.underlying_prices[-req.lookback:])

    underlying_ret = (underlying[-1] - underlying[0]) / underlying[0]
    bull_ret = (bull[-1] - bull[0]) / bull[0]
    bear_ret = (bear[-1] - bear[0]) / bear[0]

    expected_bull_ret = 3 * underlying_ret
    expected_bear_ret = -3 * underlying_ret

    bull_decay = float(expected_bull_ret - bull_ret)
    bear_decay = float(expected_bear_ret - bear_ret)
    combined_decay = bull_decay + bear_decay

    bull_value = bull[-1]
    bear_value = bear[-1]
    hedge_ratio = bull_value / bear_value if bear_value > 0 else 1.0

    if combined_decay > 0.01:
        signal = "short_both"
    elif combined_decay < -0.01:
        signal = "long_both"
    else:
        signal = "neutral"

    return LeveragedETFsResponse(
        signal=signal,
        bull_decay=bull_decay,
        bear_decay=bear_decay,
        combined_decay=combined_decay,
        hedge_ratio=hedge_ratio,
    )
