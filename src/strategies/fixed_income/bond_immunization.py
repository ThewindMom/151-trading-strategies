"""
Strategy 5.5: Bond Immunization
Matching portfolio duration to a future cash obligation to immunize against interest rate changes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class ImmunizationBond(BaseModel):
    cusip: str
    face_value: float
    coupon_rate: float
    yield_to_maturity: float
    maturity_years: float
    duration: float
    convexity: float


class Liability(BaseModel):
    amount: float = Field(..., description="Future liability amount")
    years_to_payment: float = Field(..., description="Years until liability is due")


class BondImmunizationRequest(BaseModel):
    liability: Liability
    available_bonds: list[ImmunizationBond]
    current_rates: float = Field(..., description="Current market interest rate")
    rebalancing_frequency: str = Field("quarterly", description="How often to rebalance")


class ImmunizationAllocation(BaseModel):
    cusip: str
    weight: float
    face_value: float
    contribution_to_duration: float


class BondImmunizationResponse(BaseModel):
    strategy: str = "bond_immunization"
    liability_pv: float
    required_investment: float
    portfolio_duration: float
    target_duration: float
    duration_gap: float
    portfolio_convexity: float
    allocations: list[ImmunizationAllocation]
    immunization_quality: str
    rebalancing_trigger: float


def present_value(fv: float, rate: float, years: float) -> float:
    return fv / ((1 + rate) ** years)


@router.post("/bond-immunization", response_model=BondImmunizationResponse)
def bond_immunization(req: BondImmunizationRequest):
    target_duration = req.liability.years_to_payment
    liability_pv = present_value(req.liability.amount, req.current_rates, target_duration)
    
    bonds_with_gap = [(b, abs(b.duration - target_duration)) for b in req.available_bonds]
    bonds_with_gap.sort(key=lambda x: x[1])
    
    if len(bonds_with_gap) >= 2:
        shorter = [b for b in req.available_bonds if b.duration <= target_duration]
        longer = [b for b in req.available_bonds if b.duration > target_duration]
        
        if shorter and longer:
            short_bond = max(shorter, key=lambda b: b.duration)
            long_bond = min(longer, key=lambda b: b.duration)
            
            if long_bond.duration != short_bond.duration:
                long_weight = (target_duration - short_bond.duration) / (long_bond.duration - short_bond.duration)
                long_weight = max(0.0, min(1.0, long_weight))
            else:
                long_weight = 0.5
            short_weight = 1.0 - long_weight
            
            selected_bonds = [(short_bond, short_weight), (long_bond, long_weight)]
        else:
            best_bond = bonds_with_gap[0][0]
            selected_bonds = [(best_bond, 1.0)]
    else:
        best_bond = bonds_with_gap[0][0] if bonds_with_gap else req.available_bonds[0]
        selected_bonds = [(best_bond, 1.0)]
    
    allocations = []
    portfolio_duration = 0.0
    portfolio_convexity = 0.0
    
    for bond, weight in selected_bonds:
        face_value = weight * liability_pv
        contribution = weight * bond.duration
        
        allocations.append(ImmunizationAllocation(
            cusip=bond.cusip,
            weight=weight,
            face_value=face_value,
            contribution_to_duration=contribution,
        ))
        
        portfolio_duration += contribution
        portfolio_convexity += weight * bond.convexity
    
    duration_gap = abs(portfolio_duration - target_duration)
    
    if duration_gap < 0.1:
        immunization_quality = "excellent"
    elif duration_gap < 0.25:
        immunization_quality = "good"
    elif duration_gap < 0.5:
        immunization_quality = "acceptable"
    else:
        immunization_quality = "poor"
    
    rebalancing_trigger = 0.1 * target_duration
    
    return BondImmunizationResponse(
        liability_pv=liability_pv,
        required_investment=liability_pv,
        portfolio_duration=portfolio_duration,
        target_duration=target_duration,
        duration_gap=duration_gap,
        portfolio_convexity=portfolio_convexity,
        allocations=allocations,
        immunization_quality=immunization_quality,
        rebalancing_trigger=rebalancing_trigger,
    )
