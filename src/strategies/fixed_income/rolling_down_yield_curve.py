"""
Strategy 5.12: Rolling Down the Yield Curve
Holding bonds in the steepest segments of the curve to maximize roll-down return.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class YieldCurvePoint(BaseModel):
    maturity: float
    yield_rate: float


class RollDownBond(BaseModel):
    cusip: str
    issuer: str
    maturity_years: float
    yield_to_maturity: float
    duration: float
    price: float


class RollingDownYieldCurveRequest(BaseModel):
    yield_curve: list[YieldCurvePoint]
    available_bonds: list[RollDownBond]
    holding_period: float = Field(1.0, description="Holding period in years")
    portfolio_value: float = Field(1_000_000)
    top_n: int = Field(10)


class CurveSegment(BaseModel):
    start_maturity: float
    end_maturity: float
    slope: float
    roll_down_potential: float


class RollDownAllocation(BaseModel):
    cusip: str
    issuer: str
    maturity: float
    curve_slope: float
    expected_roll_down: float
    weight: float
    face_value: float


class RollingDownYieldCurveResponse(BaseModel):
    strategy: str = "rolling_down_yield_curve"
    steepest_segments: list[CurveSegment]
    selected_count: int
    avg_roll_down: float
    avg_duration: float
    allocations: list[RollDownAllocation]
    expected_return: float


def interpolate_yield(curve: list[YieldCurvePoint], maturity: float) -> float:
    if maturity <= curve[0].maturity:
        return curve[0].yield_rate
    if maturity >= curve[-1].maturity:
        return curve[-1].yield_rate
    
    for i in range(len(curve) - 1):
        if curve[i].maturity <= maturity <= curve[i + 1].maturity:
            t = (maturity - curve[i].maturity) / (curve[i + 1].maturity - curve[i].maturity)
            return curve[i].yield_rate + t * (curve[i + 1].yield_rate - curve[i].yield_rate)
    
    return curve[-1].yield_rate


def calculate_curve_segments(curve: list[YieldCurvePoint]) -> list[CurveSegment]:
    segments = []
    sorted_curve = sorted(curve, key=lambda p: p.maturity)
    
    for i in range(len(sorted_curve) - 1):
        start = sorted_curve[i]
        end = sorted_curve[i + 1]
        
        slope = (end.yield_rate - start.yield_rate) / (end.maturity - start.maturity)
        avg_duration = (start.maturity + end.maturity) / 2 * 0.9
        roll_down_potential = slope * avg_duration
        
        segments.append(CurveSegment(
            start_maturity=start.maturity,
            end_maturity=end.maturity,
            slope=slope,
            roll_down_potential=roll_down_potential,
        ))
    
    return segments


@router.post("/rolling-down-yield-curve", response_model=RollingDownYieldCurveResponse)
def rolling_down_yield_curve(req: RollingDownYieldCurveRequest):
    sorted_curve = sorted(req.yield_curve, key=lambda p: p.maturity)
    segments = calculate_curve_segments(sorted_curve)
    steepest_segments = sorted(segments, key=lambda s: -s.slope)[:3]
    
    candidates = []
    
    for bond in req.available_bonds:
        if bond.maturity_years <= req.holding_period:
            continue
        
        current_yield = interpolate_yield(sorted_curve, bond.maturity_years)
        future_maturity = bond.maturity_years - req.holding_period
        future_yield = interpolate_yield(sorted_curve, future_maturity)
        
        yield_drop = current_yield - future_yield
        roll_down_return = bond.duration * yield_drop * req.holding_period
        
        local_slope = 0.0
        for seg in segments:
            if seg.start_maturity <= bond.maturity_years <= seg.end_maturity:
                local_slope = seg.slope
                break
        
        candidates.append((bond, roll_down_return, local_slope))
    
    candidates.sort(key=lambda x: -x[1])
    selected = candidates[:req.top_n]
    
    if not selected:
        return RollingDownYieldCurveResponse(
            steepest_segments=steepest_segments,
            selected_count=0,
            avg_roll_down=0,
            avg_duration=0,
            allocations=[],
            expected_return=0,
        )
    
    total_roll = sum(rd for _, rd, _ in selected)
    if total_roll > 0:
        weights = [rd / total_roll for _, rd, _ in selected]
    else:
        weights = [1.0 / len(selected)] * len(selected)
    
    allocations = []
    for (bond, roll_down, slope), weight in zip(selected, weights):
        allocations.append(RollDownAllocation(
            cusip=bond.cusip,
            issuer=bond.issuer,
            maturity=bond.maturity_years,
            curve_slope=slope,
            expected_roll_down=roll_down,
            weight=weight,
            face_value=weight * req.portfolio_value,
        ))
    
    avg_roll_down = sum(rd * w for (_, rd, _), w in zip(selected, weights))
    avg_duration = sum(b.duration * w for (b, _, _), w in zip(selected, weights))
    avg_yield = sum(b.yield_to_maturity * w for (b, _, _), w in zip(selected, weights))
    
    expected_return = avg_yield + avg_roll_down
    
    return RollingDownYieldCurveResponse(
        steepest_segments=steepest_segments,
        selected_count=len(selected),
        avg_roll_down=avg_roll_down,
        avg_duration=avg_duration,
        allocations=allocations,
        expected_return=expected_return,
    )
