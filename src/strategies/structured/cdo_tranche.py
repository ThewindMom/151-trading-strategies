"""
Strategy 11.2-6: CDO Tranche Trading
Carry and curve trades in CDO tranches (equity, mezzanine, senior).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/structured", tags=["structured"])


class CDOTrancheRequest(BaseModel):
    tranche_spreads: list[float] = Field(..., description="Current spreads by tranche (equity, mezz, senior)")
    expected_defaults: float = Field(..., description="Expected default rate (0-1)")
    recovery_rate: float = Field(0.4, description="Expected recovery on defaults")
    attachment_points: list[float] = Field([0.0, 0.03, 0.07], description="Tranche attachment points")
    detachment_points: list[float] = Field([0.03, 0.07, 0.15], description="Tranche detachment points")
    holding_period_days: int = Field(90, description="Holding period in days")


class CDOTrancheResponse(BaseModel):
    strategy: str = "cdo_tranche"
    tranche_signals: list[int] = Field(..., description="Signal per tranche: 1=long, -1=short, 0=neutral")
    expected_losses: list[float] = Field(..., description="Expected loss per tranche")
    carry_values: list[float] = Field(..., description="Carry (spread - expected loss) per tranche")
    best_tranche: str = Field(..., description="Recommended tranche for carry trade")
    curve_trade: str = Field(..., description="Curve trade recommendation")


@router.post("/cdo-tranche", response_model=CDOTrancheResponse)
def cdo_tranche(req: CDOTrancheRequest):
    expected_losses = []
    for attach, detach in zip(req.attachment_points, req.detachment_points):
        loss_given_default = 1.0 - req.recovery_rate
        tranche_loss = max(0, min(req.expected_defaults * loss_given_default - attach, detach - attach))
        tranche_loss_pct = tranche_loss / (detach - attach) if detach > attach else 0
        expected_losses.append(float(tranche_loss_pct))

    carry_values = []
    for spread, exp_loss in zip(req.tranche_spreads, expected_losses):
        carry = spread - exp_loss * 10000
        carry_values.append(float(carry))

    signals = [1 if c > 50 else (-1 if c < -50 else 0) for c in carry_values]

    tranche_names = ["equity", "mezzanine", "senior"]
    best_idx = int(np.argmax(carry_values))
    worst_idx = int(np.argmin(carry_values))

    curve_trade = f"Long {tranche_names[best_idx]}, Short {tranche_names[worst_idx]}"

    return CDOTrancheResponse(
        tranche_signals=signals,
        expected_losses=expected_losses,
        carry_values=carry_values,
        best_tranche=tranche_names[best_idx],
        curve_trade=curve_trade,
    )
