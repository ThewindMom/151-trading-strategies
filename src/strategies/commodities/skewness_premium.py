"""
Strategy 9.5: Skewness Premium
Commodities with negative skewness tend to underperform.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np
from scipy import stats

router = APIRouter(prefix="/commodities", tags=["commodities"])


class CommodityReturns(BaseModel):
    symbol: str = Field(..., description="Commodity symbol")
    returns: list[float] = Field(..., description="Historical returns")
    current_price: float = Field(..., description="Current price")


class SkewnessPremiumRequest(BaseModel):
    commodities: list[CommodityReturns] = Field(..., description="Commodity return data")
    lookback_days: int = Field(252, description="Lookback period for skewness calculation")
    skewness_threshold: float = Field(0.5, description="Skewness threshold for signals")
    top_n: int = Field(3, description="Number of commodities to long/short")


class SkewnessPosition(BaseModel):
    symbol: str
    signal: int
    skewness: float
    kurtosis: float
    mean_return: float
    volatility: float
    skewness_rank: int


class SkewnessPremiumResponse(BaseModel):
    strategy: str = "skewness_premium"
    positions: list[SkewnessPosition]
    long_commodities: list[str]
    short_commodities: list[str]
    avg_long_skewness: float
    avg_short_skewness: float


@router.post("/skewness-premium", response_model=SkewnessPremiumResponse)
def skewness_premium(req: SkewnessPremiumRequest):
    skew_data = []

    for commodity in req.commodities:
        if len(commodity.returns) < 30:
            continue

        returns = np.array(commodity.returns[-req.lookback_days:])

        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))
        mean_return = float(np.mean(returns))
        volatility = float(np.std(returns))

        skew_data.append({
            "symbol": commodity.symbol,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "mean_return": mean_return,
            "volatility": volatility,
        })

    sorted_by_skew = sorted(skew_data, key=lambda x: x["skewness"], reverse=True)

    for i, item in enumerate(sorted_by_skew):
        item["skewness_rank"] = i + 1

    positions = []
    long_commodities = []
    short_commodities = []

    for i, item in enumerate(sorted_by_skew):
        if i < req.top_n and item["skewness"] > req.skewness_threshold:
            signal = 1
            long_commodities.append(item["symbol"])
        elif i >= len(sorted_by_skew) - req.top_n and item["skewness"] < -req.skewness_threshold:
            signal = -1
            short_commodities.append(item["symbol"])
        else:
            signal = 0

        if signal != 0:
            positions.append(SkewnessPosition(
                symbol=item["symbol"],
                signal=signal,
                skewness=item["skewness"],
                kurtosis=item["kurtosis"],
                mean_return=item["mean_return"],
                volatility=item["volatility"],
                skewness_rank=item["skewness_rank"],
            ))

    avg_long_skew = float(np.mean([p.skewness for p in positions if p.signal == 1])) if long_commodities else 0.0
    avg_short_skew = float(np.mean([p.skewness for p in positions if p.signal == -1])) if short_commodities else 0.0

    return SkewnessPremiumResponse(
        positions=positions,
        long_commodities=long_commodities,
        short_commodities=short_commodities,
        avg_long_skewness=avg_long_skew,
        avg_short_skewness=avg_short_skew,
    )
