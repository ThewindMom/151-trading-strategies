"""
Strategy 5.3: Barbells
Concentrating holdings in very short and very long maturities to benefit from curve reshaping.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class BondInfo(BaseModel):
    cusip: str
    face_value: float
    coupon_rate: float
    yield_to_maturity: float
    maturity_years: float
    duration: float


class BarbellsRequest(BaseModel):
    short_term_bonds: list[BondInfo] = Field(..., description="Short-term bonds (< 3 years)")
    long_term_bonds: list[BondInfo] = Field(..., description="Long-term bonds (> 15 years)")
    target_duration: float = Field(..., description="Target portfolio duration")
    portfolio_value: float = Field(1_000_000)


class BarbellAllocation(BaseModel):
    cusip: str
    maturity_bucket: str
    weight: float
    face_value: float


class BarbellsResponse(BaseModel):
    strategy: str = "barbells"
    short_weight: float
    long_weight: float
    portfolio_duration: float
    portfolio_yield: float
    portfolio_convexity: float
    allocations: list[BarbellAllocation]
    curve_exposure: str


def calculate_convexity(duration: float, maturity: float) -> float:
    return duration * maturity * 0.5


@router.post("/barbells", response_model=BarbellsResponse)
def barbells_strategy(req: BarbellsRequest):
    if not req.short_term_bonds or not req.long_term_bonds:
        raise ValueError("Both short and long term bonds required")
    
    short_avg_duration = np.mean([b.duration for b in req.short_term_bonds])
    long_avg_duration = np.mean([b.duration for b in req.long_term_bonds])
    
    if long_avg_duration <= short_avg_duration:
        long_weight = 0.5
    else:
        long_weight = (req.target_duration - short_avg_duration) / (long_avg_duration - short_avg_duration)
        long_weight = max(0.0, min(1.0, long_weight))
    
    short_weight = 1.0 - long_weight
    
    allocations = []
    
    short_bond_weight = short_weight / len(req.short_term_bonds)
    for bond in req.short_term_bonds:
        allocations.append(BarbellAllocation(
            cusip=bond.cusip,
            maturity_bucket="short",
            weight=short_bond_weight,
            face_value=short_bond_weight * req.portfolio_value,
        ))
    
    long_bond_weight = long_weight / len(req.long_term_bonds)
    for bond in req.long_term_bonds:
        allocations.append(BarbellAllocation(
            cusip=bond.cusip,
            maturity_bucket="long",
            weight=long_bond_weight,
            face_value=long_bond_weight * req.portfolio_value,
        ))
    
    portfolio_duration = short_weight * short_avg_duration + long_weight * long_avg_duration
    
    short_avg_yield = np.mean([b.yield_to_maturity for b in req.short_term_bonds])
    long_avg_yield = np.mean([b.yield_to_maturity for b in req.long_term_bonds])
    portfolio_yield = short_weight * short_avg_yield + long_weight * long_avg_yield
    
    short_avg_maturity = np.mean([b.maturity_years for b in req.short_term_bonds])
    long_avg_maturity = np.mean([b.maturity_years for b in req.long_term_bonds])
    short_convexity = calculate_convexity(short_avg_duration, short_avg_maturity)
    long_convexity = calculate_convexity(long_avg_duration, long_avg_maturity)
    portfolio_convexity = short_weight * short_convexity + long_weight * long_convexity
    
    if long_weight > 0.6:
        curve_exposure = "steepener_benefit"
    elif short_weight > 0.6:
        curve_exposure = "flattener_benefit"
    else:
        curve_exposure = "neutral"
    
    return BarbellsResponse(
        short_weight=short_weight,
        long_weight=long_weight,
        portfolio_duration=portfolio_duration,
        portfolio_yield=portfolio_yield,
        portfolio_convexity=portfolio_convexity,
        allocations=allocations,
        curve_exposure=curve_exposure,
    )
