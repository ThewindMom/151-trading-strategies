"""
Strategy 15.3: Distress Risk Puzzle
Buying safest companies, selling high default risk - exploiting the anomaly.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/distressed", tags=["distressed"])


class DistressRiskPuzzleRequest(BaseModel):
    default_probabilities: list[float] = Field(..., description="Default probabilities by company")
    expected_returns: list[float] = Field(..., description="Expected returns by company")
    market_caps: list[float] = Field(..., description="Market caps for weighting")
    tickers: list[str] = Field(..., description="Company tickers")
    quintile_size: int = Field(5, description="Number of quintiles for sorting")


class CompanyPosition(BaseModel):
    ticker: str
    default_probability: float
    position: str
    weight: float


class DistressRiskPuzzleResponse(BaseModel):
    strategy: str = "distress_risk_puzzle"
    long_portfolio: list[CompanyPosition]
    short_portfolio: list[CompanyPosition]
    expected_spread: float = Field(..., description="Expected long-short return spread")
    distress_premium: float = Field(..., description="Observed distress premium (negative = puzzle)")


@router.post("/distress-risk-puzzle", response_model=DistressRiskPuzzleResponse)
def distress_risk_puzzle(req: DistressRiskPuzzleRequest):
    n = len(req.default_probabilities)
    sorted_indices = np.argsort(req.default_probabilities)

    quintile_size = max(1, n // req.quintile_size)
    safest_indices = sorted_indices[:quintile_size]
    riskiest_indices = sorted_indices[-quintile_size:]

    total_safe_cap = sum(req.market_caps[i] for i in safest_indices)
    total_risky_cap = sum(req.market_caps[i] for i in riskiest_indices)

    long_portfolio = []
    for i in safest_indices:
        weight = req.market_caps[i] / total_safe_cap if total_safe_cap > 0 else 1 / len(safest_indices)
        long_portfolio.append(CompanyPosition(
            ticker=req.tickers[i],
            default_probability=req.default_probabilities[i],
            position="long",
            weight=float(weight),
        ))

    short_portfolio = []
    for i in riskiest_indices:
        weight = req.market_caps[i] / total_risky_cap if total_risky_cap > 0 else 1 / len(riskiest_indices)
        short_portfolio.append(CompanyPosition(
            ticker=req.tickers[i],
            default_probability=req.default_probabilities[i],
            position="short",
            weight=float(weight),
        ))

    safe_return = sum(req.expected_returns[i] * (req.market_caps[i] / total_safe_cap if total_safe_cap > 0 else 1/len(safest_indices)) for i in safest_indices)
    risky_return = sum(req.expected_returns[i] * (req.market_caps[i] / total_risky_cap if total_risky_cap > 0 else 1/len(riskiest_indices)) for i in riskiest_indices)

    expected_spread = safe_return - risky_return
    distress_premium = risky_return - safe_return

    return DistressRiskPuzzleResponse(
        long_portfolio=long_portfolio,
        short_portfolio=short_portfolio,
        expected_spread=float(expected_spread),
        distress_premium=float(distress_premium),
    )
