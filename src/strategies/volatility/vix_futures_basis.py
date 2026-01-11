"""
Strategy 7.2: VIX Futures Basis
Mean-reversion between VIX spot and VIX futures.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/volatility", tags=["volatility"])


class VixFuturesBasisRequest(BaseModel):
    vix_spot: float = Field(..., description="Current VIX spot level")
    vix_futures: float = Field(..., description="Current VIX futures price")
    historical_basis: list[float] = Field(..., description="Historical basis values")
    lookback: int = Field(60, description="Lookback for mean-reversion stats")
    entry_zscore: float = Field(2.0, description="Z-score threshold for entry")
    exit_zscore: float = Field(0.5, description="Z-score threshold for exit")


class VixFuturesBasisResponse(BaseModel):
    strategy: str = "vix_futures_basis"
    signal: int = Field(..., description="1=long VIX/short futures, -1=reverse, 0=neutral")
    current_basis: float
    basis_pct: float
    zscore: float
    mean_basis: float
    std_basis: float
    contango: bool


@router.post("/vix-futures-basis", response_model=VixFuturesBasisResponse)
def vix_futures_basis(req: VixFuturesBasisRequest):
    current_basis = req.vix_futures - req.vix_spot
    basis_pct = current_basis / req.vix_spot * 100

    historical = np.array(req.historical_basis[-req.lookback:])
    mean_basis = float(np.mean(historical))
    std_basis = float(np.std(historical))

    zscore = (current_basis - mean_basis) / std_basis if std_basis > 0 else 0.0
    contango = current_basis > 0

    signal = 0
    if zscore > req.entry_zscore:
        signal = -1
    elif zscore < -req.entry_zscore:
        signal = 1
    elif abs(zscore) < req.exit_zscore:
        signal = 0

    return VixFuturesBasisResponse(
        signal=signal,
        current_basis=current_basis,
        basis_pct=basis_pct,
        zscore=zscore,
        mean_basis=mean_basis,
        std_basis=std_basis,
        contango=contango,
    )
