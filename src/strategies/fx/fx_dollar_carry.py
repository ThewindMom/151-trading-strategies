"""
Strategy 8.3: Dollar Carry Trade
Long high-yield USD pairs, short low-yield USD pairs.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fx", tags=["fx"])


class UsdPair(BaseModel):
    pair: str = Field(..., description="USD pair symbol (e.g., USDMXN)")
    spot_rate: float = Field(..., description="Current spot rate")
    foreign_rate: float = Field(..., description="Foreign currency interest rate")
    usd_rate: float = Field(..., description="USD interest rate")


class DollarCarryRequest(BaseModel):
    usd_pairs: list[UsdPair] = Field(..., description="List of USD currency pairs")
    top_n: int = Field(3, description="Number of pairs to long/short")
    min_yield_diff: float = Field(0.005, description="Minimum yield differential to trade")


class DollarCarryPosition(BaseModel):
    pair: str
    position: int
    yield_differential: float
    expected_carry: float
    is_usd_base: bool


class DollarCarryResponse(BaseModel):
    strategy: str = "dollar_carry"
    positions: list[DollarCarryPosition]
    total_expected_carry: float
    long_pairs: list[str]
    short_pairs: list[str]
    net_usd_exposure: float


@router.post("/dollar-carry", response_model=DollarCarryResponse)
def dollar_carry(req: DollarCarryRequest):
    carry_data = []
    for pair in req.usd_pairs:
        is_usd_base = pair.pair.startswith("USD")
        if is_usd_base:
            yield_diff = pair.foreign_rate - pair.usd_rate
        else:
            yield_diff = pair.usd_rate - pair.foreign_rate

        carry_data.append({
            "pair": pair.pair,
            "yield_diff": yield_diff,
            "is_usd_base": is_usd_base,
            "spot_rate": pair.spot_rate,
        })

    sorted_by_yield = sorted(carry_data, key=lambda x: x["yield_diff"], reverse=True)

    positions = []
    long_pairs = []
    short_pairs = []
    net_usd = 0.0

    for i, item in enumerate(sorted_by_yield):
        if i < req.top_n and item["yield_diff"] > req.min_yield_diff:
            positions.append(DollarCarryPosition(
                pair=item["pair"],
                position=1,
                yield_differential=item["yield_diff"],
                expected_carry=item["yield_diff"],
                is_usd_base=item["is_usd_base"],
            ))
            long_pairs.append(item["pair"])
            net_usd += 1 if item["is_usd_base"] else -1
        elif i >= len(sorted_by_yield) - req.top_n and item["yield_diff"] < -req.min_yield_diff:
            positions.append(DollarCarryPosition(
                pair=item["pair"],
                position=-1,
                yield_differential=item["yield_diff"],
                expected_carry=-item["yield_diff"],
                is_usd_base=item["is_usd_base"],
            ))
            short_pairs.append(item["pair"])
            net_usd += -1 if item["is_usd_base"] else 1

    total_carry = sum(p.expected_carry for p in positions)

    return DollarCarryResponse(
        positions=positions,
        total_expected_carry=total_carry,
        long_pairs=long_pairs,
        short_pairs=short_pairs,
        net_usd_exposure=net_usd,
    )
