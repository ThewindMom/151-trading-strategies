"""
Strategy 8.4: Momentum and Carry Combination
Combining momentum and carry signals for FX trading.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fx", tags=["fx"])


class CurrencyData(BaseModel):
    pair: str = Field(..., description="Currency pair symbol")
    spot_rate: float = Field(..., description="Current spot rate")
    base_rate: float = Field(..., description="Base currency interest rate")
    quote_rate: float = Field(..., description="Quote currency interest rate")
    returns_1m: float = Field(..., description="1-month return")
    returns_3m: float = Field(..., description="3-month return")
    returns_12m: float = Field(..., description="12-month return")


class MomentumCarryRequest(BaseModel):
    currencies: list[CurrencyData] = Field(..., description="List of currency pairs")
    momentum_weight: float = Field(0.5, description="Weight for momentum signal (0-1)")
    carry_weight: float = Field(0.5, description="Weight for carry signal (0-1)")
    momentum_lookback: str = Field("3m", description="Momentum lookback period (1m, 3m, 12m)")
    top_n: int = Field(3, description="Number of pairs to long/short")


class ComboPosition(BaseModel):
    pair: str
    position: int
    momentum_score: float
    carry_score: float
    combined_score: float
    momentum_return: float
    carry_spread: float


class MomentumCarryResponse(BaseModel):
    strategy: str = "momentum_carry_combo"
    positions: list[ComboPosition]
    long_pairs: list[str]
    short_pairs: list[str]
    avg_momentum_score: float
    avg_carry_score: float


@router.post("/momentum-carry-combo", response_model=MomentumCarryResponse)
def momentum_carry_combo(req: MomentumCarryRequest):
    lookback_map = {"1m": "returns_1m", "3m": "returns_3m", "12m": "returns_12m"}
    momentum_field = lookback_map.get(req.momentum_lookback, "returns_3m")

    scores = []
    for ccy in req.currencies:
        momentum_return = getattr(ccy, momentum_field)
        carry_spread = ccy.base_rate - ccy.quote_rate
        scores.append({
            "pair": ccy.pair,
            "momentum_return": momentum_return,
            "carry_spread": carry_spread,
        })

    if not scores:
        return MomentumCarryResponse(
            positions=[],
            long_pairs=[],
            short_pairs=[],
            avg_momentum_score=0.0,
            avg_carry_score=0.0,
        )

    momentum_values = np.array([s["momentum_return"] for s in scores])
    carry_values = np.array([s["carry_spread"] for s in scores])

    mom_mean, mom_std = np.mean(momentum_values), np.std(momentum_values)
    carry_mean, carry_std = np.mean(carry_values), np.std(carry_values)

    mom_std = mom_std if mom_std > 0 else 1
    carry_std = carry_std if carry_std > 0 else 1

    for i, s in enumerate(scores):
        mom_z = (s["momentum_return"] - mom_mean) / mom_std
        carry_z = (s["carry_spread"] - carry_mean) / carry_std
        combined = req.momentum_weight * mom_z + req.carry_weight * carry_z
        scores[i]["momentum_score"] = mom_z
        scores[i]["carry_score"] = carry_z
        scores[i]["combined_score"] = combined

    sorted_scores = sorted(scores, key=lambda x: x["combined_score"], reverse=True)

    positions = []
    long_pairs = []
    short_pairs = []

    for i, item in enumerate(sorted_scores):
        if i < req.top_n:
            positions.append(ComboPosition(
                pair=item["pair"],
                position=1,
                momentum_score=item["momentum_score"],
                carry_score=item["carry_score"],
                combined_score=item["combined_score"],
                momentum_return=item["momentum_return"],
                carry_spread=item["carry_spread"],
            ))
            long_pairs.append(item["pair"])
        elif i >= len(sorted_scores) - req.top_n:
            positions.append(ComboPosition(
                pair=item["pair"],
                position=-1,
                momentum_score=item["momentum_score"],
                carry_score=item["carry_score"],
                combined_score=item["combined_score"],
                momentum_return=item["momentum_return"],
                carry_spread=item["carry_spread"],
            ))
            short_pairs.append(item["pair"])

    avg_mom = float(np.mean([p.momentum_score for p in positions])) if positions else 0.0
    avg_carry = float(np.mean([p.carry_score for p in positions])) if positions else 0.0

    return MomentumCarryResponse(
        positions=positions,
        long_pairs=long_pairs,
        short_pairs=short_pairs,
        avg_momentum_score=avg_mom,
        avg_carry_score=avg_carry,
    )
