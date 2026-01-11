"""
Strategy 6.2: Cash and Carry Arbitrage
Arbitrage between index spot and futures.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/index", tags=["index"])


class CashAndCarryRequest(BaseModel):
    spot_price: float = Field(..., description="Current index spot price")
    futures_price: float = Field(..., description="Current futures price")
    risk_free_rate: float = Field(0.05, description="Annual risk-free rate")
    dividend_yield: float = Field(0.02, description="Annual dividend yield")
    days_to_expiry: int = Field(..., description="Days until futures expiry")
    transaction_cost: float = Field(0.001, description="Transaction cost as fraction")


class CashAndCarryResponse(BaseModel):
    strategy: str = "cash_and_carry"
    signal: int = Field(..., description="1=buy spot/sell futures, -1=reverse, 0=no arb")
    theoretical_futures: float
    basis: float
    basis_pct: float
    arbitrage_profit: float
    is_profitable: bool


@router.post("/cash-and-carry", response_model=CashAndCarryResponse)
def cash_and_carry(req: CashAndCarryRequest):
    t = req.days_to_expiry / 365.0
    cost_of_carry = req.risk_free_rate - req.dividend_yield
    theoretical_futures = req.spot_price * np.exp(cost_of_carry * t)

    basis = req.futures_price - theoretical_futures
    basis_pct = basis / req.spot_price

    total_cost = 2 * req.transaction_cost
    arbitrage_profit = abs(basis_pct) - total_cost
    is_profitable = arbitrage_profit > 0

    signal = 0
    if is_profitable:
        if basis > 0:
            signal = 1
        elif basis < 0:
            signal = -1

    return CashAndCarryResponse(
        signal=signal,
        theoretical_futures=float(theoretical_futures),
        basis=float(basis),
        basis_pct=float(basis_pct),
        arbitrage_profit=float(arbitrage_profit) if is_profitable else 0.0,
        is_profitable=is_profitable,
    )
