"""
Strategy 3.4: Low-Volatility Anomaly
Buying low-return-volatility stocks, shorting high-volatility.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class LowVolatilityRequest(BaseModel):
    returns: dict[str, list[float]] = Field(..., description="Asset to historical returns")
    lookback: int = Field(252, description="Lookback period for volatility calculation")
    long_pct: float = Field(0.1, description="Bottom percentile (low vol) to go long")
    short_pct: float = Field(0.1, description="Top percentile (high vol) to go short")


class LowVolatilityResponse(BaseModel):
    strategy: str = "low_volatility"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    volatilities: dict[str, float]


@router.post("/low-volatility", response_model=LowVolatilityResponse)
def low_volatility(req: LowVolatilityRequest):
    volatilities = {}
    for asset, rets in req.returns.items():
        if len(rets) >= req.lookback:
            volatilities[asset] = float(np.std(rets[-req.lookback:]))

    sorted_assets = sorted(volatilities.keys(), key=lambda x: volatilities[x])
    n = len(sorted_assets)
    n_long = max(1, int(n * req.long_pct))
    n_short = max(1, int(n * req.short_pct))

    long_assets = sorted_assets[:n_long]
    short_assets = sorted_assets[-n_short:]

    weights = {}
    for a in long_assets:
        weights[a] = 1.0 / n_long
    for a in short_assets:
        weights[a] = -1.0 / n_short

    return LowVolatilityResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        volatilities=volatilities,
    )
