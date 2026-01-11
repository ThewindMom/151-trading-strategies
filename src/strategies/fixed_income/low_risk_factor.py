"""
Strategy 5.9: Low Risk Factor
Buying low-risk bonds to capture the low-risk anomaly (low-risk assets outperform on risk-adjusted basis).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class BondWithRisk(BaseModel):
    cusip: str
    issuer: str
    price: float
    yield_to_maturity: float
    maturity_years: float
    duration: float
    credit_rating: str = Field(..., description="Credit rating (AAA, AA, A, BBB, etc.)")
    spread_volatility: float = Field(..., description="Historical spread volatility in bps")
    beta: float = Field(..., description="Beta to broad bond market index")


class LowRiskFactorRequest(BaseModel):
    bond_universe: list[BondWithRisk]
    max_duration: float = Field(10.0, description="Maximum duration allowed")
    max_rating_notch: int = Field(4, description="Max rating notch (0=AAA, 4=BBB)")
    max_beta: float = Field(0.8, description="Maximum beta to market")
    portfolio_value: float = Field(1_000_000)
    top_n: int = Field(20, description="Number of bonds to select")


class LowRiskAllocation(BaseModel):
    cusip: str
    issuer: str
    risk_score: float
    weight: float
    face_value: float


class LowRiskFactorResponse(BaseModel):
    strategy: str = "low_risk_factor"
    selected_count: int
    avg_duration: float
    avg_yield: float
    avg_risk_score: float
    portfolio_beta: float
    allocations: list[LowRiskAllocation]
    expected_sharpe_improvement: float


RATING_MAP = {
    "AAA": 0, "AA+": 1, "AA": 1, "AA-": 2,
    "A+": 2, "A": 3, "A-": 3,
    "BBB+": 4, "BBB": 4, "BBB-": 5,
    "BB+": 6, "BB": 6, "BB-": 7,
    "B+": 8, "B": 8, "B-": 9,
    "CCC": 10, "CC": 11, "C": 12, "D": 13
}


def rating_to_notch(rating: str) -> int:
    return RATING_MAP.get(rating.upper(), 5)


def calculate_risk_score(bond: BondWithRisk) -> float:
    duration_score = bond.duration / 30.0
    rating_score = rating_to_notch(bond.credit_rating) / 13.0
    vol_score = min(bond.spread_volatility / 200.0, 1.0)
    beta_score = min(bond.beta / 2.0, 1.0)
    
    risk_score = 0.25 * duration_score + 0.30 * rating_score + 0.25 * vol_score + 0.20 * beta_score
    return risk_score


@router.post("/low-risk-factor", response_model=LowRiskFactorResponse)
def low_risk_factor(req: LowRiskFactorRequest):
    eligible_bonds = []
    
    for bond in req.bond_universe:
        rating_notch = rating_to_notch(bond.credit_rating)
        if (bond.duration <= req.max_duration and 
            rating_notch <= req.max_rating_notch and 
            bond.beta <= req.max_beta):
            risk_score = calculate_risk_score(bond)
            eligible_bonds.append((bond, risk_score))
    
    eligible_bonds.sort(key=lambda x: x[1])
    
    selected = eligible_bonds[:req.top_n]
    
    if not selected:
        return LowRiskFactorResponse(
            selected_count=0,
            avg_duration=0,
            avg_yield=0,
            avg_risk_score=0,
            portfolio_beta=0,
            allocations=[],
            expected_sharpe_improvement=0,
        )
    
    inv_risk_weights = [1.0 / (rs + 0.01) for _, rs in selected]
    total_weight = sum(inv_risk_weights)
    weights = [w / total_weight for w in inv_risk_weights]
    
    allocations = []
    for (bond, risk_score), weight in zip(selected, weights):
        allocations.append(LowRiskAllocation(
            cusip=bond.cusip,
            issuer=bond.issuer,
            risk_score=risk_score,
            weight=weight,
            face_value=weight * req.portfolio_value,
        ))
    
    avg_duration = sum(bond.duration * w for (bond, _), w in zip(selected, weights))
    avg_yield = sum(bond.yield_to_maturity * w for (bond, _), w in zip(selected, weights))
    avg_risk_score = sum(rs * w for (_, rs), w in zip(selected, weights))
    portfolio_beta = sum(bond.beta * w for (bond, _), w in zip(selected, weights))
    
    expected_sharpe_improvement = (1.0 - avg_risk_score) * 0.5
    
    return LowRiskFactorResponse(
        selected_count=len(selected),
        avg_duration=avg_duration,
        avg_yield=avg_yield,
        avg_risk_score=avg_risk_score,
        portfolio_beta=portfolio_beta,
        allocations=allocations,
        expected_sharpe_improvement=expected_sharpe_improvement,
    )
