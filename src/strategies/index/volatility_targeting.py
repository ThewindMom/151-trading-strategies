"""
Strategy 6.5: Volatility Targeting
Rebalancing between risky index and cash based on volatility.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/index", tags=["index"])


class VolatilityTargetingRequest(BaseModel):
    returns: list[float] = Field(..., description="Historical return series")
    target_volatility: float = Field(0.15, description="Target annualized volatility")
    lookback: int = Field(20, description="Lookback period for volatility estimation")
    max_leverage: float = Field(2.0, description="Maximum leverage allowed")
    min_weight: float = Field(0.0, description="Minimum weight in risky asset")


class VolatilityTargetingResponse(BaseModel):
    strategy: str = "volatility_targeting"
    risky_weight: float = Field(..., description="Weight in risky index (0-max_leverage)")
    cash_weight: float = Field(..., description="Weight in cash")
    realized_volatility: float
    target_volatility: float
    volatility_ratio: float
    rebalance_needed: bool


@router.post("/volatility-targeting", response_model=VolatilityTargetingResponse)
def volatility_targeting(req: VolatilityTargetingRequest):
    returns = np.array(req.returns[-req.lookback:])
    daily_vol = float(np.std(returns))
    realized_vol = daily_vol * np.sqrt(252)

    volatility_ratio = req.target_volatility / realized_vol if realized_vol > 0 else 1.0

    risky_weight = np.clip(volatility_ratio, req.min_weight, req.max_leverage)
    cash_weight = 1.0 - risky_weight

    current_weight = 1.0
    rebalance_needed = abs(risky_weight - current_weight) > 0.05

    return VolatilityTargetingResponse(
        risky_weight=float(risky_weight),
        cash_weight=float(cash_weight),
        realized_volatility=float(realized_vol),
        target_volatility=req.target_volatility,
        volatility_ratio=float(volatility_ratio),
        rebalance_needed=rebalance_needed,
    )
