"""
Strategy 19.2: Fundamental Macro
Ranking countries by business cycle and trade trends for macro allocation.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/macro", tags=["macro"])


class CountryData(BaseModel):
    country: str
    gdp_growth: float = Field(..., description="GDP growth rate (%)")
    inflation: float = Field(..., description="Inflation rate (%)")
    trade_balance: float = Field(..., description="Trade balance as % of GDP")
    interest_rate: float = Field(..., description="Policy interest rate (%)")
    current_account: float = Field(..., description="Current account as % of GDP")
    pmi: float = Field(..., description="Manufacturing PMI")


class FundamentalMacroRequest(BaseModel):
    countries: list[CountryData] = Field(..., description="Macro data by country")
    risk_budget: float = Field(1.0, description="Total risk budget (1 = full)")
    max_country_weight: float = Field(0.25, description="Maximum weight per country")


class CountryAllocation(BaseModel):
    country: str
    score: float
    weight: float
    position: str
    cycle_phase: str


class FundamentalMacroResponse(BaseModel):
    strategy: str = "fundamental_macro"
    allocations: list[CountryAllocation]
    long_countries: list[str]
    short_countries: list[str]
    top_indicator: str


@router.post("/fundamental-macro", response_model=FundamentalMacroResponse)
def fundamental_macro(req: FundamentalMacroRequest):
    scores = []
    cycle_phases = []

    for c in req.countries:
        growth_score = c.gdp_growth * 2
        inflation_score = -abs(c.inflation - 2) * 0.5
        trade_score = c.trade_balance * 0.3
        ca_score = c.current_account * 0.2
        pmi_score = (c.pmi - 50) * 0.1

        total_score = growth_score + inflation_score + trade_score + ca_score + pmi_score
        scores.append(total_score)

        if c.gdp_growth > 2 and c.pmi > 50:
            phase = "expansion"
        elif c.gdp_growth > 0 and c.pmi < 50:
            phase = "slowdown"
        elif c.gdp_growth < 0 and c.pmi < 50:
            phase = "contraction"
        else:
            phase = "recovery"
        cycle_phases.append(phase)

    scores = np.array(scores)
    score_std = np.std(scores) + 0.001
    z_scores = (scores - np.mean(scores)) / score_std

    long_mask = z_scores > 0.5
    short_mask = z_scores < -0.5

    weights = np.zeros(len(scores))
    if np.any(long_mask):
        long_weights = np.exp(z_scores[long_mask])
        long_weights = long_weights / np.sum(long_weights) * req.risk_budget / 2
        long_weights = np.clip(long_weights, 0, req.max_country_weight)
        weights[long_mask] = long_weights

    if np.any(short_mask):
        short_weights = np.exp(-z_scores[short_mask])
        short_weights = short_weights / np.sum(short_weights) * req.risk_budget / 2
        short_weights = np.clip(short_weights, 0, req.max_country_weight)
        weights[short_mask] = -short_weights

    allocations = []
    for i, c in enumerate(req.countries):
        allocations.append(CountryAllocation(
            country=c.country,
            score=float(scores[i]),
            weight=float(abs(weights[i])),
            position="long" if weights[i] > 0 else ("short" if weights[i] < 0 else "neutral"),
            cycle_phase=cycle_phases[i],
        ))

    long_countries = [req.countries[i].country for i in range(len(scores)) if weights[i] > 0]
    short_countries = [req.countries[i].country for i in range(len(scores)) if weights[i] < 0]

    return FundamentalMacroResponse(
        allocations=allocations,
        long_countries=long_countries,
        short_countries=short_countries,
        top_indicator="gdp_growth",
    )
