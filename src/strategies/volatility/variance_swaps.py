"""
Strategy 7.6: Variance Swaps
Payoff based on realized variance vs. strike variance.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/volatility", tags=["volatility"])


class VarianceSwapsRequest(BaseModel):
    returns: list[float] = Field(..., description="Daily return series")
    strike_volatility: float = Field(..., description="Strike volatility (annualized)")
    notional: float = Field(100000, description="Vega notional")
    days_elapsed: int = Field(..., description="Days since swap inception")
    total_days: int = Field(252, description="Total days in swap period")


class VarianceSwapsResponse(BaseModel):
    strategy: str = "variance_swaps"
    signal: int = Field(..., description="1=long variance, -1=short variance, 0=neutral")
    realized_variance: float
    strike_variance: float
    variance_pnl: float
    annualized_realized_vol: float
    vol_spread: float
    mark_to_market: float


@router.post("/variance-swaps", response_model=VarianceSwapsResponse)
def variance_swaps(req: VarianceSwapsRequest):
    returns = np.array(req.returns)
    realized_var_daily = float(np.var(returns, ddof=1))
    realized_variance = realized_var_daily * 252
    annualized_realized_vol = float(np.sqrt(realized_variance))

    strike_variance = req.strike_volatility ** 2
    variance_pnl = (realized_variance - strike_variance) * req.notional

    time_weight = req.days_elapsed / req.total_days
    mark_to_market = variance_pnl * time_weight

    vol_spread = annualized_realized_vol - req.strike_volatility

    if annualized_realized_vol > req.strike_volatility * 1.1:
        signal = 1
    elif annualized_realized_vol < req.strike_volatility * 0.9:
        signal = -1
    else:
        signal = 0

    return VarianceSwapsResponse(
        signal=signal,
        realized_variance=realized_variance,
        strike_variance=strike_variance,
        variance_pnl=variance_pnl,
        annualized_realized_vol=annualized_realized_vol,
        vol_spread=vol_spread,
        mark_to_market=mark_to_market,
    )
