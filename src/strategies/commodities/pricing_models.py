"""
Strategy 9.6: Trading with Pricing Models
Trading based on cost-of-carry model deviations.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime

router = APIRouter(prefix="/commodities", tags=["commodities"])


class FuturesData(BaseModel):
    symbol: str = Field(..., description="Commodity symbol")
    spot_price: float = Field(..., description="Current spot price")
    futures_price: float = Field(..., description="Futures contract price")
    days_to_expiry: int = Field(..., description="Days until futures expiry")
    storage_cost_pct: float = Field(0.02, description="Annual storage cost as percentage")
    convenience_yield_pct: float = Field(0.0, description="Convenience yield as percentage")


class PricingModelsRequest(BaseModel):
    commodities: list[FuturesData] = Field(..., description="Futures data for commodities")
    risk_free_rate: float = Field(0.05, description="Risk-free interest rate")
    mispricing_threshold: float = Field(0.02, description="Minimum mispricing to trade")


class PricingPosition(BaseModel):
    symbol: str
    signal: int
    spot_price: float
    futures_price: float
    theoretical_price: float
    mispricing_pct: float
    basis: float
    annualized_basis: float
    trade_type: str


class PricingModelsResponse(BaseModel):
    strategy: str = "pricing_models"
    positions: list[PricingPosition]
    long_futures: list[str]
    short_futures: list[str]
    avg_mispricing: float
    arbitrage_opportunities: int


@router.post("/pricing-models", response_model=PricingModelsResponse)
def pricing_models(req: PricingModelsRequest):
    positions = []
    long_futures = []
    short_futures = []
    mispricings = []
    arb_count = 0

    for commodity in req.commodities:
        t = commodity.days_to_expiry / 365.0

        net_carry = req.risk_free_rate + commodity.storage_cost_pct - commodity.convenience_yield_pct
        theoretical_price = commodity.spot_price * np.exp(net_carry * t)

        mispricing = commodity.futures_price - theoretical_price
        mispricing_pct = mispricing / theoretical_price

        basis = commodity.futures_price - commodity.spot_price
        annualized_basis = (basis / commodity.spot_price) / t if t > 0 else 0

        if mispricing_pct < -req.mispricing_threshold:
            signal = 1
            trade_type = "long_futures_short_spot"
            long_futures.append(commodity.symbol)
            arb_count += 1
        elif mispricing_pct > req.mispricing_threshold:
            signal = -1
            trade_type = "short_futures_long_spot"
            short_futures.append(commodity.symbol)
            arb_count += 1
        else:
            signal = 0
            trade_type = "no_trade"

        mispricings.append(abs(mispricing_pct))

        positions.append(PricingPosition(
            symbol=commodity.symbol,
            signal=signal,
            spot_price=commodity.spot_price,
            futures_price=commodity.futures_price,
            theoretical_price=float(theoretical_price),
            mispricing_pct=float(mispricing_pct),
            basis=float(basis),
            annualized_basis=float(annualized_basis),
            trade_type=trade_type,
        ))

    avg_mispricing = float(np.mean(mispricings)) if mispricings else 0.0

    return PricingModelsResponse(
        positions=positions,
        long_futures=long_futures,
        short_futures=short_futures,
        avg_mispricing=avg_mispricing,
        arbitrage_opportunities=arb_count,
    )
