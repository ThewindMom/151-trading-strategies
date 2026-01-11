"""
Strategy 16.4: Real Estate Momentum
Momentum-based property investment using price appreciation trends.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/real-estate", tags=["real_estate"])


class MarketData(BaseModel):
    market: str = Field(..., description="Market name/location")
    price_1m: float = Field(..., description="Price change last 1 month (%)")
    price_3m: float = Field(..., description="Price change last 3 months (%)")
    price_6m: float = Field(..., description="Price change last 6 months (%)")
    price_12m: float = Field(..., description="Price change last 12 months (%)")
    volume_change: float = Field(..., description="Transaction volume change YoY (%)")
    days_on_market: float = Field(..., description="Average days on market")
    inventory_months: float = Field(..., description="Months of inventory supply")


class RealEstateMomentumRequest(BaseModel):
    markets: list[MarketData] = Field(..., description="Market momentum data")
    lookback_weight_1m: float = Field(0.1, description="Weight for 1-month momentum")
    lookback_weight_3m: float = Field(0.2, description="Weight for 3-month momentum")
    lookback_weight_6m: float = Field(0.3, description="Weight for 6-month momentum")
    lookback_weight_12m: float = Field(0.4, description="Weight for 12-month momentum")
    top_n: int = Field(3, description="Number of top markets to select")


class MarketMomentum(BaseModel):
    market: str
    momentum_score: float
    rank: int
    signal: str
    strength: str


class RealEstateMomentumResponse(BaseModel):
    strategy: str = "real_estate_momentum"
    signal: int = Field(..., description="1=invest in top markets, -1=avoid, 0=neutral")
    markets: list[MarketMomentum]
    top_markets: list[str]
    bottom_markets: list[str]
    average_momentum: float
    momentum_dispersion: float


@router.post("/real-estate-momentum", response_model=RealEstateMomentumResponse)
def real_estate_momentum(req: RealEstateMomentumRequest):
    momentum_scores = []
    
    for m in req.markets:
        price_momentum = (
            m.price_1m * req.lookback_weight_1m +
            m.price_3m * req.lookback_weight_3m +
            m.price_6m * req.lookback_weight_6m +
            m.price_12m * req.lookback_weight_12m
        )
        
        volume_adj = 1 + (m.volume_change / 100) * 0.1
        dom_adj = 1 - (m.days_on_market - 30) / 100 * 0.05
        inventory_adj = 1 - (m.inventory_months - 6) / 12 * 0.1
        
        adjusted_momentum = price_momentum * volume_adj * dom_adj * inventory_adj
        momentum_scores.append(adjusted_momentum)
    
    scores_array = np.array(momentum_scores)
    ranks = np.argsort(-scores_array) + 1
    
    avg_momentum = float(np.mean(scores_array))
    momentum_dispersion = float(np.std(scores_array))
    
    markets = []
    for i, m in enumerate(req.markets):
        score = momentum_scores[i]
        rank = int(ranks[np.where(np.argsort(-scores_array) == i)[0][0]] + 1)
        
        if score > avg_momentum + momentum_dispersion:
            signal = "strong_buy"
            strength = "high"
        elif score > avg_momentum:
            signal = "buy"
            strength = "medium"
        elif score < avg_momentum - momentum_dispersion:
            signal = "avoid"
            strength = "high"
        elif score < avg_momentum:
            signal = "caution"
            strength = "medium"
        else:
            signal = "neutral"
            strength = "low"
        
        markets.append(MarketMomentum(
            market=m.market,
            momentum_score=float(score),
            rank=rank,
            signal=signal,
            strength=strength,
        ))
    
    sorted_markets = sorted(markets, key=lambda x: x.momentum_score, reverse=True)
    top_markets = [m.market for m in sorted_markets[:req.top_n]]
    bottom_markets = [m.market for m in sorted_markets[-req.top_n:]]
    
    if avg_momentum > 5 and len([m for m in markets if m.signal in ["strong_buy", "buy"]]) >= req.top_n:
        overall_signal = 1
    elif avg_momentum < -2:
        overall_signal = -1
    else:
        overall_signal = 0
    
    return RealEstateMomentumResponse(
        signal=overall_signal,
        markets=markets,
        top_markets=top_markets,
        bottom_markets=bottom_markets,
        average_momentum=avg_momentum,
        momentum_dispersion=momentum_dispersion,
    )
