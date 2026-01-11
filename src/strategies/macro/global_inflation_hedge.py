"""
Strategy 19.3: Global Macro Inflation Hedge
Cross-asset inflation hedging using global macro indicators.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/macro", tags=["macro"])


class AssetInflationData(BaseModel):
    asset_class: str = Field(..., description="Asset class (commodities, tips, real_estate, equities, gold)")
    expected_return: float = Field(..., description="Expected annual return (%)")
    inflation_beta: float = Field(..., description="Sensitivity to inflation")
    volatility: float = Field(..., description="Annual volatility (%)")
    current_weight: float = Field(..., description="Current portfolio weight (%)")


class RegionalInflationData(BaseModel):
    region: str = Field(..., description="Region name")
    current_inflation: float = Field(..., description="Current inflation rate (%)")
    expected_inflation: float = Field(..., description="Expected inflation rate (%)")
    inflation_surprise: float = Field(..., description="Inflation surprise (actual - expected) (%)")
    central_bank_credibility: float = Field(..., description="Central bank credibility score 0-1")


class GlobalInflationHedgeRequest(BaseModel):
    assets: list[AssetInflationData] = Field(..., description="Asset class data")
    regions: list[RegionalInflationData] = Field(..., description="Regional inflation data")
    portfolio_value: float = Field(..., description="Total portfolio value")
    target_inflation_beta: float = Field(1.0, description="Target portfolio inflation beta")
    max_single_asset_weight: float = Field(0.30, description="Maximum single asset weight")


class AssetAllocation(BaseModel):
    asset_class: str
    current_weight: float
    optimal_weight: float
    adjustment: float
    inflation_contribution: float


class GlobalInflationHedgeResponse(BaseModel):
    strategy: str = "global_inflation_hedge"
    signal: int = Field(..., description="1=increase hedge, -1=reduce, 0=maintain")
    allocations: list[AssetAllocation]
    portfolio_inflation_beta: float
    expected_real_return: float
    inflation_regime: str
    hedge_effectiveness: float
    regional_exposure_recommendation: dict


@router.post("/global-inflation-hedge", response_model=GlobalInflationHedgeResponse)
def global_inflation_hedge(req: GlobalInflationHedgeRequest):
    avg_expected_inflation = np.mean([r.expected_inflation for r in req.regions])
    avg_surprise = np.mean([r.inflation_surprise for r in req.regions])
    
    if avg_expected_inflation > 4 and avg_surprise > 0:
        inflation_regime = "high_rising"
        beta_target_adj = 1.2
    elif avg_expected_inflation > 4:
        inflation_regime = "high_stable"
        beta_target_adj = 1.0
    elif avg_expected_inflation < 2 and avg_surprise < 0:
        inflation_regime = "low_falling"
        beta_target_adj = 0.7
    else:
        inflation_regime = "moderate"
        beta_target_adj = 0.9
    
    adjusted_target_beta = req.target_inflation_beta * beta_target_adj
    
    betas = np.array([a.inflation_beta for a in req.assets])
    returns = np.array([a.expected_return for a in req.assets])
    vols = np.array([a.volatility for a in req.assets])
    
    beta_diff = np.abs(betas - adjusted_target_beta)
    sharpe_approx = returns / (vols + 0.001)
    
    scores = sharpe_approx - beta_diff * 0.5
    scores = np.exp(scores)
    optimal_weights = scores / np.sum(scores)
    optimal_weights = np.clip(optimal_weights, 0, req.max_single_asset_weight)
    optimal_weights = optimal_weights / np.sum(optimal_weights)
    
    portfolio_beta = np.dot(optimal_weights, betas)
    portfolio_return = np.dot(optimal_weights, returns)
    expected_real_return = portfolio_return - avg_expected_inflation
    
    hedge_effectiveness = 1 - abs(portfolio_beta - adjusted_target_beta) / adjusted_target_beta
    hedge_effectiveness = max(0, min(1, hedge_effectiveness)) * 100
    
    allocations = []
    for i, a in enumerate(req.assets):
        current_w = a.current_weight / 100
        optimal_w = optimal_weights[i]
        inflation_contrib = optimal_w * a.inflation_beta / portfolio_beta if portfolio_beta > 0 else 0
        
        allocations.append(AssetAllocation(
            asset_class=a.asset_class,
            current_weight=float(a.current_weight),
            optimal_weight=float(optimal_w * 100),
            adjustment=float((optimal_w - current_w) * 100),
            inflation_contribution=float(inflation_contrib * 100),
        ))
    
    regional_recommendations = {}
    for r in req.regions:
        if r.inflation_surprise > 1:
            regional_recommendations[r.region] = "overweight_hedges"
        elif r.inflation_surprise < -1:
            regional_recommendations[r.region] = "underweight_hedges"
        else:
            regional_recommendations[r.region] = "neutral"
    
    if portfolio_beta < adjusted_target_beta * 0.9 and inflation_regime in ["high_rising", "high_stable"]:
        signal = 1
    elif portfolio_beta > adjusted_target_beta * 1.2 and inflation_regime == "low_falling":
        signal = -1
    else:
        signal = 0
    
    return GlobalInflationHedgeResponse(
        signal=signal,
        allocations=allocations,
        portfolio_inflation_beta=float(portfolio_beta),
        expected_real_return=float(expected_real_return),
        inflation_regime=inflation_regime,
        hedge_effectiveness=float(hedge_effectiveness),
        regional_exposure_recommendation=regional_recommendations,
    )
