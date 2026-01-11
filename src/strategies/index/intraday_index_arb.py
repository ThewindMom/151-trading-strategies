"""
Strategy 6.4: Intraday Index Arbitrage
Mispricings between two ETFs tracking the same index.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/index", tags=["index"])


class IntradayIndexArbRequest(BaseModel):
    etf_a_prices: list[float] = Field(..., description="Price series for ETF A")
    etf_b_prices: list[float] = Field(..., description="Price series for ETF B")
    lookback: int = Field(60, description="Lookback period for spread stats")
    entry_threshold: float = Field(2.0, description="Z-score threshold for entry")
    exit_threshold: float = Field(0.5, description="Z-score threshold for exit")


class IntradayIndexArbResponse(BaseModel):
    strategy: str = "intraday_index_arb"
    signal: int = Field(..., description="1=long A/short B, -1=reverse, 0=neutral")
    spread_ratio: float
    zscore: float
    mean_ratio: float
    std_ratio: float
    deviation_pct: float


@router.post("/intraday-index-arb", response_model=IntradayIndexArbResponse)
def intraday_index_arb(req: IntradayIndexArbRequest):
    a = np.array(req.etf_a_prices[-req.lookback:])
    b = np.array(req.etf_b_prices[-req.lookback:])

    ratio = a / b
    mean_ratio = float(np.mean(ratio))
    std_ratio = float(np.std(ratio))

    current_ratio = float(ratio[-1])
    zscore = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0.0
    deviation_pct = (current_ratio - mean_ratio) / mean_ratio * 100

    signal = 0
    if zscore > req.entry_threshold:
        signal = -1
    elif zscore < -req.entry_threshold:
        signal = 1
    elif abs(zscore) < req.exit_threshold:
        signal = 0

    return IntradayIndexArbResponse(
        signal=signal,
        spread_ratio=current_ratio,
        zscore=zscore,
        mean_ratio=mean_ratio,
        std_ratio=std_ratio,
        deviation_pct=deviation_pct,
    )
