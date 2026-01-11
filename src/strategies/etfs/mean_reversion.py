"""
Strategy 4.4: Mean-Reversion (IBS)
Using Internal Bar Strength (IBS) to identify overextended ETFs.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/etfs", tags=["etfs"])


class MeanReversionIBSRequest(BaseModel):
    ohlc: dict[str, dict] = Field(
        ..., description="ETF to {open, high, low, close} for the day"
    )
    ibs_threshold_low: float = Field(0.2, description="IBS below this = oversold")
    ibs_threshold_high: float = Field(0.8, description="IBS above this = overbought")


class MeanReversionIBSResponse(BaseModel):
    strategy: str = "mean_reversion_ibs"
    signals: dict[str, int]
    ibs_values: dict[str, float]


@router.post("/mean-reversion-ibs", response_model=MeanReversionIBSResponse)
def mean_reversion_ibs(req: MeanReversionIBSRequest):
    signals = {}
    ibs_values = {}

    for etf, ohlc in req.ohlc.items():
        high = ohlc.get("high", 0)
        low = ohlc.get("low", 0)
        close = ohlc.get("close", 0)

        if high > low:
            ibs = (close - low) / (high - low)
        else:
            ibs = 0.5

        ibs_values[etf] = float(ibs)

        if ibs < req.ibs_threshold_low:
            signals[etf] = 1
        elif ibs > req.ibs_threshold_high:
            signals[etf] = -1
        else:
            signals[etf] = 0

    return MeanReversionIBSResponse(
        signals=signals,
        ibs_values=ibs_values,
    )
