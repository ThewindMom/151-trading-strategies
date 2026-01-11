"""
Strategy 9.4: Value Factor in Commodities
Trading based on deviation from historical price averages.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/commodities", tags=["commodities"])


class CommodityPriceData(BaseModel):
    symbol: str = Field(..., description="Commodity symbol")
    current_price: float = Field(..., description="Current price")
    historical_prices: list[float] = Field(..., description="Historical prices")


class CommodityValueRequest(BaseModel):
    commodities: list[CommodityPriceData] = Field(..., description="Commodity price data")
    lookback_years: int = Field(5, description="Years of history for average calculation")
    z_score_threshold: float = Field(1.5, description="Z-score threshold for signals")
    mean_reversion_horizon: int = Field(252, description="Expected mean reversion period in days")


class ValuePosition(BaseModel):
    symbol: str
    signal: int
    current_price: float
    historical_mean: float
    z_score: float
    deviation_pct: float
    expected_return: float


class CommodityValueResponse(BaseModel):
    strategy: str = "commodity_value"
    positions: list[ValuePosition]
    long_commodities: list[str]
    short_commodities: list[str]
    avg_absolute_z_score: float


@router.post("/commodity-value", response_model=CommodityValueResponse)
def commodity_value(req: CommodityValueRequest):
    positions = []
    long_commodities = []
    short_commodities = []

    z_scores = []

    for commodity in req.commodities:
        if not commodity.historical_prices:
            continue

        prices = np.array(commodity.historical_prices)
        days_per_year = 252
        lookback_days = req.lookback_years * days_per_year
        relevant_prices = prices[-lookback_days:] if len(prices) > lookback_days else prices

        hist_mean = float(np.mean(relevant_prices))
        hist_std = float(np.std(relevant_prices))

        if hist_std == 0:
            continue

        z_score = (commodity.current_price - hist_mean) / hist_std
        deviation_pct = (commodity.current_price - hist_mean) / hist_mean

        expected_return = -deviation_pct * (252 / req.mean_reversion_horizon)

        if z_score < -req.z_score_threshold:
            signal = 1
            long_commodities.append(commodity.symbol)
        elif z_score > req.z_score_threshold:
            signal = -1
            short_commodities.append(commodity.symbol)
        else:
            signal = 0

        z_scores.append(abs(z_score))

        positions.append(ValuePosition(
            symbol=commodity.symbol,
            signal=signal,
            current_price=commodity.current_price,
            historical_mean=hist_mean,
            z_score=z_score,
            deviation_pct=deviation_pct,
            expected_return=expected_return,
        ))

    avg_z = float(np.mean(z_scores)) if z_scores else 0.0

    return CommodityValueResponse(
        positions=positions,
        long_commodities=long_commodities,
        short_commodities=short_commodities,
        avg_absolute_z_score=avg_z,
    )
