"""
Strategy 7.3: Volatility Carry
Short VXX, long VXZ to capture roll yield from contango.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/volatility", tags=["volatility"])


class VolatilityCarryRequest(BaseModel):
    vxx_price: float = Field(..., description="Current VXX price (short-term VIX ETN)")
    vxz_price: float = Field(..., description="Current VXZ price (mid-term VIX ETN)")
    vxx_prices: list[float] = Field(..., description="Historical VXX prices")
    vxz_prices: list[float] = Field(..., description="Historical VXZ prices")
    lookback: int = Field(20, description="Lookback for roll yield estimation")
    contango_threshold: float = Field(0.0, description="Minimum contango to enter trade")


class VolatilityCarryResponse(BaseModel):
    strategy: str = "volatility_carry"
    signal: int = Field(..., description="1=short VXX/long VXZ, 0=no position")
    vxx_roll_yield: float
    vxz_roll_yield: float
    spread_roll_yield: float
    ratio: float
    is_contango: bool


@router.post("/volatility-carry", response_model=VolatilityCarryResponse)
def volatility_carry(req: VolatilityCarryRequest):
    vxx_hist = np.array(req.vxx_prices[-req.lookback:])
    vxz_hist = np.array(req.vxz_prices[-req.lookback:])

    vxx_return = (vxx_hist[-1] / vxx_hist[0]) - 1
    vxz_return = (vxz_hist[-1] / vxz_hist[0]) - 1

    vxx_roll_yield = -vxx_return * (252 / req.lookback)
    vxz_roll_yield = -vxz_return * (252 / req.lookback)

    spread_roll_yield = vxx_roll_yield - vxz_roll_yield

    ratio = req.vxx_price / req.vxz_price
    is_contango = spread_roll_yield > req.contango_threshold

    signal = 1 if is_contango else 0

    return VolatilityCarryResponse(
        signal=signal,
        vxx_roll_yield=float(vxx_roll_yield),
        vxz_roll_yield=float(vxz_roll_yield),
        spread_roll_yield=float(spread_roll_yield),
        ratio=float(ratio),
        is_contango=is_contango,
    )
