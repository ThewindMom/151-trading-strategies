"""
Strategy 8.1: FX Moving Averages
Using Hodrick-Prescott filter for trend extraction.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fx", tags=["fx"])


class FxMovingAveragesRequest(BaseModel):
    prices: list[float] = Field(..., description="FX price series")
    hp_lambda: float = Field(1600, description="HP filter smoothing parameter")
    lookback: int = Field(100, description="Lookback period for filter")


class FxMovingAveragesResponse(BaseModel):
    strategy: str = "fx_moving_averages"
    signal: int = Field(..., description="1=long, -1=short, 0=neutral")
    current_price: float
    trend: float
    cycle: float
    trend_slope: float
    deviation_pct: float


def hp_filter(y: np.ndarray, lamb: float = 1600) -> tuple[np.ndarray, np.ndarray]:
    n = len(y)
    I = np.eye(n)
    D = np.zeros((n - 2, n))
    for i in range(n - 2):
        D[i, i] = 1
        D[i, i + 1] = -2
        D[i, i + 2] = 1
    trend = np.linalg.solve(I + lamb * D.T @ D, y)
    cycle = y - trend
    return trend, cycle


@router.post("/fx-moving-averages", response_model=FxMovingAveragesResponse)
def fx_moving_averages(req: FxMovingAveragesRequest):
    prices = np.array(req.prices[-req.lookback:])
    trend, cycle = hp_filter(prices, req.hp_lambda)

    current_price = float(prices[-1])
    current_trend = float(trend[-1])
    current_cycle = float(cycle[-1])

    trend_slope = float(trend[-1] - trend[-5]) if len(trend) >= 5 else 0.0
    deviation_pct = (current_price - current_trend) / current_trend * 100

    if trend_slope > 0 and current_price > current_trend:
        signal = 1
    elif trend_slope < 0 and current_price < current_trend:
        signal = -1
    else:
        signal = 0

    return FxMovingAveragesResponse(
        signal=signal,
        current_price=current_price,
        trend=current_trend,
        cycle=current_cycle,
        trend_slope=trend_slope,
        deviation_pct=deviation_pct,
    )
