"""
Strategy 14.1: Inflation Swaps
Exchanging fixed for floating inflation rates to hedge or speculate on inflation.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/misc", tags=["misc"])


class InflationSwapsRequest(BaseModel):
    breakeven_inflation: float = Field(..., description="Market-implied breakeven inflation rate")
    forecast_inflation: float = Field(..., description="Your inflation forecast")
    swap_rate: float = Field(..., description="Current inflation swap fixed rate")
    real_yield: float = Field(..., description="Real yield (TIPS yield)")
    nominal_yield: float = Field(..., description="Nominal Treasury yield")
    horizon_years: int = Field(5, description="Investment horizon in years")


class InflationSwapsResponse(BaseModel):
    strategy: str = "inflation_swaps"
    signal: int = Field(..., description="1=receive inflation, -1=pay inflation, 0=neutral")
    inflation_edge: float = Field(..., description="Forecast - Breakeven spread")
    fair_swap_rate: float = Field(..., description="Model-implied fair swap rate")
    expected_pnl: float = Field(..., description="Expected P&L per notional")
    risk_premium: float = Field(..., description="Inflation risk premium estimate")


@router.post("/inflation-swaps", response_model=InflationSwapsResponse)
def inflation_swaps(req: InflationSwapsRequest):
    inflation_edge = req.forecast_inflation - req.breakeven_inflation

    fair_swap_rate = req.nominal_yield - req.real_yield

    risk_premium = req.breakeven_inflation - req.forecast_inflation

    expected_pnl = inflation_edge * req.horizon_years * 100

    if inflation_edge > 0.25:
        signal = 1
    elif inflation_edge < -0.25:
        signal = -1
    else:
        signal = 0

    return InflationSwapsResponse(
        signal=signal,
        inflation_edge=float(inflation_edge),
        fair_swap_rate=float(fair_swap_rate),
        expected_pnl=float(expected_pnl),
        risk_premium=float(risk_premium),
    )
