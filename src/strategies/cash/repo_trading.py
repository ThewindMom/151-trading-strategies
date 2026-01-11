"""
Strategy 17.4: Repurchase Agreement (REPO) Trading
Short-term secured lending and borrowing using repo markets.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/cash", tags=["cash"])


class CollateralInfo(BaseModel):
    collateral_type: str = Field(..., description="Type of collateral (treasury, agency, corporate)")
    market_value: float = Field(..., description="Market value of collateral")
    haircut: float = Field(..., description="Haircut percentage (%)")
    credit_rating: str = Field(..., description="Credit rating of collateral")


class RepoOpportunity(BaseModel):
    counterparty: str = Field(..., description="Counterparty name/identifier")
    direction: str = Field(..., description="repo (lending) or reverse_repo (borrowing)")
    rate: float = Field(..., description="Repo rate (%)")
    term_days: int = Field(..., description="Term in days")
    principal: float = Field(..., description="Principal amount")
    collateral: CollateralInfo


class RepoTradingRequest(BaseModel):
    opportunities: list[RepoOpportunity] = Field(..., description="Available repo opportunities")
    available_cash: float = Field(..., description="Available cash for repo lending")
    securities_available: float = Field(..., description="Securities available for reverse repo")
    target_return: float = Field(0.05, description="Target daily return (%)")
    max_counterparty_exposure: float = Field(0.25, description="Max exposure per counterparty")
    min_credit_rating: str = Field("BBB", description="Minimum acceptable credit rating")


class RepoTradeRecommendation(BaseModel):
    counterparty: str
    direction: str
    rate: float
    term_days: int
    recommended_size: float
    expected_return: float
    risk_adjusted_return: float
    signal: str


class RepoTradingResponse(BaseModel):
    strategy: str = "repo_trading"
    signal: int = Field(..., description="1=enter trades, -1=unwind, 0=hold")
    recommendations: list[RepoTradeRecommendation]
    total_repo_exposure: float
    total_reverse_repo_exposure: float
    weighted_avg_rate: float
    net_interest_income: float
    spread_vs_target: float


@router.post("/repo-trading", response_model=RepoTradingResponse)
def repo_trading(req: RepoTradingRequest):
    rating_scores = {"AAA": 5, "AA": 4, "A": 3, "BBB": 2, "BB": 1, "B": 0}
    min_rating_score = rating_scores.get(req.min_credit_rating, 2)
    
    recommendations = []
    repo_exposure = 0.0
    reverse_repo_exposure = 0.0
    total_interest = 0.0
    rate_weighted_sum = 0.0
    total_weight = 0.0
    
    sorted_opps = sorted(req.opportunities, key=lambda x: x.rate, reverse=True)
    
    counterparty_exposure = {}
    
    for opp in sorted_opps:
        rating_score = rating_scores.get(opp.collateral.credit_rating, 0)
        if rating_score < min_rating_score:
            continue
        
        current_exposure = counterparty_exposure.get(opp.counterparty, 0)
        max_additional = req.available_cash * req.max_counterparty_exposure - current_exposure
        
        if opp.direction == "repo":
            collateral_value = opp.collateral.market_value * (1 - opp.collateral.haircut / 100)
            max_by_collateral = collateral_value
            max_by_cash = req.available_cash - repo_exposure
            recommended_size = min(opp.principal, max_additional, max_by_collateral, max_by_cash)
        else:
            max_by_securities = req.securities_available - reverse_repo_exposure
            recommended_size = min(opp.principal, max_additional, max_by_securities)
        
        recommended_size = max(0, recommended_size)
        
        if recommended_size > 0:
            expected_return = recommended_size * (opp.rate / 100) * (opp.term_days / 365)
            
            haircut_risk = opp.collateral.haircut / 100
            credit_adj = (5 - rating_score) * 0.02
            risk_adj_rate = opp.rate - credit_adj * 100 - haircut_risk * opp.rate
            risk_adjusted_return = recommended_size * (risk_adj_rate / 100) * (opp.term_days / 365)
            
            if opp.direction == "repo":
                repo_exposure += recommended_size
            else:
                reverse_repo_exposure += recommended_size
            
            total_interest += expected_return
            rate_weighted_sum += opp.rate * recommended_size
            total_weight += recommended_size
            counterparty_exposure[opp.counterparty] = current_exposure + recommended_size
            
            if risk_adj_rate > req.target_return * 365:
                signal = "enter"
            elif risk_adj_rate > 0:
                signal = "consider"
            else:
                signal = "avoid"
            
            recommendations.append(RepoTradeRecommendation(
                counterparty=opp.counterparty,
                direction=opp.direction,
                rate=opp.rate,
                term_days=opp.term_days,
                recommended_size=float(recommended_size),
                expected_return=float(expected_return),
                risk_adjusted_return=float(risk_adjusted_return),
                signal=signal,
            ))
    
    weighted_avg_rate = rate_weighted_sum / total_weight if total_weight > 0 else 0
    annualized_target = req.target_return * 365
    spread_vs_target = weighted_avg_rate - annualized_target
    
    if spread_vs_target > 0.1 and len([r for r in recommendations if r.signal == "enter"]) > 0:
        overall_signal = 1
    elif spread_vs_target < -0.1:
        overall_signal = -1
    else:
        overall_signal = 0
    
    return RepoTradingResponse(
        signal=overall_signal,
        recommendations=recommendations,
        total_repo_exposure=float(repo_exposure),
        total_reverse_repo_exposure=float(reverse_repo_exposure),
        weighted_avg_rate=float(weighted_avg_rate),
        net_interest_income=float(total_interest),
        spread_vs_target=float(spread_vs_target),
    )
