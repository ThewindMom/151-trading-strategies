"""
Strategy 9.1: Roll Yields
Selection based on backwardation vs contango in commodity futures.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/commodities", tags=["commodities"])


class CommodityContract(BaseModel):
    symbol: str = Field(..., description="Commodity symbol")
    front_price: float = Field(..., description="Front month futures price")
    next_price: float = Field(..., description="Next month futures price")
    days_to_roll: int = Field(..., description="Days until roll")


class RollYieldsRequest(BaseModel):
    commodities: list[CommodityContract] = Field(..., description="List of commodity contracts")
    top_n: int = Field(5, description="Number of commodities to long/short")
    min_roll_yield: float = Field(0.01, description="Minimum annualized roll yield")


class RollPosition(BaseModel):
    symbol: str
    position: int
    roll_yield: float
    annualized_roll: float
    curve_state: str


class RollYieldsResponse(BaseModel):
    strategy: str = "roll_yields"
    positions: list[RollPosition]
    long_commodities: list[str]
    short_commodities: list[str]
    total_expected_roll: float


@router.post("/roll-yields", response_model=RollYieldsResponse)
def roll_yields(req: RollYieldsRequest):
    roll_data = []
    for c in req.commodities:
        roll_yield = (c.front_price - c.next_price) / c.next_price
        annualized_roll = roll_yield * (365 / c.days_to_roll) if c.days_to_roll > 0 else 0
        curve_state = "backwardation" if roll_yield > 0 else "contango"
        roll_data.append({
            "symbol": c.symbol,
            "roll_yield": roll_yield,
            "annualized_roll": annualized_roll,
            "curve_state": curve_state,
        })

    sorted_by_roll = sorted(roll_data, key=lambda x: x["annualized_roll"], reverse=True)

    positions = []
    long_commodities = []
    short_commodities = []

    for i, item in enumerate(sorted_by_roll):
        if i < req.top_n and item["annualized_roll"] > req.min_roll_yield:
            positions.append(RollPosition(
                symbol=item["symbol"],
                position=1,
                roll_yield=item["roll_yield"],
                annualized_roll=item["annualized_roll"],
                curve_state=item["curve_state"],
            ))
            long_commodities.append(item["symbol"])
        elif i >= len(sorted_by_roll) - req.top_n and item["annualized_roll"] < -req.min_roll_yield:
            positions.append(RollPosition(
                symbol=item["symbol"],
                position=-1,
                roll_yield=item["roll_yield"],
                annualized_roll=item["annualized_roll"],
                curve_state=item["curve_state"],
            ))
            short_commodities.append(item["symbol"])

    total_expected_roll = sum(
        p.annualized_roll * p.position for p in positions
    )

    return RollYieldsResponse(
        positions=positions,
        long_commodities=long_commodities,
        short_commodities=short_commodities,
        total_expected_roll=total_expected_roll,
    )
