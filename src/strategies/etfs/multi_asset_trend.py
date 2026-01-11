"""
Strategy 4.6: Multi-Asset Trend
Diversified long-only trend following across asset classes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/etfs", tags=["etfs"])


class MultiAssetTrendRequest(BaseModel):
    asset_prices: dict[str, list[float]] = Field(..., description="Asset to price series")
    lookback: int = Field(200, description="Trend lookback period")
    vol_lookback: int = Field(20, description="Volatility lookback")
    vol_target: float = Field(0.10, description="Target annualized volatility")


class MultiAssetTrendResponse(BaseModel):
    strategy: str = "multi_asset_trend"
    weights: dict[str, float]
    signals: dict[str, int]
    volatilities: dict[str, float]


@router.post("/multi-asset-trend", response_model=MultiAssetTrendResponse)
def multi_asset_trend(req: MultiAssetTrendRequest):
    signals = {}
    volatilities = {}
    raw_weights = {}

    for asset, prices in req.asset_prices.items():
        prices_arr = np.array(prices)
        if len(prices_arr) < req.lookback:
            continue

        sma = np.mean(prices_arr[-req.lookback:])
        current = prices_arr[-1]

        signals[asset] = 1 if current > sma else 0

        returns = np.diff(prices_arr[-req.vol_lookback - 1:]) / prices_arr[-req.vol_lookback - 1:-1]
        vol = float(np.std(returns) * np.sqrt(252))
        volatilities[asset] = vol

        if signals[asset] == 1 and vol > 0:
            raw_weights[asset] = req.vol_target / vol
        else:
            raw_weights[asset] = 0.0

    total_weight = sum(raw_weights.values())
    if total_weight > 0:
        weights = {a: w / total_weight for a, w in raw_weights.items()}
    else:
        weights = {a: 0.0 for a in raw_weights}

    return MultiAssetTrendResponse(
        weights=weights,
        signals=signals,
        volatilities=volatilities,
    )
