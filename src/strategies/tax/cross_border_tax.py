"""
Strategy 13.2: Cross-Border Tax Arbitrage (Stock Loan Version)
Exploiting tax treaty differences through securities lending across jurisdictions.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tax", tags=["tax"])


class CrossBorderTaxRequest(BaseModel):
    dividend_yield: float = Field(..., description="Annual dividend yield of stock")
    domestic_withholding_rate: float = Field(..., description="Domestic withholding tax rate (0-1)")
    foreign_withholding_rate: float = Field(..., description="Foreign jurisdiction withholding rate (0-1)")
    stock_loan_fee: float = Field(..., description="Annual stock borrow/loan fee")
    financing_rate: float = Field(..., description="Financing/funding rate")
    treaty_reclaim_rate: float = Field(0.0, description="Tax treaty reclaim rate (0-1)")
    transaction_costs: float = Field(0.001, description="Round-trip transaction costs")
    holding_period_days: int = Field(30, description="Holding period around dividend")


class CrossBorderTaxResponse(BaseModel):
    strategy: str = "cross_border_tax"
    signal: int = Field(..., description="1=execute arb, -1=avoid, 0=neutral")
    tax_savings: float = Field(..., description="Tax savings from treaty/structure")
    net_arbitrage_profit: float = Field(..., description="Net profit after all costs")
    annualized_return: float = Field(..., description="Annualized return on capital")
    breakeven_dividend: float = Field(..., description="Minimum dividend yield for profitability")
    effective_tax_rate: float = Field(..., description="Effective tax rate achieved")


@router.post("/cross-border-tax", response_model=CrossBorderTaxResponse)
def cross_border_tax(req: CrossBorderTaxRequest):
    domestic_tax = req.dividend_yield * req.domestic_withholding_rate
    foreign_tax = req.dividend_yield * req.foreign_withholding_rate
    treaty_reclaim = req.dividend_yield * req.treaty_reclaim_rate

    tax_savings = domestic_tax - foreign_tax + treaty_reclaim

    holding_fraction = req.holding_period_days / 365
    loan_cost = req.stock_loan_fee * holding_fraction
    financing_cost = req.financing_rate * holding_fraction
    total_costs = loan_cost + financing_cost + req.transaction_costs

    net_arbitrage_profit = tax_savings - total_costs

    if holding_fraction > 0 and net_arbitrage_profit != 0:
        annualized_return = (net_arbitrage_profit / holding_fraction) * 100
    else:
        annualized_return = 0.0

    tax_diff = req.domestic_withholding_rate - req.foreign_withholding_rate + req.treaty_reclaim_rate
    if tax_diff > 0:
        breakeven_dividend = total_costs / tax_diff
    else:
        breakeven_dividend = float("inf")

    if req.dividend_yield > 0:
        effective_tax_rate = foreign_tax / req.dividend_yield - req.treaty_reclaim_rate
    else:
        effective_tax_rate = req.foreign_withholding_rate

    if net_arbitrage_profit > 0.001 and annualized_return > 5:
        signal = 1
    elif net_arbitrage_profit < -0.001:
        signal = -1
    else:
        signal = 0

    return CrossBorderTaxResponse(
        signal=signal,
        tax_savings=float(tax_savings),
        net_arbitrage_profit=float(net_arbitrage_profit),
        annualized_return=float(annualized_return),
        breakeven_dividend=float(breakeven_dividend),
        effective_tax_rate=float(effective_tax_rate),
    )
