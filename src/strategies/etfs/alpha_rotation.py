"""
Strategy 4.2: Alpha Rotation
Sector rotation using Jensen's alpha as the criterion.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/etfs", tags=["etfs"])


class AlphaRotationRequest(BaseModel):
    sector_returns: dict[str, list[float]] = Field(..., description="Sector to return series")
    market_returns: list[float] = Field(..., description="Market benchmark returns")
    risk_free_rate: float = Field(0.0, description="Risk-free rate per period")
    lookback: int = Field(60)
    top_n: int = Field(3)


class AlphaRotationResponse(BaseModel):
    strategy: str = "alpha_rotation"
    weights: dict[str, float]
    alphas: dict[str, float]
    betas: dict[str, float]
    top_sectors: list[str]


@router.post("/alpha-rotation", response_model=AlphaRotationResponse)
def alpha_rotation(req: AlphaRotationRequest):
    mkt = np.array(req.market_returns[-req.lookback:])
    rf = req.risk_free_rate

    alphas = {}
    betas = {}

    for sector, rets in req.sector_returns.items():
        y = np.array(rets[-req.lookback:]) - rf
        x = mkt - rf
        if len(y) == len(x):
            X = np.column_stack([np.ones(len(x)), x])
            try:
                coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                alphas[sector] = float(coeffs[0])
                betas[sector] = float(coeffs[1])
            except np.linalg.LinAlgError:
                continue

    sorted_sectors = sorted(alphas.keys(), key=lambda s: alphas[s], reverse=True)
    top_sectors = sorted_sectors[: req.top_n]

    weights = {}
    for sector in sorted_sectors:
        if sector in top_sectors:
            weights[sector] = 1.0 / req.top_n
        else:
            weights[sector] = 0.0

    return AlphaRotationResponse(
        weights=weights,
        alphas=alphas,
        betas=betas,
        top_sectors=top_sectors,
    )
