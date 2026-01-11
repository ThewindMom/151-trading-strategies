"""
Strategy 4.3: R-Squared
Selection based on the "selectivity" (1-R²) of a regression.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/etfs", tags=["etfs"])


class RSquaredRequest(BaseModel):
    etf_returns: dict[str, list[float]] = Field(..., description="ETF to return series")
    benchmark_returns: list[float] = Field(..., description="Benchmark returns")
    lookback: int = Field(60)
    top_n: int = Field(3)


class RSquaredResponse(BaseModel):
    strategy: str = "r_squared"
    weights: dict[str, float]
    r_squared: dict[str, float]
    selectivity: dict[str, float]
    top_etfs: list[str]


@router.post("/r-squared", response_model=RSquaredResponse)
def r_squared(req: RSquaredRequest):
    bm = np.array(req.benchmark_returns[-req.lookback:])

    r_squared_scores = {}
    selectivity = {}

    for etf, rets in req.etf_returns.items():
        y = np.array(rets[-req.lookback:])
        if len(y) == len(bm):
            X = np.column_stack([np.ones(len(bm)), bm])
            try:
                coeffs, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
                y_pred = X @ coeffs
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                r_squared_scores[etf] = float(r2)
                selectivity[etf] = float(1 - r2)
            except np.linalg.LinAlgError:
                continue

    sorted_etfs = sorted(selectivity.keys(), key=lambda e: selectivity[e], reverse=True)
    top_etfs = sorted_etfs[: req.top_n]

    weights = {}
    for etf in sorted_etfs:
        if etf in top_etfs:
            weights[etf] = 1.0 / req.top_n
        else:
            weights[etf] = 0.0

    return RSquaredResponse(
        weights=weights,
        r_squared=r_squared_scores,
        selectivity=selectivity,
        top_etfs=top_etfs,
    )
