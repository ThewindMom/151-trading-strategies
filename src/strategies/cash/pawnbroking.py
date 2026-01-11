"""
Strategy 17.5: Pawnbroking
Secured lending against collateral with loan-to-value management.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/cash", tags=["cash"])


class CollateralItem(BaseModel):
    item_type: str = Field(..., description="Type of collateral (jewelry, electronics, vehicles, etc.)")
    appraised_value: float = Field(..., description="Appraised market value")
    liquidity_score: float = Field(..., description="Liquidity score 1-10 (10=most liquid)")
    depreciation_rate: float = Field(..., description="Monthly depreciation rate (%)")
    authentication_confidence: float = Field(..., description="Authentication confidence 0-1")


class LoanApplication(BaseModel):
    application_id: str = Field(..., description="Loan application identifier")
    requested_amount: float = Field(..., description="Requested loan amount")
    loan_term_days: int = Field(..., description="Requested loan term in days")
    collateral: CollateralItem
    borrower_history_score: float = Field(0.5, description="Borrower history score 0-1")


class PawnbrokingRequest(BaseModel):
    applications: list[LoanApplication] = Field(..., description="Loan applications")
    available_capital: float = Field(..., description="Available lending capital")
    target_yield: float = Field(24.0, description="Target annual yield (%)")
    max_ltv: float = Field(0.60, description="Maximum loan-to-value ratio")
    min_liquidity_score: float = Field(5.0, description="Minimum collateral liquidity score")
    default_rate_assumption: float = Field(0.05, description="Assumed default rate")


class LoanDecision(BaseModel):
    application_id: str
    decision: str
    approved_amount: float
    interest_rate: float
    ltv_ratio: float
    risk_score: float
    expected_profit: float
    collateral_coverage: float


class PawnbrokingResponse(BaseModel):
    strategy: str = "pawnbroking"
    signal: int = Field(..., description="1=deploy capital, -1=tighten lending, 0=maintain")
    decisions: list[LoanDecision]
    total_approved: float
    portfolio_weighted_ltv: float
    portfolio_yield: float
    expected_defaults: float
    net_expected_return: float
    capital_utilization: float


@router.post("/pawnbroking", response_model=PawnbrokingResponse)
def pawnbroking(req: PawnbrokingRequest):
    decisions = []
    total_approved = 0.0
    remaining_capital = req.available_capital
    
    weighted_ltv_sum = 0.0
    weighted_yield_sum = 0.0
    total_expected_profit = 0.0
    
    scored_apps = []
    for app in req.applications:
        coll = app.collateral
        
        liquidity_factor = coll.liquidity_score / 10
        depreciation_factor = 1 - (coll.depreciation_rate * app.loan_term_days / 30) / 100
        auth_factor = coll.authentication_confidence
        history_factor = app.borrower_history_score
        
        risk_score = 1 - (liquidity_factor * 0.3 + depreciation_factor * 0.2 +
                         auth_factor * 0.25 + history_factor * 0.25)
        
        scored_apps.append((app, risk_score))
    
    scored_apps.sort(key=lambda x: x[1])
    
    for app, risk_score in scored_apps:
        coll = app.collateral
        
        if coll.liquidity_score < req.min_liquidity_score:
            decisions.append(LoanDecision(
                application_id=app.application_id,
                decision="rejected",
                approved_amount=0,
                interest_rate=0,
                ltv_ratio=0,
                risk_score=float(risk_score),
                expected_profit=0,
                collateral_coverage=0,
            ))
            continue
        
        adjusted_ltv = req.max_ltv * (1 - risk_score * 0.3)
        max_loan = coll.appraised_value * adjusted_ltv
        
        approved_amount = min(app.requested_amount, max_loan, remaining_capital)
        
        if approved_amount < app.requested_amount * 0.5:
            decisions.append(LoanDecision(
                application_id=app.application_id,
                decision="rejected",
                approved_amount=0,
                interest_rate=0,
                ltv_ratio=0,
                risk_score=float(risk_score),
                expected_profit=0,
                collateral_coverage=0,
            ))
            continue
        
        base_rate = req.target_yield
        risk_premium = risk_score * 20
        interest_rate = base_rate + risk_premium
        
        actual_ltv = approved_amount / coll.appraised_value
        collateral_coverage = coll.appraised_value / approved_amount if approved_amount > 0 else 0
        
        term_years = app.loan_term_days / 365
        gross_interest = approved_amount * (interest_rate / 100) * term_years
        expected_default_loss = approved_amount * req.default_rate_assumption * (1 - collateral_coverage * 0.7)
        expected_profit = gross_interest - expected_default_loss
        
        decisions.append(LoanDecision(
            application_id=app.application_id,
            decision="approved",
            approved_amount=float(approved_amount),
            interest_rate=float(interest_rate),
            ltv_ratio=float(actual_ltv),
            risk_score=float(risk_score),
            expected_profit=float(expected_profit),
            collateral_coverage=float(collateral_coverage),
        ))
        
        total_approved += approved_amount
        remaining_capital -= approved_amount
        weighted_ltv_sum += actual_ltv * approved_amount
        weighted_yield_sum += interest_rate * approved_amount
        total_expected_profit += expected_profit
    
    portfolio_ltv = weighted_ltv_sum / total_approved if total_approved > 0 else 0
    portfolio_yield = weighted_yield_sum / total_approved if total_approved > 0 else 0
    expected_defaults = total_approved * req.default_rate_assumption
    capital_utilization = total_approved / req.available_capital if req.available_capital > 0 else 0
    
    if capital_utilization > 0.8 and portfolio_yield > req.target_yield:
        signal = 1
    elif portfolio_ltv > req.max_ltv or portfolio_yield < req.target_yield * 0.8:
        signal = -1
    else:
        signal = 0
    
    return PawnbrokingResponse(
        signal=signal,
        decisions=decisions,
        total_approved=float(total_approved),
        portfolio_weighted_ltv=float(portfolio_ltv),
        portfolio_yield=float(portfolio_yield),
        expected_defaults=float(expected_defaults),
        net_expected_return=float(total_expected_profit),
        capital_utilization=float(capital_utilization),
    )
