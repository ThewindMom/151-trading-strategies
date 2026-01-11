"""
Strategy 3.2: Earnings Momentum
Selection based on Standardized Unexpected Earnings (SUE).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class EarningsMomentumRequest(BaseModel):
    earnings: dict[str, list[float]] = Field(..., description="Asset to quarterly earnings history")
    long_pct: float = Field(0.1, description="Top percentile to go long")
    short_pct: float = Field(0.1, description="Bottom percentile to go short")


class EarningsMomentumResponse(BaseModel):
    strategy: str = "earnings_momentum"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    sue_scores: dict[str, float]


@router.post("/earnings-momentum", response_model=EarningsMomentumResponse)
def earnings_momentum(req: EarningsMomentumRequest):
    sue_scores = {}
    for asset, earnings in req.earnings.items():
        if len(earnings) >= 5:
            expected = np.mean(earnings[-5:-1])
            actual = earnings[-1]
            std = np.std(earnings[-5:-1])
            if std > 0:
                sue_scores[asset] = (actual - expected) / std

    sorted_assets = sorted(sue_scores.keys(), key=lambda x: sue_scores[x], reverse=True)
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

    return EarningsMomentumResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        sue_scores=sue_scores,
    )
