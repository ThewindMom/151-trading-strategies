"""
Strategy 8.2: FX Carry Trade
Long high-yield currency, short low-yield currency.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fx", tags=["fx"])


class CurrencyPair(BaseModel):
    pair: str = Field(..., description="Currency pair symbol (e.g., USDJPY)")
    spot_rate: float = Field(..., description="Current spot rate")
    base_rate: float = Field(..., description="Base currency interest rate")
    quote_rate: float = Field(..., description="Quote currency interest rate")


class FxCarryTradeRequest(BaseModel):
    currencies: list[CurrencyPair] = Field(..., description="List of currency pairs")
    top_n: int = Field(3, description="Number of currencies to long/short")
    min_carry: float = Field(0.01, description="Minimum carry spread to trade")


class CarryPosition(BaseModel):
    pair: str
    position: int
    carry_spread: float
    expected_return: float


class FxCarryTradeResponse(BaseModel):
    strategy: str = "fx_carry_trade"
    positions: list[CarryPosition]
    total_carry: float
    long_currencies: list[str]
    short_currencies: list[str]


@router.post("/fx-carry-trade", response_model=FxCarryTradeResponse)
def fx_carry_trade(req: FxCarryTradeRequest):
    carry_data = []
    for ccy in req.currencies:
        carry_spread = ccy.base_rate - ccy.quote_rate
        carry_data.append({
            "pair": ccy.pair,
            "carry_spread": carry_spread,
            "spot_rate": ccy.spot_rate,
        })

    sorted_by_carry = sorted(carry_data, key=lambda x: x["carry_spread"], reverse=True)

    positions = []
    long_currencies = []
    short_currencies = []

    for i, item in enumerate(sorted_by_carry):
        if i < req.top_n and item["carry_spread"] > req.min_carry:
            positions.append(CarryPosition(
                pair=item["pair"],
                position=1,
                carry_spread=item["carry_spread"],
                expected_return=item["carry_spread"],
            ))
            long_currencies.append(item["pair"])
        elif i >= len(sorted_by_carry) - req.top_n and item["carry_spread"] < -req.min_carry:
            positions.append(CarryPosition(
                pair=item["pair"],
                position=-1,
                carry_spread=item["carry_spread"],
                expected_return=-item["carry_spread"],
            ))
            short_currencies.append(item["pair"])

    total_carry = sum(p.expected_return for p in positions)

    return FxCarryTradeResponse(
        positions=positions,
        total_carry=total_carry,
        long_currencies=long_currencies,
        short_currencies=short_currencies,
    )
