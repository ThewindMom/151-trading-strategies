"""
Strategy 3.9: Mean-Reversion (Cluster)
Scaling pairs trading to a correlated industry/sector cluster.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class MeanReversionClusterRequest(BaseModel):
    prices: dict[str, list[float]] = Field(..., description="Asset to price series")
    lookback: int = Field(60, description="Lookback period")
    entry_zscore: float = Field(2.0)
    exit_zscore: float = Field(0.5)


class MeanReversionClusterResponse(BaseModel):
    strategy: str = "mean_reversion_cluster"
    signals: dict[str, int]
    zscores: dict[str, float]
    cluster_mean: list[float]


@router.post("/mean-reversion-cluster", response_model=MeanReversionClusterResponse)
def mean_reversion_cluster(req: MeanReversionClusterRequest):
    assets = list(req.prices.keys())
    min_len = min(len(req.prices[a]) for a in assets)
    lookback = min(req.lookback, min_len)

    prices_matrix = np.array([req.prices[a][-lookback:] for a in assets])
    cluster_mean = np.mean(prices_matrix, axis=0)

    signals = {}
    zscores = {}

    for i, asset in enumerate(assets):
        spread = prices_matrix[i] - cluster_mean
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)

        if spread_std > 0:
            z = (spread[-1] - spread_mean) / spread_std
        else:
            z = 0.0

        zscores[asset] = float(z)

        if z > req.entry_zscore:
            signals[asset] = -1
        elif z < -req.entry_zscore:
            signals[asset] = 1
        elif abs(z) < req.exit_zscore:
            signals[asset] = 0
        else:
            signals[asset] = 0

    return MeanReversionClusterResponse(
        signals=signals,
        zscores=zscores,
        cluster_mean=cluster_mean.tolist(),
    )
