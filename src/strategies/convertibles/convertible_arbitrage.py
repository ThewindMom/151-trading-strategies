"""
Strategy 12.1: Convertible Arbitrage
Long convertible bond, short underlying stock to capture mispricing.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/convertibles", tags=["convertibles"])


class ConvertibleArbitrageRequest(BaseModel):
    bond_price: float = Field(..., description="Current convertible bond price")
    stock_price: float = Field(..., description="Current stock price")
    conversion_ratio: float = Field(..., description="Shares per bond on conversion")
    bond_floor: float = Field(..., description="Straight bond value (no conversion)")
    implied_vol: float = Field(..., description="Implied volatility of conversion option")
    realized_vol: float = Field(..., description="Realized stock volatility")
    credit_spread: float = Field(..., description="Credit spread (bps)")
    risk_free_rate: float = Field(0.05, description="Risk-free rate")


class ConvertibleArbitrageResponse(BaseModel):
    strategy: str = "convertible_arbitrage"
    signal: int = Field(..., description="1=long CB/short stock, -1=reverse, 0=neutral")
    parity: float = Field(..., description="Conversion parity value")
    premium: float = Field(..., description="Premium over parity (%)")
    delta: float = Field(..., description="Hedge delta (shares to short per bond)")
    gamma_pnl: float = Field(..., description="Expected gamma P&L")
    vol_edge: float = Field(..., description="Implied - Realized vol spread")


@router.post("/convertible-arbitrage", response_model=ConvertibleArbitrageResponse)
def convertible_arbitrage(req: ConvertibleArbitrageRequest):
    parity = req.stock_price * req.conversion_ratio
    premium = ((req.bond_price - parity) / parity) * 100 if parity > 0 else 0

    moneyness = parity / req.bond_floor if req.bond_floor > 0 else 1
    delta = min(1.0, max(0.0, 0.5 + 0.5 * (moneyness - 1)))
    delta_shares = delta * req.conversion_ratio

    vol_edge = req.implied_vol - req.realized_vol

    gamma = 0.1 * (1 - abs(delta - 0.5) * 2)
    gamma_pnl = gamma * (req.realized_vol ** 2) * req.stock_price * 0.01

    if vol_edge < -5 and premium < 30:
        signal = 1
    elif vol_edge > 10 or premium > 50:
        signal = -1
    else:
        signal = 0

    return ConvertibleArbitrageResponse(
        signal=signal,
        parity=float(parity),
        premium=float(premium),
        delta=float(delta_shares),
        gamma_pnl=float(gamma_pnl),
        vol_edge=float(vol_edge),
    )
