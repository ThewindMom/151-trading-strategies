"""
Strategy 3.18: Statistical Arbitrage
Optimized dollar-neutral portfolio based on expected returns.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class StatArbRequest(BaseModel):
    expected_returns: dict[str, float] = Field(..., description="Asset to expected return")
    covariance_matrix: list[list[float]] = Field(..., description="Covariance matrix")
    asset_order: list[str] = Field(..., description="Order of assets in covariance matrix")
    risk_aversion: float = Field(1.0, description="Risk aversion parameter")


class StatArbResponse(BaseModel):
    strategy: str = "stat_arb"
    weights: dict[str, float]
    long_assets: list[str]
    short_assets: list[str]
    expected_portfolio_return: float
    portfolio_volatility: float


@router.post("/stat-arb", response_model=StatArbResponse)
def stat_arb(req: StatArbRequest):
    assets = req.asset_order
    n = len(assets)
    mu = np.array([req.expected_returns.get(a, 0) for a in assets])
    cov = np.array(req.covariance_matrix)

    try:
        cov_inv = np.linalg.inv(cov)
        raw_weights = cov_inv @ mu / req.risk_aversion
    except np.linalg.LinAlgError:
        raw_weights = mu

    long_sum = np.sum(raw_weights[raw_weights > 0])
    short_sum = np.abs(np.sum(raw_weights[raw_weights < 0]))

    if long_sum > 0 and short_sum > 0:
        scale = 2 / (long_sum + short_sum)
        normalized_weights = raw_weights * scale
    else:
        normalized_weights = raw_weights

    weights = {assets[i]: float(normalized_weights[i]) for i in range(n)}
    long_assets = [a for a, w in weights.items() if w > 0]
    short_assets = [a for a, w in weights.items() if w < 0]

    expected_return = float(normalized_weights @ mu)
    portfolio_var = float(normalized_weights @ cov @ normalized_weights)
    portfolio_vol = float(np.sqrt(max(0, portfolio_var)))

    return StatArbResponse(
        weights=weights,
        long_assets=long_assets,
        short_assets=short_assets,
        expected_portfolio_return=expected_return,
        portfolio_volatility=portfolio_vol,
    )
