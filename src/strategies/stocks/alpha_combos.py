"""
Strategy 3.20: Alpha Combos
Combining a large number of machine-learned alpha signals.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class AlphaCombosRequest(BaseModel):
    alphas: dict[str, dict[str, float]] = Field(
        ..., description="Alpha name -> {asset: alpha_score}"
    )
    alpha_weights: dict[str, float] = Field(
        default_factory=dict, description="Alpha name -> weight"
    )
    decay_factor: float = Field(1.0, description="Decay factor for alpha weighting")
    neutralize: bool = Field(True, description="Make portfolio dollar-neutral")


class AlphaCombosResponse(BaseModel):
    strategy: str = "alpha_combos"
    weights: dict[str, float]
    combined_alphas: dict[str, float]
    long_assets: list[str]
    short_assets: list[str]


@router.post("/alpha-combos", response_model=AlphaCombosResponse)
def alpha_combos(req: AlphaCombosRequest):
    all_assets = set()
    for alpha_scores in req.alphas.values():
        all_assets.update(alpha_scores.keys())

    alpha_weights = req.alpha_weights
    if not alpha_weights:
        alpha_weights = {a: 1.0 / len(req.alphas) for a in req.alphas}

    combined_alphas = {}
    for asset in all_assets:
        combined = 0.0
        for alpha_name, scores in req.alphas.items():
            if asset in scores:
                combined += alpha_weights.get(alpha_name, 0) * scores[asset]
        combined_alphas[asset] = combined * req.decay_factor

    if req.neutralize:
        mean_alpha = np.mean(list(combined_alphas.values()))
        combined_alphas = {a: v - mean_alpha for a, v in combined_alphas.items()}

    total_abs = sum(abs(v) for v in combined_alphas.values())
    if total_abs > 0:
        weights = {a: v / total_abs for a, v in combined_alphas.items()}
    else:
        weights = {a: 0.0 for a in combined_alphas}

    long_assets = [a for a, w in weights.items() if w > 0]
    short_assets = [a for a, w in weights.items() if w < 0]

    return AlphaCombosResponse(
        weights=weights,
        combined_alphas=combined_alphas,
        long_assets=long_assets,
        short_assets=short_assets,
    )
