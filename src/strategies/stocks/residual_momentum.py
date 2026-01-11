"""
Strategy 3.7: Residual Momentum
Momentum based on residuals of Fama-French 3-factor regressions.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class ResidualMomentumRequest(BaseModel):
    stock_returns: dict[str, list[float]] = Field(..., description="Asset to return series")
    market_returns: list[float] = Field(..., description="Market excess returns")
    smb: list[float] = Field(..., description="SMB factor returns")
    hml: list[float] = Field(..., description="HML factor returns")
    lookback: int = Field(12, description="Lookback for residual momentum")
    long_pct: float = Field(0.1)
    short_pct: float = Field(0.1)


class ResidualMomentumResponse(BaseModel):
    strategy: str = "residual_momentum"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    residual_momentum: dict[str, float]


@router.post("/residual-momentum", response_model=ResidualMomentumResponse)
def residual_momentum(req: ResidualMomentumRequest):
    T = len(req.market_returns)
    X = np.column_stack([
        np.ones(T),
        req.market_returns,
        req.smb,
        req.hml,
    ])

    residual_momentum = {}
    for asset, rets in req.stock_returns.items():
        if len(rets) == T:
            y = np.array(rets)
            try:
                beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                residuals = y - X @ beta
                if len(residuals) >= req.lookback:
                    residual_momentum[asset] = float(np.sum(residuals[-req.lookback:]))
            except np.linalg.LinAlgError:
                continue

    sorted_assets = sorted(residual_momentum.keys(), key=lambda x: residual_momentum[x], reverse=True)
    n = len(sorted_assets)
    n_long = max(1, int(n * req.long_pct))
    n_short = max(1, int(n * req.short_pct))

    long_assets = sorted_assets[:n_long]
    short_assets = sorted_assets[-n_short:]

    weights = {}
    for a in long_assets:
        weights[a] = 1.0 / n_long
    for a in short_assets:
        weights[a] = -1.0 / n_short

    return ResidualMomentumResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        residual_momentum=residual_momentum,
    )
