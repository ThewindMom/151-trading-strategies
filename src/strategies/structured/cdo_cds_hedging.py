"""
Strategy 11.5: CDO Carry (CDS Hedging)
Hedge CDO tranche exposure using single-name or index CDS positions.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class CDSHedge(BaseModel):
    name: str = Field(..., description="CDS reference name or index")
    spread: float = Field(..., description="CDS spread (bps)")
    notional: float = Field(..., description="CDS notional available")
    correlation_to_portfolio: float = Field(..., description="Correlation to CDO portfolio (0-1)")


class CDOCDSHedgingRequest(BaseModel):
    tranche_name: str = Field(..., description="Tranche being hedged")
    tranche_spread: float = Field(..., description="Tranche spread (bps)")
    tranche_notional: float = Field(..., description="Tranche notional")
    tranche_delta: float = Field(..., description="Tranche delta to credit spreads")
    attachment_point: float = Field(..., description="Tranche attachment")
    detachment_point: float = Field(..., description="Tranche detachment")
    available_cds: list[CDSHedge] = Field(..., description="Available CDS for hedging")
    index_spread: float = Field(..., description="CDX/iTraxx index spread (bps)")
    hedge_ratio_target: float = Field(1.0, description="Target hedge ratio (1.0 = fully hedged)")


class CDSHedgeAllocation(BaseModel):
    cds_name: str
    notional: float
    direction: str
    cost_bps: float
    hedge_effectiveness: float


class CDOCDSHedgingResponse(BaseModel):
    strategy: str = "cdo_cds_hedging"
    signal: int = Field(..., description="1=use CDS hedge, -1=use index hedge, 0=no hedge")
    cds_allocations: list[CDSHedgeAllocation]
    index_hedge_notional: float = Field(..., description="Recommended index hedge notional")
    total_hedge_cost: float = Field(..., description="Total hedging cost (bps annualized)")
    basis_risk: float = Field(..., description="Remaining basis risk after hedge")
    net_carry: float = Field(..., description="Net carry after hedge cost")
    hedge_efficiency: float = Field(..., description="Hedge effectiveness ratio")


@router.post("/cdo-cds-hedging", response_model=CDOCDSHedgingResponse)
def cdo_cds_hedging(req: CDOCDSHedgingRequest):
    tranche_width = req.detachment_point - req.attachment_point
    tranche_risk = req.tranche_delta * req.tranche_notional
    target_hedge = tranche_risk * req.hedge_ratio_target
    
    allocations = []
    remaining_hedge = target_hedge
    total_cds_cost = 0.0
    total_effectiveness = 0.0
    
    sorted_cds = sorted(
        req.available_cds,
        key=lambda c: c.spread / c.correlation_to_portfolio if c.correlation_to_portfolio > 0 else float('inf')
    )
    
    for cds in sorted_cds:
        if remaining_hedge <= 0:
            break
        
        effectiveness = cds.correlation_to_portfolio ** 2
        
        hedge_notional = min(
            remaining_hedge / (cds.correlation_to_portfolio if cds.correlation_to_portfolio > 0 else 1),
            cds.notional
        )
        
        cost = cds.spread * hedge_notional / 10000
        
        allocations.append(CDSHedgeAllocation(
            cds_name=cds.name,
            notional=float(hedge_notional),
            direction="buy protection",
            cost_bps=float(cds.spread),
            hedge_effectiveness=float(effectiveness),
        ))
        
        remaining_hedge -= hedge_notional * cds.correlation_to_portfolio
        total_cds_cost += cost
        total_effectiveness += effectiveness * hedge_notional
    
    if remaining_hedge > 0:
        index_hedge_notional = remaining_hedge / 0.8
        index_cost = req.index_spread * index_hedge_notional / 10000
    else:
        index_hedge_notional = 0.0
        index_cost = 0.0
    
    total_hedged = sum(a.notional * a.hedge_effectiveness for a in allocations) + index_hedge_notional * 0.64
    hedge_efficiency = total_hedged / target_hedge if target_hedge > 0 else 0
    
    basis_risk = 1 - min(hedge_efficiency, 1.0)
    
    gross_carry = req.tranche_spread * req.tranche_notional / 10000
    total_cost = total_cds_cost + index_cost
    net_carry = gross_carry - total_cost
    
    if allocations and total_cds_cost < index_cost * 1.2:
        signal = 1
    elif index_hedge_notional > 0:
        signal = -1
    else:
        signal = 0
    
    return CDOCDSHedgingResponse(
        signal=signal,
        cds_allocations=allocations,
        index_hedge_notional=float(index_hedge_notional),
        total_hedge_cost=float(total_cost),
        basis_risk=float(basis_risk),
        net_carry=float(net_carry),
        hedge_efficiency=float(hedge_efficiency),
    )
