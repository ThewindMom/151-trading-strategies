"""
Strategy 10.1: Hedging with Futures
Cross-hedging and interest rate risk hedging.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/futures", tags=["futures"])


class HedgingWithFuturesRequest(BaseModel):
    spot_position_value: float = Field(..., description="Value of spot position to hedge")
    spot_returns: list[float] = Field(..., description="Historical spot returns")
    futures_returns: list[float] = Field(..., description="Historical futures returns")
    futures_contract_size: float = Field(..., description="Size of one futures contract")
    hedge_ratio_method: str = Field("ols", description="Method: ols, minimum_variance, or naive")


class HedgingWithFuturesResponse(BaseModel):
    strategy: str = "hedging_with_futures"
    hedge_ratio: float
    contracts_needed: int
    correlation: float
    hedge_effectiveness: float
    beta: float
    residual_risk: float


@router.post("/hedging-with-futures", response_model=HedgingWithFuturesResponse)
def hedging_with_futures(req: HedgingWithFuturesRequest):
    spot = np.array(req.spot_returns)
    futures = np.array(req.futures_returns)

    correlation = float(np.corrcoef(spot, futures)[0, 1])
    spot_std = float(np.std(spot))
    futures_std = float(np.std(futures))

    if req.hedge_ratio_method == "ols":
        X = np.column_stack([np.ones(len(futures)), futures])
        beta_vec, _, _, _ = np.linalg.lstsq(X, spot, rcond=None)
        hedge_ratio = float(beta_vec[1])
    elif req.hedge_ratio_method == "minimum_variance":
        hedge_ratio = correlation * (spot_std / futures_std)
    else:
        hedge_ratio = 1.0

    contracts_needed = int(np.round(
        req.spot_position_value * hedge_ratio / req.futures_contract_size
    ))

    hedge_effectiveness = correlation ** 2

    hedged_returns = spot - hedge_ratio * futures
    residual_risk = float(np.std(hedged_returns))

    return HedgingWithFuturesResponse(
        hedge_ratio=hedge_ratio,
        contracts_needed=contracts_needed,
        correlation=correlation,
        hedge_effectiveness=hedge_effectiveness,
        beta=hedge_ratio,
        residual_risk=residual_risk,
    )
