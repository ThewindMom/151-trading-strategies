"""
Strategy 3.16: Event-Driven (M&A)
Merger arbitrage: Long target, short acquirer.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stocks", tags=["stocks"])


class EventDrivenRequest(BaseModel):
    target_price: float = Field(..., description="Current price of target company")
    acquirer_price: float = Field(..., description="Current price of acquirer")
    offer_price: float = Field(..., description="Offer price per target share")
    exchange_ratio: float = Field(0.0, description="Shares of acquirer per target share (if stock deal)")
    cash_component: float = Field(0.0, description="Cash per target share")
    deal_probability: float = Field(0.8, description="Estimated probability deal closes")


class EventDrivenResponse(BaseModel):
    strategy: str = "event_driven"
    signal: int
    spread: float
    spread_pct: float
    expected_return: float
    hedge_ratio: float


@router.post("/event-driven", response_model=EventDrivenResponse)
def event_driven(req: EventDrivenRequest):
    if req.exchange_ratio > 0:
        implied_value = req.exchange_ratio * req.acquirer_price + req.cash_component
    else:
        implied_value = req.offer_price

    spread = implied_value - req.target_price
    spread_pct = spread / req.target_price if req.target_price > 0 else 0

    expected_return = req.deal_probability * spread_pct

    hedge_ratio = req.exchange_ratio if req.exchange_ratio > 0 else 0

    if spread > 0 and expected_return > 0.01:
        signal = 1
    elif spread < 0:
        signal = -1
    else:
        signal = 0

    return EventDrivenResponse(
        signal=signal,
        spread=spread,
        spread_pct=spread_pct,
        expected_return=expected_return,
        hedge_ratio=hedge_ratio,
    )
