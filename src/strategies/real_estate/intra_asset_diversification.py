"""
Strategy 16.3: Intra-asset Class Diversification
Diversification across property types (residential, commercial, industrial, etc.).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/real-estate", tags=["real_estate"])


class PropertyTypeData(BaseModel):
    property_type: str = Field(..., description="Type of property (residential, commercial, industrial, retail, office)")
    expected_return: float = Field(..., description="Expected annual return (%)")
    volatility: float = Field(..., description="Annual volatility (%)")
    current_weight: float = Field(..., description="Current portfolio weight (%)")
    occupancy_rate: float = Field(..., description="Current occupancy rate (%)")
    cap_rate: float = Field(..., description="Capitalization rate (%)")


class IntraAssetDiversificationRequest(BaseModel):
    property_types: list[PropertyTypeData] = Field(..., description="Data for each property type")
    correlation_matrix: list[list[float]] = Field(..., description="Correlation matrix between property types")
    target_return: float = Field(8.0, description="Target portfolio return (%)")
    max_single_type_weight: float = Field(0.40, description="Maximum weight for single property type")


class PropertyAllocation(BaseModel):
    property_type: str
    current_weight: float
    optimal_weight: float
    adjustment: float
    risk_contribution: float


class IntraAssetDiversificationResponse(BaseModel):
    strategy: str = "intra_asset_diversification"
    signal: int = Field(..., description="1=rebalance, 0=hold")
    allocations: list[PropertyAllocation]
    portfolio_return: float
    portfolio_volatility: float
    diversification_ratio: float
    concentration_index: float


@router.post("/intra-asset-diversification", response_model=IntraAssetDiversificationResponse)
def intra_asset_diversification(req: IntraAssetDiversificationRequest):
    n = len(req.property_types)
    returns = np.array([p.expected_return for p in req.property_types])
    vols = np.array([p.volatility for p in req.property_types])
    current_weights = np.array([p.current_weight / 100 for p in req.property_types])
    corr_matrix = np.array(req.correlation_matrix)
    
    cov_matrix = np.outer(vols, vols) * corr_matrix / 10000
    
    inv_vol = 1 / vols
    optimal_weights = inv_vol / np.sum(inv_vol)
    optimal_weights = np.clip(optimal_weights, 0, req.max_single_type_weight)
    optimal_weights = optimal_weights / np.sum(optimal_weights)
    
    portfolio_return = np.dot(optimal_weights, returns)
    portfolio_variance = np.dot(optimal_weights, np.dot(cov_matrix, optimal_weights))
    portfolio_volatility = np.sqrt(portfolio_variance) * 100
    
    weighted_avg_vol = np.dot(optimal_weights, vols)
    diversification_ratio = weighted_avg_vol / (portfolio_volatility + 0.001)
    
    concentration_index = np.sum(optimal_weights ** 2)
    
    marginal_risk = np.dot(cov_matrix, optimal_weights)
    risk_contributions = optimal_weights * marginal_risk
    total_risk = np.sum(risk_contributions)
    risk_contrib_pct = (risk_contributions / (total_risk + 0.0001)) * 100
    
    allocations = []
    for i, p in enumerate(req.property_types):
        allocations.append(PropertyAllocation(
            property_type=p.property_type,
            current_weight=float(current_weights[i] * 100),
            optimal_weight=float(optimal_weights[i] * 100),
            adjustment=float((optimal_weights[i] - current_weights[i]) * 100),
            risk_contribution=float(risk_contrib_pct[i]),
        ))
    
    max_deviation = max(abs(a.adjustment) for a in allocations)
    signal = 1 if max_deviation > 5 else 0
    
    return IntraAssetDiversificationResponse(
        signal=signal,
        allocations=allocations,
        portfolio_return=float(portfolio_return),
        portfolio_volatility=float(portfolio_volatility),
        diversification_ratio=float(diversification_ratio),
        concentration_index=float(concentration_index),
    )
