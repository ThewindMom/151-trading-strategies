"""
Strategy 19.4: Global Fixed-Income Strategy
Cross-country fixed-income allocation based on yield curves and macro fundamentals.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/macro", tags=["macro"])


class CountryBondData(BaseModel):
    country: str = Field(..., description="Country name")
    yield_2y: float = Field(..., description="2-year government bond yield (%)")
    yield_10y: float = Field(..., description="10-year government bond yield (%)")
    yield_30y: float = Field(..., description="30-year government bond yield (%)")
    inflation_rate: float = Field(..., description="Current inflation rate (%)")
    policy_rate: float = Field(..., description="Central bank policy rate (%)")
    credit_rating_score: float = Field(..., description="Credit score 1-10 (10=AAA)")
    currency_code: str = Field(..., description="Currency code")
    fx_3m_change: float = Field(..., description="3-month FX change vs USD (%)")


class GlobalFixedIncomeRequest(BaseModel):
    countries: list[CountryBondData] = Field(..., description="Bond data by country")
    base_currency: str = Field("USD", description="Base currency for returns")
    hedge_fx: bool = Field(True, description="Whether to hedge FX exposure")
    duration_target: float = Field(5.0, description="Target portfolio duration")
    max_country_weight: float = Field(0.20, description="Maximum weight per country")
    min_credit_score: float = Field(5.0, description="Minimum credit score")


class CountryBondAllocation(BaseModel):
    country: str
    weight: float
    duration_bucket: str
    real_yield: float
    curve_slope: float
    signal: str
    fx_adjusted_yield: float


class GlobalFixedIncomeResponse(BaseModel):
    strategy: str = "global_fixed_income"
    signal: int = Field(..., description="1=extend duration/add, -1=reduce, 0=hold")
    allocations: list[CountryBondAllocation]
    portfolio_yield: float
    portfolio_duration: float
    portfolio_real_yield: float
    curve_steepness_avg: float
    recommended_duration_bucket: str


@router.post("/global-fixed-income", response_model=GlobalFixedIncomeResponse)
def global_fixed_income(req: GlobalFixedIncomeRequest):
    allocations = []
    eligible_countries = []
    
    for c in req.countries:
        if c.credit_rating_score < req.min_credit_score:
            continue
        
        curve_slope = c.yield_10y - c.yield_2y
        real_yield_10y = c.yield_10y - c.inflation_rate
        
        if req.hedge_fx:
            fx_adj = 0
        else:
            fx_adj = c.fx_3m_change * 4 * 0.3
        
        fx_adjusted_yield = c.yield_10y + fx_adj
        
        score = (
            real_yield_10y * 2 +
            curve_slope * 0.5 +
            c.credit_rating_score * 0.3 +
            fx_adj * 0.2
        )
        
        eligible_countries.append({
            "country": c.country,
            "score": score,
            "real_yield": real_yield_10y,
            "curve_slope": curve_slope,
            "fx_adjusted_yield": fx_adjusted_yield,
            "yield_2y": c.yield_2y,
            "yield_10y": c.yield_10y,
            "yield_30y": c.yield_30y,
        })
    
    if not eligible_countries:
        return GlobalFixedIncomeResponse(
            signal=0,
            allocations=[],
            portfolio_yield=0,
            portfolio_duration=0,
            portfolio_real_yield=0,
            curve_steepness_avg=0,
            recommended_duration_bucket="short",
        )
    
    scores = np.array([c["score"] for c in eligible_countries])
    exp_scores = np.exp(scores - np.max(scores))
    weights = exp_scores / np.sum(exp_scores)
    weights = np.clip(weights, 0, req.max_country_weight)
    weights = weights / np.sum(weights)
    
    avg_slope = np.mean([c["curve_slope"] for c in eligible_countries])
    if avg_slope > 1.5:
        duration_bucket = "long"
        duration_mult = 1.5
    elif avg_slope > 0.5:
        duration_bucket = "intermediate"
        duration_mult = 1.0
    elif avg_slope > -0.5:
        duration_bucket = "short"
        duration_mult = 0.7
    else:
        duration_bucket = "ultra_short"
        duration_mult = 0.4
    
    for i, c in enumerate(eligible_countries):
        if c["curve_slope"] > 1:
            country_duration = "long"
        elif c["curve_slope"] > 0:
            country_duration = "intermediate"
        else:
            country_duration = "short"
        
        if c["real_yield"] > 2 and c["curve_slope"] > 0.5:
            signal = "overweight"
        elif c["real_yield"] > 0:
            signal = "neutral"
        else:
            signal = "underweight"
        
        allocations.append(CountryBondAllocation(
            country=c["country"],
            weight=float(weights[i] * 100),
            duration_bucket=country_duration,
            real_yield=float(c["real_yield"]),
            curve_slope=float(c["curve_slope"]),
            signal=signal,
            fx_adjusted_yield=float(c["fx_adjusted_yield"]),
        ))
    
    portfolio_yield = np.dot(weights, [c["yield_10y"] for c in eligible_countries])
    portfolio_real_yield = np.dot(weights, [c["real_yield"] for c in eligible_countries])
    portfolio_duration = req.duration_target * duration_mult
    
    if portfolio_real_yield > 2 and avg_slope > 0.5:
        overall_signal = 1
    elif portfolio_real_yield < 0 or avg_slope < -0.5:
        overall_signal = -1
    else:
        overall_signal = 0
    
    return GlobalFixedIncomeResponse(
        signal=overall_signal,
        allocations=allocations,
        portfolio_yield=float(portfolio_yield),
        portfolio_duration=float(portfolio_duration),
        portfolio_real_yield=float(portfolio_real_yield),
        curve_steepness_avg=float(avg_slope),
        recommended_duration_bucket=duration_bucket,
    )
