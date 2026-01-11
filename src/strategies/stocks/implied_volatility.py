"""
Strategy 3.5: Implied Volatility
Cross-sectional trade based on changes in call/put implied volatility.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/stocks", tags=["stocks"])


class ImpliedVolatilityRequest(BaseModel):
    iv_changes: dict[str, float] = Field(..., description="Asset to IV change")
    long_pct: float = Field(0.1, description="Bottom percentile (IV decreased) to go long")
    short_pct: float = Field(0.1, description="Top percentile (IV increased) to go short")


class ImpliedVolatilityResponse(BaseModel):
    strategy: str = "implied_volatility"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    iv_changes: dict[str, float]


@router.post("/implied-volatility", response_model=ImpliedVolatilityResponse)
def implied_volatility(req: ImpliedVolatilityRequest):
    sorted_assets = sorted(req.iv_changes.keys(), key=lambda x: req.iv_changes[x])
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

    return ImpliedVolatilityResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        iv_changes=req.iv_changes,
    )
