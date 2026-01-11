"""
Strategy 16.2: Real Estate Diversification
VAR model allocation across property types (office, retail, industrial, residential).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/real-estate", tags=["real_estate"])


class RealEstateDiversityRequest(BaseModel):
    property_returns: dict[str, list[float]] = Field(..., description="Historical returns by property type")
    current_allocations: dict[str, float] = Field(..., description="Current portfolio weights")
    risk_tolerance: float = Field(0.15, description="Maximum acceptable volatility")
    min_allocation: float = Field(0.05, description="Minimum allocation per type")
    max_allocation: float = Field(0.50, description="Maximum allocation per type")


class PropertyAllocation(BaseModel):
    property_type: str
    current_weight: float
    target_weight: float
    expected_return: float
    volatility: float


class RealEstateDiversityResponse(BaseModel):
    strategy: str = "real_estate_diversity"
    allocations: list[PropertyAllocation]
    portfolio_return: float
    portfolio_volatility: float
    sharpe_ratio: float
    rebalance_needed: bool


@router.post("/real-estate-diversity", response_model=RealEstateDiversityResponse)
def real_estate_diversity(req: RealEstateDiversityRequest):
    property_types = list(req.property_returns.keys())
    n = len(property_types)

    returns_matrix = np.array([req.property_returns[p] for p in property_types])
    expected_returns = np.mean(returns_matrix, axis=1)
    volatilities = np.std(returns_matrix, axis=1)
    cov_matrix = np.cov(returns_matrix)

    inv_vol = 1 / (volatilities + 0.001)
    target_weights = inv_vol / np.sum(inv_vol)

    target_weights = np.clip(target_weights, req.min_allocation, req.max_allocation)
    target_weights = target_weights / np.sum(target_weights)

    allocations = []
    for i, prop_type in enumerate(property_types):
        allocations.append(PropertyAllocation(
            property_type=prop_type,
            current_weight=req.current_allocations.get(prop_type, 0),
            target_weight=float(target_weights[i]),
            expected_return=float(expected_returns[i]),
            volatility=float(volatilities[i]),
        ))

    portfolio_return = float(np.dot(target_weights, expected_returns))
    portfolio_volatility = float(np.sqrt(np.dot(target_weights, np.dot(cov_matrix, target_weights))))
    sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0

    current_weights = np.array([req.current_allocations.get(p, 0) for p in property_types])
    weight_diff = np.sum(np.abs(target_weights - current_weights))
    rebalance_needed = weight_diff > 0.1

    return RealEstateDiversityResponse(
        allocations=allocations,
        portfolio_return=portfolio_return,
        portfolio_volatility=portfolio_volatility,
        sharpe_ratio=float(sharpe_ratio),
        rebalance_needed=rebalance_needed,
    )
