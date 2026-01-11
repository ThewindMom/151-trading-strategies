"""
Strategy 8.5: FX Triangular Arbitrage
Exploiting price gaps in 3-way currency loops.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/fx", tags=["fx"])


class FxTriangularArbRequest(BaseModel):
    rate_ab: float = Field(..., description="Exchange rate A/B (e.g., EUR/USD)")
    rate_bc: float = Field(..., description="Exchange rate B/C (e.g., USD/JPY)")
    rate_ca: float = Field(..., description="Exchange rate C/A (e.g., JPY/EUR)")
    currency_a: str = Field("EUR", description="Currency A symbol")
    currency_b: str = Field("USD", description="Currency B symbol")
    currency_c: str = Field("JPY", description="Currency C symbol")
    initial_amount: float = Field(1000000, description="Initial amount in currency A")
    transaction_cost: float = Field(0.0001, description="Transaction cost per trade")


class FxTriangularArbResponse(BaseModel):
    strategy: str = "fx_triangular_arb"
    signal: int = Field(..., description="1=clockwise arb, -1=counter-clockwise, 0=no arb")
    clockwise_result: float
    counter_clockwise_result: float
    arbitrage_profit: float
    profit_pct: float
    is_profitable: bool
    direction: str


@router.post("/fx-triangular-arb", response_model=FxTriangularArbResponse)
def fx_triangular_arb(req: FxTriangularArbRequest):
    cost_mult = 1 - req.transaction_cost

    cw_step1 = req.initial_amount * req.rate_ab * cost_mult
    cw_step2 = cw_step1 * req.rate_bc * cost_mult
    cw_step3 = cw_step2 * req.rate_ca * cost_mult
    clockwise_result = cw_step3

    ccw_step1 = req.initial_amount / req.rate_ca * cost_mult
    ccw_step2 = ccw_step1 / req.rate_bc * cost_mult
    ccw_step3 = ccw_step2 / req.rate_ab * cost_mult
    counter_clockwise_result = ccw_step3

    cw_profit = clockwise_result - req.initial_amount
    ccw_profit = counter_clockwise_result - req.initial_amount

    if cw_profit > ccw_profit and cw_profit > 0:
        signal = 1
        arbitrage_profit = cw_profit
        direction = "clockwise"
    elif ccw_profit > cw_profit and ccw_profit > 0:
        signal = -1
        arbitrage_profit = ccw_profit
        direction = "counter_clockwise"
    else:
        signal = 0
        arbitrage_profit = 0.0
        direction = "none"

    profit_pct = arbitrage_profit / req.initial_amount * 100
    is_profitable = arbitrage_profit > 0

    return FxTriangularArbResponse(
        signal=signal,
        clockwise_result=clockwise_result,
        counter_clockwise_result=counter_clockwise_result,
        arbitrage_profit=arbitrage_profit,
        profit_pct=profit_pct,
        is_profitable=is_profitable,
        direction=direction,
    )
