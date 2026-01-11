"""
Strategy 9.3: Portfolio Diversification with Commodities
Optimal commodity allocation for portfolio diversification.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/commodities", tags=["commodities"])


class AssetData(BaseModel):
    symbol: str = Field(..., description="Asset symbol")
    asset_class: str = Field(..., description="Asset class (equity, bond, commodity)")
    expected_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., description="Annual volatility")


class PortfolioDiversificationRequest(BaseModel):
    assets: list[AssetData] = Field(..., description="List of assets")
    correlation_matrix: list[list[float]] = Field(..., description="Correlation matrix")
    target_commodity_weight: float = Field(0.1, description="Target commodity allocation")
    risk_free_rate: float = Field(0.02, description="Risk-free rate")
    min_weight: float = Field(0.0, description="Minimum weight per asset")
    max_weight: float = Field(0.3, description="Maximum weight per asset")


class AssetAllocation(BaseModel):
    symbol: str
    asset_class: str
    weight: float
    contribution_to_return: float
    contribution_to_risk: float


class PortfolioDiversificationResponse(BaseModel):
    strategy: str = "portfolio_diversification"
    allocations: list[AssetAllocation]
    portfolio_return: float
    portfolio_volatility: float
    sharpe_ratio: float
    commodity_weight: float
    diversification_ratio: float


@router.post("/portfolio-diversification", response_model=PortfolioDiversificationResponse)
def portfolio_diversification(req: PortfolioDiversificationRequest):
    n = len(req.assets)
    if n == 0:
        return PortfolioDiversificationResponse(
            allocations=[],
            portfolio_return=0.0,
            portfolio_volatility=0.0,
            sharpe_ratio=0.0,
            commodity_weight=0.0,
            diversification_ratio=1.0,
        )

    returns = np.array([a.expected_return for a in req.assets])
    vols = np.array([a.volatility for a in req.assets])
    corr = np.array(req.correlation_matrix)

    cov = np.outer(vols, vols) * corr

    commodity_indices = [i for i, a in enumerate(req.assets) if a.asset_class == "commodity"]
    non_commodity_indices = [i for i, a in enumerate(req.assets) if a.asset_class != "commodity"]

    weights = np.zeros(n)

    if commodity_indices:
        commodity_weight_each = req.target_commodity_weight / len(commodity_indices)
        for i in commodity_indices:
            weights[i] = min(max(commodity_weight_each, req.min_weight), req.max_weight)

    remaining_weight = 1.0 - np.sum(weights)
    if non_commodity_indices and remaining_weight > 0:
        sharpe_ratios = (returns[non_commodity_indices] - req.risk_free_rate) / vols[non_commodity_indices]
        sharpe_ratios = np.maximum(sharpe_ratios, 0.001)
        sharpe_weights = sharpe_ratios / np.sum(sharpe_ratios)

        for idx, i in enumerate(non_commodity_indices):
            w = sharpe_weights[idx] * remaining_weight
            weights[i] = min(max(w, req.min_weight), req.max_weight)

    weights = weights / np.sum(weights) if np.sum(weights) > 0 else weights

    port_return = float(np.dot(weights, returns))
    port_vol = float(np.sqrt(np.dot(weights, np.dot(cov, weights))))
    sharpe = (port_return - req.risk_free_rate) / port_vol if port_vol > 0 else 0

    weighted_avg_vol = float(np.dot(weights, vols))
    div_ratio = weighted_avg_vol / port_vol if port_vol > 0 else 1.0

    allocations = []
    for i, asset in enumerate(req.assets):
        contrib_return = weights[i] * returns[i]
        marginal_risk = np.dot(cov[i], weights) / port_vol if port_vol > 0 else 0
        contrib_risk = weights[i] * marginal_risk

        allocations.append(AssetAllocation(
            symbol=asset.symbol,
            asset_class=asset.asset_class,
            weight=float(weights[i]),
            contribution_to_return=float(contrib_return),
            contribution_to_risk=float(contrib_risk),
        ))

    actual_commodity_weight = sum(weights[i] for i in commodity_indices)

    return PortfolioDiversificationResponse(
        allocations=allocations,
        portfolio_return=port_return,
        portfolio_volatility=port_vol,
        sharpe_ratio=sharpe,
        commodity_weight=float(actual_commodity_weight),
        diversification_ratio=div_ratio,
    )
