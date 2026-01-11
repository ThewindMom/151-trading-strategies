"""
Strategy 3.19: Market-Making
Capturing bid-ask spread via limit orders.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stocks", tags=["stocks"])


class MarketMakingRequest(BaseModel):
    mid_price: float = Field(..., description="Current mid price")
    volatility: float = Field(..., description="Recent volatility")
    inventory: float = Field(0.0, description="Current inventory position")
    max_inventory: float = Field(100.0, description="Maximum allowed inventory")
    base_spread: float = Field(0.001, description="Base spread as fraction of price")
    inventory_risk_factor: float = Field(0.5, description="How much inventory skews quotes")


class MarketMakingResponse(BaseModel):
    strategy: str = "market_making"
    bid_price: float
    ask_price: float
    spread: float
    inventory_skew: float


@router.post("/market-making", response_model=MarketMakingResponse)
def market_making(req: MarketMakingRequest):
    vol_adjusted_spread = req.base_spread * (1 + req.volatility * 10)

    inventory_ratio = req.inventory / req.max_inventory if req.max_inventory > 0 else 0
    inventory_skew = -inventory_ratio * req.inventory_risk_factor * req.mid_price

    half_spread = req.mid_price * vol_adjusted_spread / 2

    bid_price = req.mid_price - half_spread + inventory_skew
    ask_price = req.mid_price + half_spread + inventory_skew

    spread = ask_price - bid_price

    return MarketMakingResponse(
        bid_price=bid_price,
        ask_price=ask_price,
        spread=spread,
        inventory_skew=inventory_skew,
    )
