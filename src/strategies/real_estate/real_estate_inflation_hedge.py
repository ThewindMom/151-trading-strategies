"""
Strategy 16.5: Inflation Hedging with Real Estate
Using real estate as an inflation hedge with lease escalation analysis.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/real-estate", tags=["real_estate"])


class PropertyInflationData(BaseModel):
    property_id: str = Field(..., description="Property identifier")
    property_type: str = Field(..., description="Type of property")
    current_noi: float = Field(..., description="Current Net Operating Income")
    lease_escalation_rate: float = Field(..., description="Annual lease escalation rate (%)")
    lease_term_remaining: float = Field(..., description="Years remaining on lease")
    operating_expense_ratio: float = Field(..., description="Operating expenses as % of revenue")
    property_value: float = Field(..., description="Current property value")
    cap_rate: float = Field(..., description="Current cap rate (%)")


class RealEstateInflationHedgeRequest(BaseModel):
    properties: list[PropertyInflationData] = Field(..., description="Property data")
    expected_inflation: float = Field(..., description="Expected annual inflation rate (%)")
    inflation_forecast_years: int = Field(5, description="Forecast horizon in years")
    target_real_return: float = Field(3.0, description="Target real return above inflation (%)")


class PropertyHedgeAnalysis(BaseModel):
    property_id: str
    property_type: str
    inflation_beta: float
    real_return: float
    hedge_effectiveness: float
    noi_growth_vs_inflation: float
    signal: str


class RealEstateInflationHedgeResponse(BaseModel):
    strategy: str = "real_estate_inflation_hedge"
    signal: int = Field(..., description="1=allocate to real estate, -1=reduce, 0=hold")
    properties: list[PropertyHedgeAnalysis]
    portfolio_inflation_beta: float
    expected_real_return: float
    best_hedge_properties: list[str]
    inflation_protection_score: float


@router.post("/real-estate-inflation-hedge", response_model=RealEstateInflationHedgeResponse)
def real_estate_inflation_hedge(req: RealEstateInflationHedgeRequest):
    analyses = []
    total_value = sum(p.property_value for p in req.properties)
    
    for p in req.properties:
        future_noi = p.current_noi * ((1 + p.lease_escalation_rate / 100) ** req.inflation_forecast_years)
        noi_growth_rate = (future_noi / p.current_noi - 1) * 100 / req.inflation_forecast_years
        
        inflation_beta = p.lease_escalation_rate / req.expected_inflation if req.expected_inflation > 0 else 1.0
        
        nominal_return = p.cap_rate + noi_growth_rate
        real_return = nominal_return - req.expected_inflation
        
        noi_vs_inflation = p.lease_escalation_rate - req.expected_inflation
        
        expense_drag = p.operating_expense_ratio * req.expected_inflation / 100
        adjusted_real_return = real_return - expense_drag
        
        hedge_effectiveness = min(100, max(0, 50 + inflation_beta * 25 + noi_vs_inflation * 10))
        
        if adjusted_real_return >= req.target_real_return and inflation_beta >= 0.9:
            signal = "strong_hedge"
        elif adjusted_real_return >= 0 and inflation_beta >= 0.7:
            signal = "moderate_hedge"
        elif adjusted_real_return < 0:
            signal = "poor_hedge"
        else:
            signal = "neutral"
        
        analyses.append(PropertyHedgeAnalysis(
            property_id=p.property_id,
            property_type=p.property_type,
            inflation_beta=float(inflation_beta),
            real_return=float(adjusted_real_return),
            hedge_effectiveness=float(hedge_effectiveness),
            noi_growth_vs_inflation=float(noi_vs_inflation),
            signal=signal,
        ))
    
    weights = np.array([p.property_value / total_value for p in req.properties])
    betas = np.array([a.inflation_beta for a in analyses])
    real_returns = np.array([a.real_return for a in analyses])
    hedge_scores = np.array([a.hedge_effectiveness for a in analyses])
    
    portfolio_beta = float(np.dot(weights, betas))
    expected_real_return = float(np.dot(weights, real_returns))
    inflation_protection_score = float(np.dot(weights, hedge_scores))
    
    sorted_analyses = sorted(analyses, key=lambda x: x.hedge_effectiveness, reverse=True)
    best_hedge_properties = [a.property_id for a in sorted_analyses if a.signal in ["strong_hedge", "moderate_hedge"]][:3]
    
    if expected_real_return >= req.target_real_return and portfolio_beta >= 0.9:
        overall_signal = 1
    elif expected_real_return < 0:
        overall_signal = -1
    else:
        overall_signal = 0
    
    return RealEstateInflationHedgeResponse(
        signal=overall_signal,
        properties=analyses,
        portfolio_inflation_beta=portfolio_beta,
        expected_real_return=expected_real_return,
        best_hedge_properties=best_hedge_properties,
        inflation_protection_score=inflation_protection_score,
    )
