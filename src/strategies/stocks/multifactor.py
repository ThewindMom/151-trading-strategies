"""
Strategy 3.6: Multifactor Portfolio
Combining value, momentum, and other factors via ranking.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class MultifactorRequest(BaseModel):
    factors: dict[str, dict[str, float]] = Field(
        ..., description="Factor name -> {asset: score}"
    )
    factor_weights: dict[str, float] = Field(
        default_factory=dict, description="Factor name -> weight (default equal)"
    )
    long_pct: float = Field(0.1, description="Top percentile to go long")
    short_pct: float = Field(0.1, description="Bottom percentile to go short")


class MultifactorResponse(BaseModel):
    strategy: str = "multifactor"
    long_assets: list[str]
    short_assets: list[str]
    weights: dict[str, float]
    combined_scores: dict[str, float]


@router.post("/multifactor", response_model=MultifactorResponse)
def multifactor(req: MultifactorRequest):
    all_assets = set()
    for factor_scores in req.factors.values():
        all_assets.update(factor_scores.keys())

    factor_weights = req.factor_weights
    if not factor_weights:
        factor_weights = {f: 1.0 / len(req.factors) for f in req.factors}

    def rank_normalize(scores: dict[str, float]) -> dict[str, float]:
        sorted_items = sorted(scores.items(), key=lambda x: x[1])
        n = len(sorted_items)
        return {asset: rank / n for rank, (asset, _) in enumerate(sorted_items)}

    normalized_factors = {
        factor: rank_normalize(scores) for factor, scores in req.factors.items()
    }

    combined_scores = {}
    for asset in all_assets:
        score = 0.0
        for factor, norm_scores in normalized_factors.items():
            if asset in norm_scores:
                score += factor_weights.get(factor, 0) * norm_scores[asset]
        combined_scores[asset] = score

    sorted_assets = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
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

    return MultifactorResponse(
        long_assets=long_assets,
        short_assets=short_assets,
        weights=weights,
        combined_scores=combined_scores,
    )
