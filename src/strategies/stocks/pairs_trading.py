"""
Strategy 3.8: Pairs Trading
Mean-reversion between two historically correlated stocks.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class PairsTradingRequest(BaseModel):
    prices_a: list[float] = Field(..., description="Price series for stock A")
    prices_b: list[float] = Field(..., description="Price series for stock B")
    lookback: int = Field(60, description="Lookback for spread calculation")
    entry_zscore: float = Field(2.0, description="Z-score threshold for entry")
    exit_zscore: float = Field(0.5, description="Z-score threshold for exit")


class PairsTradingResponse(BaseModel):
    strategy: str = "pairs_trading"
    signal: int = Field(..., description="1=long spread, -1=short spread, 0=neutral")
    hedge_ratio: float
    spread: float
    zscore: float
    spread_mean: float
    spread_std: float


@router.post("/pairs-trading", response_model=PairsTradingResponse)
def pairs_trading(req: PairsTradingRequest):
    a = np.array(req.prices_a[-req.lookback:])
    b = np.array(req.prices_b[-req.lookback:])

    X = np.column_stack([np.ones(len(b)), b])
    beta, _, _, _ = np.linalg.lstsq(X, a, rcond=None)
    hedge_ratio = float(beta[1])

    spread = a - hedge_ratio * b
    spread_mean = float(np.mean(spread))
    spread_std = float(np.std(spread))

    current_spread = float(spread[-1])
    zscore = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0.0

    signal = 0
    if zscore > req.entry_zscore:
        signal = -1
    elif zscore < -req.entry_zscore:
        signal = 1
    elif abs(zscore) < req.exit_zscore:
        signal = 0

    return PairsTradingResponse(
        signal=signal,
        hedge_ratio=hedge_ratio,
        spread=current_spread,
        zscore=zscore,
        spread_mean=spread_mean,
        spread_std=spread_std,
    )
