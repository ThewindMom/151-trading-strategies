"""
Strategy 5.15: Swap Spread Arbitrage
Long/short position in interest rate swap vs. Treasury bond to capture swap spread.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class TreasuryBond(BaseModel):
    cusip: str
    maturity_years: float
    yield_to_maturity: float
    duration: float
    dv01: float = Field(..., description="DV01 per $1M face")
    price: float


class InterestRateSwap(BaseModel):
    maturity_years: float
    fixed_rate: float = Field(..., description="Fixed leg rate")
    floating_index: str = Field("SOFR", description="Floating rate index")
    notional: float = Field(10_000_000)
    dv01: float = Field(..., description="DV01 per $1M notional")


class SwapSpreadArbitrageRequest(BaseModel):
    treasury: TreasuryBond
    swap: InterestRateSwap
    current_swap_spread: float = Field(..., description="Current swap spread in bps")
    historical_spread_mean: float = Field(..., description="Historical mean in bps")
    historical_spread_std: float = Field(..., description="Historical std dev in bps")
    funding_rate: float = Field(..., description="Repo rate for Treasury financing")
    notional: float = Field(10_000_000)


class SwapSpreadLeg(BaseModel):
    instrument: str
    position: str
    notional: float
    rate: float
    dv01_contribution: float


class SwapSpreadArbitrageResponse(BaseModel):
    strategy: str = "swap_spread_arbitrage"
    current_spread: float
    fair_value_spread: float
    z_score: float
    trade_direction: str
    legs: list[SwapSpreadLeg]
    net_carry: float
    hedge_ratio: float
    expected_pnl_convergence: float
    risks: list[str]


@router.post("/swap-spread-arbitrage", response_model=SwapSpreadArbitrageResponse)
def swap_spread_arbitrage(req: SwapSpreadArbitrageRequest):
    z_score = (req.current_swap_spread - req.historical_spread_mean) / req.historical_spread_std if req.historical_spread_std > 0 else 0
    
    if z_score > 1.5:
        trade_direction = "receive_swap_long_treasury"
    elif z_score < -1.5:
        trade_direction = "pay_swap_short_treasury"
    else:
        trade_direction = "no_trade"
    
    hedge_ratio = req.swap.dv01 / req.treasury.dv01 if req.treasury.dv01 > 0 else 1.0
    
    treasury_notional = req.notional
    swap_notional = treasury_notional * hedge_ratio
    
    legs = []
    
    if trade_direction == "receive_swap_long_treasury":
        legs = [
            SwapSpreadLeg(
                instrument="treasury",
                position="long",
                notional=treasury_notional,
                rate=req.treasury.yield_to_maturity,
                dv01_contribution=req.treasury.dv01 * (treasury_notional / 1_000_000),
            ),
            SwapSpreadLeg(
                instrument="swap",
                position="receive_fixed",
                notional=swap_notional,
                rate=req.swap.fixed_rate,
                dv01_contribution=-req.swap.dv01 * (swap_notional / 1_000_000),
            ),
        ]
        treasury_carry = req.treasury.yield_to_maturity - req.funding_rate
        swap_carry = req.swap.fixed_rate - req.funding_rate
        net_carry = (treasury_carry - swap_carry) * treasury_notional / 100
        
    elif trade_direction == "pay_swap_short_treasury":
        legs = [
            SwapSpreadLeg(
                instrument="treasury",
                position="short",
                notional=treasury_notional,
                rate=req.treasury.yield_to_maturity,
                dv01_contribution=-req.treasury.dv01 * (treasury_notional / 1_000_000),
            ),
            SwapSpreadLeg(
                instrument="swap",
                position="pay_fixed",
                notional=swap_notional,
                rate=req.swap.fixed_rate,
                dv01_contribution=req.swap.dv01 * (swap_notional / 1_000_000),
            ),
        ]
        short_rebate = req.funding_rate - req.treasury.yield_to_maturity
        swap_pay = req.funding_rate - req.swap.fixed_rate
        net_carry = (short_rebate + swap_pay) * treasury_notional / 100
    else:
        net_carry = 0
    
    spread_deviation = abs(req.current_swap_spread - req.historical_spread_mean)
    expected_pnl = spread_deviation * req.treasury.dv01 * (treasury_notional / 1_000_000) / 100
    
    risks = []
    if abs(z_score) > 3:
        risks.append("extreme_z_score_regime_change_risk")
    if req.swap.maturity_years != req.treasury.maturity_years:
        risks.append("maturity_mismatch")
    risks.append("counterparty_risk_on_swap")
    risks.append("basis_risk_sofr_vs_treasury")
    if trade_direction == "pay_swap_short_treasury":
        risks.append("treasury_borrow_risk")
    
    return SwapSpreadArbitrageResponse(
        current_spread=req.current_swap_spread,
        fair_value_spread=req.historical_spread_mean,
        z_score=z_score,
        trade_direction=trade_direction,
        legs=legs,
        net_carry=net_carry,
        hedge_ratio=hedge_ratio,
        expected_pnl_convergence=expected_pnl,
        risks=risks,
    )
