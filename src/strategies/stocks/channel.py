"""
Strategy 3.15: Channel
Buying at the floor and selling at the ceiling of a price band.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class ChannelRequest(BaseModel):
    prices: list[float]
    lookback: int = Field(20, description="Lookback for channel calculation")
    channel_type: str = Field("donchian", description="donchian or bollinger")
    num_std: float = Field(2.0, description="Std devs for Bollinger bands")


class ChannelResponse(BaseModel):
    strategy: str = "channel"
    signal: int
    current_price: float
    upper_band: float
    lower_band: float
    middle: float
    position_in_channel: float


@router.post("/channel", response_model=ChannelResponse)
def channel(req: ChannelRequest):
    prices = np.array(req.prices[-req.lookback:])
    current_price = float(req.prices[-1])

    if req.channel_type.lower() == "bollinger":
        middle = float(np.mean(prices))
        std = float(np.std(prices))
        upper_band = middle + req.num_std * std
        lower_band = middle - req.num_std * std
    else:
        upper_band = float(np.max(prices))
        lower_band = float(np.min(prices))
        middle = (upper_band + lower_band) / 2

    channel_width = upper_band - lower_band
    if channel_width > 0:
        position_in_channel = (current_price - lower_band) / channel_width
    else:
        position_in_channel = 0.5

    if current_price <= lower_band:
        signal = 1
    elif current_price >= upper_band:
        signal = -1
    else:
        signal = 0

    return ChannelResponse(
        signal=signal,
        current_price=current_price,
        upper_band=upper_band,
        lower_band=lower_band,
        middle=middle,
        position_in_channel=position_in_channel,
    )
