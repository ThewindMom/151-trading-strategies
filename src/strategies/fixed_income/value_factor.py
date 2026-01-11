"""
Strategy 5.10: Value Factor
Buying bonds where observed spread is higher than theoretical (fair value) spread.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class ValueBond(BaseModel):
    cusip: str
    issuer: str
    observed_spread: float = Field(..., description="Current OAS in bps")
    theoretical_spread: float = Field(..., description="Model-implied fair spread in bps")
    yield_to_maturity: float
    duration: float
    credit_rating: str
    sector: str


class ValueFactorRequest(BaseModel):
    bond_universe: list[ValueBond]
    min_spread_diff: float = Field(20, description="Minimum spread difference to consider (bps)")
    max_duration: float = Field(15.0)
    portfolio_value: float = Field(1_000_000)
    top_n: int = Field(20)
    sector_limit: float = Field(0.25, description="Max weight per sector")


class ValueAllocation(BaseModel):
    cusip: str
    issuer: str
    sector: str
    spread_diff: float
    value_score: float
    weight: float
    face_value: float


class ValueFactorResponse(BaseModel):
    strategy: str = "value_factor"
    selected_count: int
    avg_spread_diff: float
    avg_duration: float
    avg_yield: float
    sector_weights: dict[str, float]
    allocations: list[ValueAllocation]
    expected_excess_return: float


@router.post("/value-factor", response_model=ValueFactorResponse)
def value_factor(req: ValueFactorRequest):
    candidates = []
    
    for bond in req.bond_universe:
        spread_diff = bond.observed_spread - bond.theoretical_spread
        if spread_diff >= req.min_spread_diff and bond.duration <= req.max_duration:
            value_score = spread_diff / bond.duration if bond.duration > 0 else spread_diff
            candidates.append((bond, spread_diff, value_score))
    
    candidates.sort(key=lambda x: -x[2])
    
    selected = []
    sector_notional: dict[str, float] = {}
    
    for bond, spread_diff, value_score in candidates:
        if len(selected) >= req.top_n:
            break
        
        current_sector_weight = sector_notional.get(bond.sector, 0) / req.portfolio_value
        if current_sector_weight >= req.sector_limit:
            continue
        
        selected.append((bond, spread_diff, value_score))
        sector_notional[bond.sector] = sector_notional.get(bond.sector, 0) + req.portfolio_value / req.top_n
    
    if not selected:
        return ValueFactorResponse(
            selected_count=0,
            avg_spread_diff=0,
            avg_duration=0,
            avg_yield=0,
            sector_weights={},
            allocations=[],
            expected_excess_return=0,
        )
    
    total_value_score = sum(vs for _, _, vs in selected)
    weights = [vs / total_value_score for _, _, vs in selected]
    
    allocations = []
    sector_weights: dict[str, float] = {}
    
    for (bond, spread_diff, value_score), weight in zip(selected, weights):
        allocations.append(ValueAllocation(
            cusip=bond.cusip,
            issuer=bond.issuer,
            sector=bond.sector,
            spread_diff=spread_diff,
            value_score=value_score,
            weight=weight,
            face_value=weight * req.portfolio_value,
        ))
        sector_weights[bond.sector] = sector_weights.get(bond.sector, 0) + weight
    
    avg_spread_diff = sum(sd * w for (_, sd, _), w in zip(selected, weights))
    avg_duration = sum(b.duration * w for (b, _, _), w in zip(selected, weights))
    avg_yield = sum(b.yield_to_maturity * w for (b, _, _), w in zip(selected, weights))
    
    expected_excess_return = avg_spread_diff * 0.5 / 100
    
    return ValueFactorResponse(
        selected_count=len(selected),
        avg_spread_diff=avg_spread_diff,
        avg_duration=avg_duration,
        avg_yield=avg_yield,
        sector_weights=sector_weights,
        allocations=allocations,
        expected_excess_return=expected_excess_return,
    )
