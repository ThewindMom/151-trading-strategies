"""
Strategy 5.4: Ladders
Bonds with equidistant maturities to manage reinvestment risk and provide liquidity.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np
from typing import Optional

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class BondForLadder(BaseModel):
    cusip: str
    coupon_rate: float
    yield_to_maturity: float
    maturity_years: float
    price: float = Field(100.0, description="Bond price as percentage of par")


class LaddersRequest(BaseModel):
    available_bonds: list[BondForLadder]
    num_rungs: int = Field(10, description="Number of rungs in the ladder")
    min_maturity: float = Field(1.0, description="Minimum maturity in years")
    max_maturity: float = Field(10.0, description="Maximum maturity in years")
    portfolio_value: float = Field(1_000_000)
    equal_weight: bool = Field(True, description="Equal weight each rung")


class LadderRung(BaseModel):
    rung_number: int
    target_maturity: float
    cusip: Optional[str]
    actual_maturity: Optional[float]
    weight: float
    face_value: float
    yield_to_maturity: Optional[float]


class LaddersResponse(BaseModel):
    strategy: str = "ladders"
    num_rungs: int
    avg_maturity: float
    portfolio_duration: float
    portfolio_yield: float
    rungs: list[LadderRung]
    reinvestment_schedule: list[float]
    diversification_score: float


@router.post("/ladders", response_model=LaddersResponse)
def ladders_strategy(req: LaddersRequest):
    maturity_step = (req.max_maturity - req.min_maturity) / (req.num_rungs - 1) if req.num_rungs > 1 else 0
    target_maturities = [req.min_maturity + i * maturity_step for i in range(req.num_rungs)]
    
    rungs = []
    selected_bonds = []
    
    for i, target_mat in enumerate(target_maturities):
        best_bond = None
        best_diff = float('inf')
        
        for bond in req.available_bonds:
            diff = abs(bond.maturity_years - target_mat)
            if diff < best_diff and bond.cusip not in [b.cusip for b in selected_bonds]:
                best_diff = diff
                best_bond = bond
        
        weight = 1.0 / req.num_rungs if req.equal_weight else (i + 1) / sum(range(1, req.num_rungs + 1))
        
        if best_bond:
            selected_bonds.append(best_bond)
            rungs.append(LadderRung(
                rung_number=i + 1,
                target_maturity=target_mat,
                cusip=best_bond.cusip,
                actual_maturity=best_bond.maturity_years,
                weight=weight,
                face_value=weight * req.portfolio_value,
                yield_to_maturity=best_bond.yield_to_maturity,
            ))
        else:
            rungs.append(LadderRung(
                rung_number=i + 1,
                target_maturity=target_mat,
                cusip=None,
                actual_maturity=None,
                weight=weight,
                face_value=weight * req.portfolio_value,
                yield_to_maturity=None,
            ))
    
    filled_rungs = [r for r in rungs if r.actual_maturity is not None]
    
    if filled_rungs:
        avg_maturity = np.mean([r.actual_maturity for r in filled_rungs])
        portfolio_yield = np.average(
            [r.yield_to_maturity for r in filled_rungs],
            weights=[r.weight for r in filled_rungs]
        )
        portfolio_duration = avg_maturity * 0.9
    else:
        avg_maturity = 0.0
        portfolio_yield = 0.0
        portfolio_duration = 0.0
    
    reinvestment_schedule = sorted([r.actual_maturity for r in filled_rungs if r.actual_maturity])
    
    if len(reinvestment_schedule) > 1:
        gaps = [reinvestment_schedule[i+1] - reinvestment_schedule[i] 
                for i in range(len(reinvestment_schedule) - 1)]
        gap_variance = np.var(gaps) if gaps else 0
        diversification_score = 1.0 / (1.0 + gap_variance)
    else:
        diversification_score = 0.0
    
    return LaddersResponse(
        num_rungs=req.num_rungs,
        avg_maturity=avg_maturity,
        portfolio_duration=portfolio_duration,
        portfolio_yield=portfolio_yield,
        rungs=rungs,
        reinvestment_schedule=reinvestment_schedule,
        diversification_score=diversification_score,
    )
