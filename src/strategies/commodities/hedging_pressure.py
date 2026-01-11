"""
Strategy 9.2: Hedging Pressure
Trading based on Commitments of Traders (COT) report.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/commodities", tags=["commodities"])


class CotData(BaseModel):
    symbol: str = Field(..., description="Commodity symbol")
    commercial_long: int = Field(..., description="Commercial long positions")
    commercial_short: int = Field(..., description="Commercial short positions")
    non_commercial_long: int = Field(..., description="Non-commercial long positions")
    non_commercial_short: int = Field(..., description="Non-commercial short positions")
    open_interest: int = Field(..., description="Total open interest")


class HedgingPressureRequest(BaseModel):
    cot_data: list[CotData] = Field(..., description="COT data for commodities")
    historical_hedging_pressure: dict[str, list[float]] = Field(
        default={}, description="Historical hedging pressure by symbol"
    )
    lookback: int = Field(52, description="Lookback weeks for percentile calculation")
    long_threshold: float = Field(0.8, description="Percentile threshold for long")
    short_threshold: float = Field(0.2, description="Percentile threshold for short")


class HedgingPosition(BaseModel):
    symbol: str
    signal: int
    hedging_pressure: float
    pressure_percentile: float
    commercial_net: int
    speculator_net: int


class HedgingPressureResponse(BaseModel):
    strategy: str = "hedging_pressure"
    positions: list[HedgingPosition]
    long_commodities: list[str]
    short_commodities: list[str]


@router.post("/hedging-pressure", response_model=HedgingPressureResponse)
def hedging_pressure(req: HedgingPressureRequest):
    positions = []
    long_commodities = []
    short_commodities = []

    for cot in req.cot_data:
        commercial_net = cot.commercial_long - cot.commercial_short
        speculator_net = cot.non_commercial_long - cot.non_commercial_short

        hp = commercial_net / cot.open_interest if cot.open_interest > 0 else 0

        historical = req.historical_hedging_pressure.get(cot.symbol, [])
        if historical:
            hist_array = np.array(historical[-req.lookback:])
            percentile = float(np.sum(hist_array < hp) / len(hist_array))
        else:
            percentile = 0.5

        if percentile > req.long_threshold:
            signal = 1
            long_commodities.append(cot.symbol)
        elif percentile < req.short_threshold:
            signal = -1
            short_commodities.append(cot.symbol)
        else:
            signal = 0

        positions.append(HedgingPosition(
            symbol=cot.symbol,
            signal=signal,
            hedging_pressure=hp,
            pressure_percentile=percentile,
            commercial_net=commercial_net,
            speculator_net=speculator_net,
        ))

    return HedgingPressureResponse(
        positions=positions,
        long_commodities=long_commodities,
        short_commodities=short_commodities,
    )
