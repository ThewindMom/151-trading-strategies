"""
Strategy 5.11: Carry Factor
Buying bonds based on yield and roll-down returns (total carry).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class CarryBond(BaseModel):
    cusip: str
    issuer: str
    yield_to_maturity: float
    maturity_years: float
    duration: float
    coupon_rate: float
    price: float
    yield_1y_shorter: float = Field(..., description="Yield of bond 1 year shorter on curve")


class CarryFactorRequest(BaseModel):
    bond_universe: list[CarryBond]
    funding_rate: float = Field(..., description="Repo/funding rate for financing")
    holding_period: float = Field(1.0, description="Holding period in years")
    portfolio_value: float = Field(1_000_000)
    top_n: int = Field(20)
    min_maturity: float = Field(2.0)


class CarryAllocation(BaseModel):
    cusip: str
    issuer: str
    yield_carry: float
    roll_down: float
    total_carry: float
    weight: float
    face_value: float


class CarryFactorResponse(BaseModel):
    strategy: str = "carry_factor"
    selected_count: int
    avg_total_carry: float
    avg_yield_carry: float
    avg_roll_down: float
    avg_duration: float
    allocations: list[CarryAllocation]
    expected_return: float


def calculate_roll_down(bond: CarryBond) -> float:
    yield_drop = bond.yield_to_maturity - bond.yield_1y_shorter
    roll_down_return = bond.duration * yield_drop
    return roll_down_return


@router.post("/carry-factor", response_model=CarryFactorResponse)
def carry_factor(req: CarryFactorRequest):
    candidates = []
    
    for bond in req.bond_universe:
        if bond.maturity_years < req.min_maturity:
            continue
        
        yield_carry = bond.yield_to_maturity - req.funding_rate
        roll_down = calculate_roll_down(bond)
        total_carry = yield_carry + roll_down
        
        candidates.append((bond, yield_carry, roll_down, total_carry))
    
    candidates.sort(key=lambda x: -x[3])
    
    selected = candidates[:req.top_n]
    
    if not selected:
        return CarryFactorResponse(
            selected_count=0,
            avg_total_carry=0,
            avg_yield_carry=0,
            avg_roll_down=0,
            avg_duration=0,
            allocations=[],
            expected_return=0,
        )
    
    total_carry_sum = sum(tc for _, _, _, tc in selected)
    if total_carry_sum > 0:
        weights = [tc / total_carry_sum for _, _, _, tc in selected]
    else:
        weights = [1.0 / len(selected)] * len(selected)
    
    allocations = []
    for (bond, yield_carry, roll_down, total_carry), weight in zip(selected, weights):
        allocations.append(CarryAllocation(
            cusip=bond.cusip,
            issuer=bond.issuer,
            yield_carry=yield_carry,
            roll_down=roll_down,
            total_carry=total_carry,
            weight=weight,
            face_value=weight * req.portfolio_value,
        ))
    
    avg_total_carry = sum(tc * w for (_, _, _, tc), w in zip(selected, weights))
    avg_yield_carry = sum(yc * w for (_, yc, _, _), w in zip(selected, weights))
    avg_roll_down = sum(rd * w for (_, _, rd, _), w in zip(selected, weights))
    avg_duration = sum(b.duration * w for (b, _, _, _), w in zip(selected, weights))
    
    expected_return = avg_total_carry * req.holding_period
    
    return CarryFactorResponse(
        selected_count=len(selected),
        avg_total_carry=avg_total_carry,
        avg_yield_carry=avg_yield_carry,
        avg_roll_down=avg_roll_down,
        avg_duration=avg_duration,
        allocations=allocations,
        expected_return=expected_return,
    )
