"""
Strategy 16.6: Fix and Flip
Short-term renovation and resale ROI calculation.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/real-estate", tags=["real_estate"])


class FixAndFlipRequest(BaseModel):
    purchase_price: float = Field(..., description="Property purchase price")
    renovation_cost: float = Field(..., description="Estimated renovation cost")
    after_repair_value: float = Field(..., description="Expected ARV after renovation")
    holding_months: int = Field(..., description="Expected holding period in months")
    closing_costs_buy: float = Field(0.03, description="Buying closing costs as %")
    closing_costs_sell: float = Field(0.08, description="Selling closing costs as %")
    holding_costs_monthly: float = Field(..., description="Monthly holding costs (taxes, insurance, utilities)")
    financing_rate: float = Field(0.12, description="Annual financing rate")
    ltv_ratio: float = Field(0.70, description="Loan-to-value ratio")


class FixAndFlipResponse(BaseModel):
    strategy: str = "fix_and_flip"
    signal: int = Field(..., description="1=proceed, -1=pass, 0=marginal")
    total_investment: float = Field(..., description="Total cash required")
    expected_profit: float = Field(..., description="Net profit after all costs")
    roi_percent: float = Field(..., description="Return on investment (%)")
    annualized_roi: float = Field(..., description="Annualized ROI (%)")
    max_purchase_price: float = Field(..., description="Maximum purchase price for 20% ROI")
    seventy_percent_rule: float = Field(..., description="70% rule max offer")


@router.post("/fix-and-flip", response_model=FixAndFlipResponse)
def fix_and_flip(req: FixAndFlipRequest):
    buy_closing = req.purchase_price * req.closing_costs_buy
    sell_closing = req.after_repair_value * req.closing_costs_sell
    total_holding = req.holding_costs_monthly * req.holding_months

    loan_amount = req.purchase_price * req.ltv_ratio
    interest_cost = loan_amount * (req.financing_rate / 12) * req.holding_months

    total_costs = (req.purchase_price + req.renovation_cost + buy_closing +
                   sell_closing + total_holding + interest_cost)

    cash_down = req.purchase_price * (1 - req.ltv_ratio)
    total_investment = cash_down + req.renovation_cost + buy_closing + total_holding + interest_cost

    expected_profit = req.after_repair_value - total_costs
    roi_percent = (expected_profit / total_investment) * 100 if total_investment > 0 else 0
    annualized_roi = ((1 + roi_percent / 100) ** (12 / req.holding_months) - 1) * 100 if req.holding_months > 0 else 0

    seventy_percent_rule = req.after_repair_value * 0.70 - req.renovation_cost

    target_roi = 0.20
    target_profit = total_investment * target_roi
    max_purchase_price = (req.after_repair_value - req.renovation_cost - sell_closing -
                          total_holding - target_profit) / (1 + req.closing_costs_buy)

    if roi_percent > 25:
        signal = 1
    elif roi_percent < 10:
        signal = -1
    else:
        signal = 0

    return FixAndFlipResponse(
        signal=signal,
        total_investment=float(total_investment),
        expected_profit=float(expected_profit),
        roi_percent=float(roi_percent),
        annualized_roi=float(annualized_roi),
        max_purchase_price=float(max_purchase_price),
        seventy_percent_rule=float(seventy_percent_rule),
    )
