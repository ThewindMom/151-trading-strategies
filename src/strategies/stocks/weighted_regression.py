"""
Strategy 3.10: Weighted Regression
Cluster-neutral mean-reversion using regression weights.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class WeightedRegressionRequest(BaseModel):
    returns: dict[str, list[float]] = Field(..., description="Asset to return series")
    cluster_returns: list[float] = Field(..., description="Cluster/sector returns")
    lookback: int = Field(60)


class WeightedRegressionResponse(BaseModel):
    strategy: str = "weighted_regression"
    weights: dict[str, float]
    alphas: dict[str, float]
    betas: dict[str, float]


@router.post("/weighted-regression", response_model=WeightedRegressionResponse)
def weighted_regression(req: WeightedRegressionRequest):
    cluster = np.array(req.cluster_returns[-req.lookback:])
    X = np.column_stack([np.ones(len(cluster)), cluster])

    alphas = {}
    betas = {}

    for asset, rets in req.returns.items():
        y = np.array(rets[-req.lookback:])
        if len(y) == len(cluster):
            try:
                coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                alphas[asset] = float(coeffs[0])
                betas[asset] = float(coeffs[1])
            except np.linalg.LinAlgError:
                continue

    total_alpha = sum(abs(a) for a in alphas.values())
    weights = {}
    if total_alpha > 0:
        for asset, alpha in alphas.items():
            weights[asset] = alpha / total_alpha

    return WeightedRegressionResponse(
        weights=weights,
        alphas=alphas,
        betas=betas,
    )
