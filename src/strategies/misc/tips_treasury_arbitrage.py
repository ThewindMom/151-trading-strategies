"""
Strategy 14.2: TIPS-Treasury Arbitrage
Long TIPS (inflation-protected), short nominal Treasury to capture inflation mispricing.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/misc", tags=["misc"])


class TipsTreasuryArbitrageRequest(BaseModel):
    tips_yield: float = Field(..., description="Real yield on TIPS")
    nominal_treasury_yield: float = Field(..., description="Nominal Treasury yield")
    breakeven_inflation: float = Field(..., description="Market breakeven inflation rate")
    forecast_inflation: float = Field(..., description="Your inflation forecast")
    tips_duration: float = Field(..., description="TIPS modified duration")
    treasury_duration: float = Field(..., description="Treasury modified duration")
    repo_rate: float = Field(..., description="Repo financing rate")
    tips_liquidity_spread: float = Field(0.05, description="TIPS liquidity premium (bps)")


class TipsTreasuryArbitrageResponse(BaseModel):
    strategy: str = "tips_treasury_arbitrage"
    signal: int = Field(..., description="1=long TIPS/short Treasury, -1=reverse, 0=neutral")
    inflation_edge: float = Field(..., description="Forecast vs breakeven spread")
    expected_pnl_bps: float = Field(..., description="Expected P&L in basis points")
    hedge_ratio: float = Field(..., description="Duration-neutral hedge ratio")
    carry_cost: float = Field(..., description="Net carry cost of position")
    breakeven_inflation_move: float = Field(..., description="Inflation move needed to breakeven")


@router.post("/tips-treasury-arbitrage", response_model=TipsTreasuryArbitrageResponse)
def tips_treasury_arbitrage(req: TipsTreasuryArbitrageRequest):
    inflation_edge = req.forecast_inflation - req.breakeven_inflation

    hedge_ratio = req.tips_duration / req.treasury_duration if req.treasury_duration > 0 else 1.0

    carry_long_tips = req.tips_yield
    carry_short_treasury = req.repo_rate - req.nominal_treasury_yield
    net_carry = carry_long_tips + carry_short_treasury - req.tips_liquidity_spread / 100

    expected_pnl_bps = (inflation_edge * req.tips_duration * 100) + (net_carry * 100)

    if req.tips_duration > 0:
        breakeven_inflation_move = -net_carry / req.tips_duration
    else:
        breakeven_inflation_move = 0.0

    carry_cost = -net_carry if net_carry < 0 else 0.0

    if inflation_edge > 0.15 and expected_pnl_bps > 10:
        signal = 1
    elif inflation_edge < -0.15 and expected_pnl_bps < -10:
        signal = -1
    else:
        signal = 0

    return TipsTreasuryArbitrageResponse(
        signal=signal,
        inflation_edge=float(inflation_edge),
        expected_pnl_bps=float(expected_pnl_bps),
        hedge_ratio=float(hedge_ratio),
        carry_cost=float(carry_cost),
        breakeven_inflation_move=float(breakeven_inflation_move),
    )
