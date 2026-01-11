"""
Strategy 4.1: Sector Momentum
Overweighting outperforming sectors via ETFs.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/etfs", tags=["etfs"])


class SectorMomentumRequest(BaseModel):
    sector_returns: dict[str, list[float]] = Field(..., description="Sector to return series")
    lookback: int = Field(12, description="Lookback period")
    top_n: int = Field(3, description="Number of top sectors to overweight")


class SectorMomentumResponse(BaseModel):
    strategy: str = "sector_momentum"
    weights: dict[str, float]
    momentum_scores: dict[str, float]
    top_sectors: list[str]


@router.post("/sector-momentum", response_model=SectorMomentumResponse)
def sector_momentum(req: SectorMomentumRequest):
    momentum_scores = {}
    for sector, rets in req.sector_returns.items():
        if len(rets) >= req.lookback:
            cum_ret = np.prod([1 + r for r in rets[-req.lookback:]]) - 1
            momentum_scores[sector] = float(cum_ret)

    sorted_sectors = sorted(momentum_scores.keys(), key=lambda x: momentum_scores[x], reverse=True)
    top_sectors = sorted_sectors[: req.top_n]

    weights = {}
    for sector in sorted_sectors:
        if sector in top_sectors:
            weights[sector] = 1.0 / req.top_n
        else:
            weights[sector] = 0.0

    return SectorMomentumResponse(
        weights=weights,
        momentum_scores=momentum_scores,
        top_sectors=top_sectors,
    )
