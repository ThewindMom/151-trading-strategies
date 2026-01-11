"""
Strategy 5.14: CDS Basis Arbitrage
Buying a bond and insuring it with CDS to exploit the basis between bond spread and CDS spread.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class BondForCDS(BaseModel):
    cusip: str
    issuer: str
    price: float
    yield_to_maturity: float
    spread_to_treasury: float = Field(..., description="Spread over Treasury in bps")
    maturity_years: float
    duration: float
    face_value: float = Field(1_000_000)


class CDSContract(BaseModel):
    reference_entity: str
    cds_spread: float = Field(..., description="CDS spread in bps")
    maturity_years: float
    notional: float = Field(1_000_000)
    upfront_fee: float = Field(0.0, description="Upfront fee as percentage")


class CDSBasisArbitrageRequest(BaseModel):
    bond: BondForCDS
    cds: CDSContract
    funding_rate: float = Field(..., description="Repo/funding rate")
    transaction_costs: float = Field(5.0, description="Transaction costs in bps")
    holding_period: float = Field(1.0, description="Expected holding period in years")


class CDSBasisArbitrageResponse(BaseModel):
    strategy: str = "cds_basis_arbitrage"
    basis: float = Field(..., description="CDS-Bond basis in bps (positive = negative basis)")
    trade_type: str = Field(..., description="negative_basis_trade or positive_basis_trade")
    bond_position: str
    cds_position: str
    carry: float
    net_spread: float
    breakeven_default_prob: float
    expected_pnl: float
    risk_factors: list[str]


@router.post("/cds-basis-arbitrage", response_model=CDSBasisArbitrageResponse)
def cds_basis_arbitrage(req: CDSBasisArbitrageRequest):
    basis = req.cds.cds_spread - req.bond.spread_to_treasury
    
    if basis < -req.transaction_costs:
        trade_type = "negative_basis_trade"
        bond_position = "long"
        cds_position = "buy_protection"
        net_spread = abs(basis) - req.transaction_costs
    elif basis > req.transaction_costs:
        trade_type = "positive_basis_trade"
        bond_position = "short"
        cds_position = "sell_protection"
        net_spread = basis - req.transaction_costs
    else:
        trade_type = "no_trade"
        bond_position = "none"
        cds_position = "none"
        net_spread = 0
    
    if trade_type == "negative_basis_trade":
        bond_carry = req.bond.yield_to_maturity - req.funding_rate
        cds_cost = req.cds.cds_spread / 100
        carry = (bond_carry - cds_cost) * 100
    elif trade_type == "positive_basis_trade":
        short_rebate = req.funding_rate - req.bond.yield_to_maturity
        cds_premium = req.cds.cds_spread / 100
        carry = (short_rebate + cds_premium) * 100
    else:
        carry = 0
    
    recovery_rate = 0.40
    expected_loss_rate = (1 - recovery_rate)
    breakeven_default_prob = net_spread / 100 / expected_loss_rate if expected_loss_rate > 0 else 0
    
    expected_pnl = (net_spread / 100) * req.bond.face_value * req.holding_period
    
    risk_factors = []
    if abs(basis) > 100:
        risk_factors.append("large_basis_may_indicate_liquidity_risk")
    if req.bond.duration > 10:
        risk_factors.append("high_duration_sensitivity")
    if req.cds.maturity_years != req.bond.maturity_years:
        risk_factors.append("maturity_mismatch")
    if trade_type == "positive_basis_trade":
        risk_factors.append("short_bond_requires_borrow")
    
    return CDSBasisArbitrageResponse(
        basis=basis,
        trade_type=trade_type,
        bond_position=bond_position,
        cds_position=cds_position,
        carry=carry,
        net_spread=net_spread,
        breakeven_default_prob=breakeven_default_prob,
        expected_pnl=expected_pnl,
        risk_factors=risk_factors,
    )
