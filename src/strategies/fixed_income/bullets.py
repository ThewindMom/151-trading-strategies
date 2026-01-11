"""
Strategy 5.2: Bullets
Portfolio where all bonds have the same maturity, concentrating interest rate risk at one point.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class BondPosition(BaseModel):
    cusip: str = Field(..., description="Bond identifier")
    face_value: float = Field(..., description="Face value of the bond")
    coupon_rate: float = Field(..., description="Annual coupon rate (e.g., 0.05 for 5%)")
    yield_to_maturity: float = Field(..., description="Current YTM")
    maturity_years: float = Field(..., description="Years to maturity")


class BulletsRequest(BaseModel):
    target_maturity: float = Field(..., description="Target maturity in years (e.g., 10)")
    available_bonds: list[BondPosition] = Field(..., description="Available bonds to choose from")
    portfolio_value: float = Field(1_000_000, description="Total portfolio value to allocate")
    maturity_tolerance: float = Field(0.5, description="Tolerance around target maturity in years")


class BulletAllocation(BaseModel):
    cusip: str
    weight: float
    face_value: float
    duration: float


class BulletsResponse(BaseModel):
    strategy: str = "bullets"
    target_maturity: float
    portfolio_duration: float
    portfolio_yield: float
    allocations: list[BulletAllocation]
    convexity: float


def calculate_macaulay_duration(coupon_rate: float, ytm: float, maturity: float, periods_per_year: int = 2) -> float:
    if ytm <= 0:
        return maturity
    n = int(maturity * periods_per_year)
    c = coupon_rate / periods_per_year
    y = ytm / periods_per_year
    
    pv_weighted = 0.0
    pv_total = 0.0
    
    for t in range(1, n + 1):
        pv = c / ((1 + y) ** t)
        pv_weighted += t * pv
        pv_total += pv
    
    pv_face = 1 / ((1 + y) ** n)
    pv_weighted += n * pv_face
    pv_total += pv_face
    
    return (pv_weighted / pv_total) / periods_per_year if pv_total > 0 else maturity


def calculate_convexity(coupon_rate: float, ytm: float, maturity: float, periods_per_year: int = 2) -> float:
    if ytm <= 0:
        return maturity ** 2
    n = int(maturity * periods_per_year)
    c = coupon_rate / periods_per_year
    y = ytm / periods_per_year
    
    conv_sum = 0.0
    pv_total = 0.0
    
    for t in range(1, n + 1):
        pv = c / ((1 + y) ** t)
        conv_sum += t * (t + 1) * pv
        pv_total += pv
    
    pv_face = 1 / ((1 + y) ** n)
    conv_sum += n * (n + 1) * pv_face
    pv_total += pv_face
    
    return (conv_sum / (pv_total * (1 + y) ** 2)) / (periods_per_year ** 2) if pv_total > 0 else 0


@router.post("/bullets", response_model=BulletsResponse)
def bullets_strategy(req: BulletsRequest):
    eligible_bonds = [
        b for b in req.available_bonds
        if abs(b.maturity_years - req.target_maturity) <= req.maturity_tolerance
    ]
    
    if not eligible_bonds:
        eligible_bonds = sorted(
            req.available_bonds, 
            key=lambda b: abs(b.maturity_years - req.target_maturity)
        )[:3]
    
    eligible_bonds = sorted(eligible_bonds, key=lambda b: -b.yield_to_maturity)
    
    allocations = []
    total_weight = 0.0
    weights = []
    
    for i, bond in enumerate(eligible_bonds):
        weight = 1.0 / (i + 1)
        weights.append(weight)
        total_weight += weight
    
    weights = [w / total_weight for w in weights]
    
    portfolio_duration = 0.0
    portfolio_yield = 0.0
    portfolio_convexity = 0.0
    
    for bond, weight in zip(eligible_bonds, weights):
        duration = calculate_macaulay_duration(bond.coupon_rate, bond.yield_to_maturity, bond.maturity_years)
        convexity = calculate_convexity(bond.coupon_rate, bond.yield_to_maturity, bond.maturity_years)
        
        allocations.append(BulletAllocation(
            cusip=bond.cusip,
            weight=weight,
            face_value=weight * req.portfolio_value,
            duration=duration,
        ))
        
        portfolio_duration += weight * duration
        portfolio_yield += weight * bond.yield_to_maturity
        portfolio_convexity += weight * convexity
    
    return BulletsResponse(
        target_maturity=req.target_maturity,
        portfolio_duration=portfolio_duration,
        portfolio_yield=portfolio_yield,
        allocations=allocations,
        convexity=portfolio_convexity,
    )
