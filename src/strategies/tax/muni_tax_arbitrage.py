"""
Strategy 13.1: Municipal Bond Tax Arbitrage
Borrowing to buy tax-exempt municipal bonds for after-tax yield advantage.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tax", tags=["tax"])


class MuniTaxArbitrageRequest(BaseModel):
    muni_yield: float = Field(..., description="Tax-exempt municipal bond yield")
    taxable_yield: float = Field(..., description="Comparable taxable bond yield")
    borrowing_rate: float = Field(..., description="Cost of borrowing")
    marginal_tax_rate: float = Field(..., description="Investor marginal tax rate (0-1)")
    state_tax_rate: float = Field(0.0, description="State tax rate if applicable (0-1)")
    leverage_ratio: float = Field(1.0, description="Leverage ratio (1 = no leverage)")


class MuniTaxArbitrageResponse(BaseModel):
    strategy: str = "muni_tax_arbitrage"
    signal: int = Field(..., description="1=buy munis, -1=buy taxable, 0=neutral")
    tax_equivalent_yield: float = Field(..., description="Muni yield adjusted for tax benefit")
    after_tax_spread: float = Field(..., description="Spread after considering all taxes")
    leveraged_return: float = Field(..., description="Return with leverage applied")
    breakeven_tax_rate: float = Field(..., description="Tax rate where strategies equalize")


@router.post("/muni-tax-arbitrage", response_model=MuniTaxArbitrageResponse)
def muni_tax_arbitrage(req: MuniTaxArbitrageRequest):
    combined_tax_rate = req.marginal_tax_rate + req.state_tax_rate * (1 - req.marginal_tax_rate)
    tax_equivalent_yield = req.muni_yield / (1 - combined_tax_rate) if combined_tax_rate < 1 else req.muni_yield

    taxable_after_tax = req.taxable_yield * (1 - combined_tax_rate)
    after_tax_spread = req.muni_yield - taxable_after_tax

    borrowing_after_tax = req.borrowing_rate * (1 - req.marginal_tax_rate)
    net_carry = req.muni_yield - borrowing_after_tax
    leveraged_return = net_carry * req.leverage_ratio

    breakeven_tax_rate = 1 - (req.muni_yield / req.taxable_yield) if req.taxable_yield > 0 else 0

    if after_tax_spread > 0.25 and leveraged_return > 0:
        signal = 1
    elif after_tax_spread < -0.25:
        signal = -1
    else:
        signal = 0

    return MuniTaxArbitrageResponse(
        signal=signal,
        tax_equivalent_yield=float(tax_equivalent_yield),
        after_tax_spread=float(after_tax_spread),
        leveraged_return=float(leveraged_return),
        breakeven_tax_rate=float(breakeven_tax_rate),
    )
