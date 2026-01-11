"""
Strategy 15.1: Distressed Debt Investing
Buying bonds of firms in default or near-default at steep discounts.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/distressed", tags=["distressed"])


class DistressedDebtRequest(BaseModel):
    bond_price: float = Field(..., description="Current bond price (cents on dollar)")
    face_value: float = Field(100.0, description="Face value of bond")
    recovery_estimate: float = Field(..., description="Estimated recovery value")
    time_to_resolution: float = Field(..., description="Expected months to resolution")
    senior_claims: float = Field(..., description="Senior claims amount")
    total_assets: float = Field(..., description="Estimated total asset value")
    legal_costs: float = Field(0.1, description="Legal/admin costs as % of assets")
    probability_reorganization: float = Field(0.5, description="Probability of reorganization vs liquidation")


class DistressedDebtResponse(BaseModel):
    strategy: str = "distressed_debt"
    signal: int = Field(..., description="1=buy, -1=avoid, 0=neutral")
    expected_recovery: float = Field(..., description="Expected recovery per $100 face")
    upside_potential: float = Field(..., description="Potential gain (%)")
    downside_risk: float = Field(..., description="Potential loss (%)")
    annualized_return: float = Field(..., description="Annualized expected return")
    coverage_ratio: float = Field(..., description="Asset coverage of claims")


@router.post("/distressed-debt", response_model=DistressedDebtResponse)
def distressed_debt(req: DistressedDebtRequest):
    net_assets = req.total_assets * (1 - req.legal_costs)
    available_for_bond = max(0, net_assets - req.senior_claims)

    liquidation_recovery = min(req.face_value, available_for_bond / req.face_value * 100)
    reorg_recovery = req.recovery_estimate

    expected_recovery = (req.probability_reorganization * reorg_recovery +
                         (1 - req.probability_reorganization) * liquidation_recovery)

    upside_potential = ((expected_recovery - req.bond_price) / req.bond_price) * 100 if req.bond_price > 0 else 0
    downside_risk = ((req.bond_price - liquidation_recovery * 0.5) / req.bond_price) * 100 if req.bond_price > 0 else 0

    months = max(1, req.time_to_resolution)
    total_return = (expected_recovery - req.bond_price) / req.bond_price if req.bond_price > 0 else 0
    annualized_return = ((1 + total_return) ** (12 / months) - 1) * 100

    coverage_ratio = net_assets / (req.senior_claims + req.face_value) if (req.senior_claims + req.face_value) > 0 else 0

    if annualized_return > 25 and coverage_ratio > 0.5:
        signal = 1
    elif annualized_return < 0 or coverage_ratio < 0.3:
        signal = -1
    else:
        signal = 0

    return DistressedDebtResponse(
        signal=signal,
        expected_recovery=float(expected_recovery),
        upside_potential=float(upside_potential),
        downside_risk=float(downside_risk),
        annualized_return=float(annualized_return),
        coverage_ratio=float(coverage_ratio),
    )
