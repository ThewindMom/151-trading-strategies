"""
Strategy 3.1: Price Momentum
Buy top decile, short bottom decile based on 12-month returns (skip last month).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class PriceMomentumRequest(BaseModel):
    prices: dict[str, list[float]] = Field(..., description="Asset name to 13-month price series")
    lookback: int = Field(12, description="Lookback period in months")
    skip_last: int = Field(1, description="Months to skip at end")
    long_pct: float = Field(0.1, description="Top percentile to go long")
    short_pct: float = Field(0.1, description="Bottom percentile to go short")


class PriceMomentumResponse(BaseModel):
    strategy: str = "price_momentum"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    momentum_scores: dict[str, float]


@router.post("/price-momentum", response_model=PriceMomentumResponse)
def price_momentum(req: PriceMomentumRequest):
    momentum_scores = {}
    for asset, prices in req.prices.items():
        if len(prices) >= req.lookback + req.skip_last + 1:
            start_idx = -(req.lookback + req.skip_last + 1)
            end_idx = -req.skip_last if req.skip_last > 0 else None
            p_start = prices[start_idx]
            p_end = prices[end_idx] if end_idx else prices[-1]
            if p_start > 0:
                momentum_scores[asset] = (p_end - p_start) / p_start

    sorted_assets = sorted(momentum_scores.keys(), key=lambda x: momentum_scores[x], reverse=True)
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

    return PriceMomentumResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        momentum_scores=momentum_scores,
    )
