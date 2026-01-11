"""
Strategy 10.4: Trend Following
Momentum weights based on sign of returns.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/futures", tags=["futures"])


class TrendAsset(BaseModel):
    symbol: str = Field(..., description="Futures symbol")
    prices: list[float] = Field(..., description="Price series")
    volatility: float = Field(None, description="Optional: annualized volatility for sizing")


class TrendFollowingRequest(BaseModel):
    assets: list[TrendAsset] = Field(..., description="List of futures assets")
    short_lookback: int = Field(20, description="Short-term lookback days")
    medium_lookback: int = Field(60, description="Medium-term lookback days")
    long_lookback: int = Field(120, description="Long-term lookback days")
    vol_target: float = Field(0.10, description="Target portfolio volatility")


class TrendPosition(BaseModel):
    symbol: str
    signal: int
    momentum_score: float
    weight: float
    short_trend: float
    medium_trend: float
    long_trend: float


class TrendFollowingResponse(BaseModel):
    strategy: str = "trend_following"
    positions: list[TrendPosition]
    long_assets: list[str]
    short_assets: list[str]
    net_exposure: float


@router.post("/trend-following", response_model=TrendFollowingResponse)
def trend_following(req: TrendFollowingRequest):
    positions = []
    long_assets = []
    short_assets = []

    for asset in req.assets:
        prices = np.array(asset.prices)

        if len(prices) >= req.short_lookback:
            short_ret = prices[-1] / prices[-req.short_lookback] - 1
        else:
            short_ret = 0

        if len(prices) >= req.medium_lookback:
            medium_ret = prices[-1] / prices[-req.medium_lookback] - 1
        else:
            medium_ret = 0

        if len(prices) >= req.long_lookback:
            long_ret = prices[-1] / prices[-req.long_lookback] - 1
        else:
            long_ret = 0

        short_signal = np.sign(short_ret)
        medium_signal = np.sign(medium_ret)
        long_signal = np.sign(long_ret)

        momentum_score = (short_signal + medium_signal + long_signal) / 3

        if asset.volatility and asset.volatility > 0:
            vol_scalar = req.vol_target / asset.volatility
        else:
            returns = np.diff(prices) / prices[:-1]
            vol = float(np.std(returns) * np.sqrt(252))
            vol_scalar = req.vol_target / vol if vol > 0 else 1.0

        weight = momentum_score * vol_scalar

        signal = int(np.sign(momentum_score))

        if signal > 0:
            long_assets.append(asset.symbol)
        elif signal < 0:
            short_assets.append(asset.symbol)

        positions.append(TrendPosition(
            symbol=asset.symbol,
            signal=signal,
            momentum_score=float(momentum_score),
            weight=float(weight),
            short_trend=float(short_ret),
            medium_trend=float(medium_ret),
            long_trend=float(long_ret),
        ))

    net_exposure = sum(p.weight for p in positions)

    return TrendFollowingResponse(
        positions=positions,
        long_assets=long_assets,
        short_assets=short_assets,
        net_exposure=net_exposure,
    )
