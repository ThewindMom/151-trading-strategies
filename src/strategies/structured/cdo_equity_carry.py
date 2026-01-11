"""
Strategy 11.2: CDO Carry (Equity Tranche)
Capture high spread carry from equity tranche while managing first-loss risk.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class CDOEquityCarryRequest(BaseModel):
    equity_spread: float = Field(..., description="Equity tranche spread (bps)")
    attachment_point: float = Field(0.0, description="Equity tranche attachment point")
    detachment_point: float = Field(0.03, description="Equity tranche detachment point (typically 0-3%)")
    expected_default_rate: float = Field(..., description="Expected portfolio default rate (0-1)")
    recovery_rate: float = Field(0.4, description="Expected recovery rate on defaults")
    correlation: float = Field(0.3, description="Default correlation assumption")
    funding_cost: float = Field(0.05, description="Funding cost for position")
    holding_period_days: int = Field(90, description="Holding period in days")
    notional: float = Field(10_000_000, description="Notional amount")


class CDOEquityCarryResponse(BaseModel):
    strategy: str = "cdo_equity_carry"
    signal: int = Field(..., description="1=long equity, -1=short, 0=neutral")
    expected_loss: float = Field(..., description="Expected loss percentage")
    gross_carry: float = Field(..., description="Gross carry (spread income)")
    net_carry: float = Field(..., description="Net carry after expected losses")
    breakeven_default_rate: float = Field(..., description="Default rate where carry = loss")
    risk_reward_ratio: float = Field(..., description="Carry / max loss ratio")
    levered_return: float = Field(..., description="Annualized return on equity")


@router.post("/cdo-equity-carry", response_model=CDOEquityCarryResponse)
def cdo_equity_carry(req: CDOEquityCarryRequest):
    tranche_width = req.detachment_point - req.attachment_point
    
    portfolio_loss = req.expected_default_rate * (1 - req.recovery_rate)
    tranche_loss = max(0, min(portfolio_loss - req.attachment_point, tranche_width))
    expected_loss_pct = tranche_loss / tranche_width if tranche_width > 0 else 0
    
    period_fraction = req.holding_period_days / 365
    gross_carry = (req.equity_spread / 10000) * req.notional * period_fraction
    
    expected_loss_dollar = expected_loss_pct * req.notional * period_fraction
    net_carry = gross_carry - expected_loss_dollar
    
    breakeven_loss = req.equity_spread / 10000
    breakeven_default_rate = (breakeven_loss * tranche_width + req.attachment_point) / (1 - req.recovery_rate)
    breakeven_default_rate = min(1.0, breakeven_default_rate)
    
    max_loss = tranche_width * req.notional
    risk_reward = (net_carry / max_loss) if max_loss > 0 else 0
    
    equity_required = tranche_width * req.notional * 0.5
    levered_return = (net_carry / equity_required) * (365 / req.holding_period_days) if equity_required > 0 else 0
    
    if net_carry > 0 and risk_reward > 0.05 and req.expected_default_rate < breakeven_default_rate * 0.7:
        signal = 1
    elif net_carry < 0 or req.expected_default_rate > breakeven_default_rate:
        signal = -1
    else:
        signal = 0
    
    return CDOEquityCarryResponse(
        signal=signal,
        expected_loss=float(expected_loss_pct),
        gross_carry=float(gross_carry),
        net_carry=float(net_carry),
        breakeven_default_rate=float(breakeven_default_rate),
        risk_reward_ratio=float(risk_reward),
        levered_return=float(levered_return),
    )
