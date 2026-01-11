"""
Strategy 3.14: Support and Resistance
Trading based on pivot points, support, and resistance levels.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stocks", tags=["stocks"])


class SupportResistanceRequest(BaseModel):
    high: float = Field(..., description="Previous period high")
    low: float = Field(..., description="Previous period low")
    close: float = Field(..., description="Previous period close")
    current_price: float = Field(..., description="Current price")


class SupportResistanceResponse(BaseModel):
    strategy: str = "support_resistance"
    signal: int
    pivot: float
    resistance1: float
    resistance2: float
    resistance3: float
    support1: float
    support2: float
    support3: float
    nearest_level: str


@router.post("/support-resistance", response_model=SupportResistanceResponse)
def support_resistance(req: SupportResistanceRequest):
    pivot = (req.high + req.low + req.close) / 3

    r1 = 2 * pivot - req.low
    r2 = pivot + (req.high - req.low)
    r3 = req.high + 2 * (pivot - req.low)

    s1 = 2 * pivot - req.high
    s2 = pivot - (req.high - req.low)
    s3 = req.low - 2 * (req.high - pivot)

    levels = {
        "pivot": pivot,
        "r1": r1, "r2": r2, "r3": r3,
        "s1": s1, "s2": s2, "s3": s3,
    }

    nearest_level = min(levels.keys(), key=lambda k: abs(levels[k] - req.current_price))

    if req.current_price > pivot:
        signal = 1
    elif req.current_price < pivot:
        signal = -1
    else:
        signal = 0

    return SupportResistanceResponse(
        signal=signal,
        pivot=pivot,
        resistance1=r1,
        resistance2=r2,
        resistance3=r3,
        support1=s1,
        support2=s2,
        support3=s3,
        nearest_level=nearest_level,
    )
