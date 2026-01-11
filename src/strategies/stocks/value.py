"""
Strategy 3.3: Value
Buying high Book-to-Price (B/P) stocks, shorting low B/P.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stocks", tags=["stocks"])


class ValueRequest(BaseModel):
    book_values: dict[str, float] = Field(..., description="Asset to book value per share")
    prices: dict[str, float] = Field(..., description="Asset to current price")
    long_pct: float = Field(0.1, description="Top percentile to go long")
    short_pct: float = Field(0.1, description="Bottom percentile to go short")


class ValueResponse(BaseModel):
    strategy: str = "value"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    bp_ratios: dict[str, float]


@router.post("/value", response_model=ValueResponse)
def value(req: ValueRequest):
    bp_ratios = {}
    for asset in req.book_values:
        if asset in req.prices and req.prices[asset] > 0:
            bp_ratios[asset] = req.book_values[asset] / req.prices[asset]

    sorted_assets = sorted(bp_ratios.keys(), key=lambda x: bp_ratios[x], reverse=True)
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

    return ValueResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        bp_ratios=bp_ratios,
    )
