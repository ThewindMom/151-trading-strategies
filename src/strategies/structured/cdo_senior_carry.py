"""
Strategy 11.3: CDO Carry (Senior/Mezzanine)
Capture carry from senior and mezzanine tranches with lower risk than equity.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class TrancheInput(BaseModel):
    name: str = Field(..., description="Tranche name (e.g., 'senior', 'mezzanine')")
    spread: float = Field(..., description="Tranche spread (bps)")
    attachment_point: float = Field(..., description="Attachment point")
    detachment_point: float = Field(..., description="Detachment point")


class CDOSeniorCarryRequest(BaseModel):
    tranches: list[TrancheInput] = Field(..., description="List of senior/mezz tranches")
    expected_default_rate: float = Field(..., description="Expected portfolio default rate (0-1)")
    recovery_rate: float = Field(0.4, description="Expected recovery rate")
    risk_free_rate: float = Field(0.05, description="Risk-free rate for comparison")
    holding_period_days: int = Field(90, description="Holding period in days")
    target_rating: str = Field("BBB", description="Target minimum rating (AAA, AA, A, BBB)")


class TrancheAnalysis(BaseModel):
    name: str
    signal: int
    spread: float
    expected_loss: float
    net_spread: float
    spread_per_risk: float
    implied_rating: str


class CDOSeniorCarryResponse(BaseModel):
    strategy: str = "cdo_senior_carry"
    tranche_analyses: list[TrancheAnalysis]
    best_tranche: str = Field(..., description="Recommended tranche for carry")
    portfolio_signal: int = Field(..., description="Overall portfolio signal")
    total_expected_carry: float = Field(..., description="Total expected carry (bps)")


@router.post("/cdo-senior-carry", response_model=CDOSeniorCarryResponse)
def cdo_senior_carry(req: CDOSeniorCarryRequest):
    rating_thresholds = {
        "AAA": 0.001,
        "AA": 0.005,
        "A": 0.02,
        "BBB": 0.05,
        "BB": 0.10,
        "B": 0.20,
    }
    
    portfolio_loss = req.expected_default_rate * (1 - req.recovery_rate)
    
    analyses = []
    for tranche in req.tranches:
        width = tranche.detachment_point - tranche.attachment_point
        tranche_loss = max(0, min(portfolio_loss - tranche.attachment_point, width))
        expected_loss_pct = tranche_loss / width if width > 0 else 0
        
        net_spread = tranche.spread - (expected_loss_pct * 10000)
        
        spread_per_risk = net_spread / (expected_loss_pct * 100) if expected_loss_pct > 0 else float('inf')
        
        implied_rating = "NR"
        for rating, threshold in sorted(rating_thresholds.items(), key=lambda x: x[1]):
            if expected_loss_pct <= threshold:
                implied_rating = rating
                break
        else:
            implied_rating = "CCC"
        
        target_threshold = rating_thresholds.get(req.target_rating, 0.05)
        if net_spread > 20 and expected_loss_pct <= target_threshold:
            signal = 1
        elif net_spread < 0 or expected_loss_pct > target_threshold * 2:
            signal = -1
        else:
            signal = 0
        
        analyses.append(TrancheAnalysis(
            name=tranche.name,
            signal=signal,
            spread=tranche.spread,
            expected_loss=float(expected_loss_pct),
            net_spread=float(net_spread),
            spread_per_risk=float(min(spread_per_risk, 1000)),
            implied_rating=implied_rating,
        ))
    
    best_idx = max(range(len(analyses)), key=lambda i: analyses[i].net_spread)
    best_tranche = analyses[best_idx].name
    
    portfolio_signal = 1 if sum(a.signal for a in analyses) > 0 else (-1 if sum(a.signal for a in analyses) < 0 else 0)
    total_carry = sum(a.net_spread for a in analyses if a.signal == 1)
    
    return CDOSeniorCarryResponse(
        tranche_analyses=analyses,
        best_tranche=best_tranche,
        portfolio_signal=portfolio_signal,
        total_expected_carry=float(total_carry),
    )
