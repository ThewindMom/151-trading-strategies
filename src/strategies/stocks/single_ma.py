"""
Strategy 3.11: Single Moving Average
Price crossing a single SMA/EMA signal.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class SingleMARequest(BaseModel):
    prices: list[float] = Field(..., description="Price series")
    period: int = Field(20, description="MA period")
    ma_type: str = Field("sma", description="sma or ema")


class SingleMAResponse(BaseModel):
    strategy: str = "single_ma"
    signal: int = Field(..., description="1=long, -1=short, 0=neutral")
    current_price: float
    ma_value: float


@router.post("/single-ma", response_model=SingleMAResponse)
def single_ma(req: SingleMARequest):
    prices = np.array(req.prices)

    if req.ma_type.lower() == "ema":
        alpha = 2 / (req.period + 1)
        ema = prices[0]
        for p in prices[1:]:
            ema = alpha * p + (1 - alpha) * ema
        ma_value = float(ema)
    else:
        ma_value = float(np.mean(prices[-req.period:]))

    current_price = float(prices[-1])
    prev_price = float(prices[-2]) if len(prices) > 1 else current_price

    signal = 0
    if prev_price <= ma_value < current_price:
        signal = 1
    elif prev_price >= ma_value > current_price:
        signal = -1
    elif current_price > ma_value:
        signal = 1
    else:
        signal = -1

    return SingleMAResponse(
        signal=signal,
        current_price=current_price,
        ma_value=ma_value,
    )
