"""
Strategy 5.8: Regression Butterfly
Using historical regression to weight wings vs. the body based on yield curve dynamics.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class RegressionBond(BaseModel):
    cusip: str
    price: float
    yield_to_maturity: float
    maturity_years: float
    duration: float
    convexity: float


class HistoricalYields(BaseModel):
    short_yields: list[float] = Field(..., description="Historical short-term yields")
    body_yields: list[float] = Field(..., description="Historical medium-term yields")
    long_yields: list[float] = Field(..., description="Historical long-term yields")


class RegressionButterflyRequest(BaseModel):
    short_wing: RegressionBond
    body: RegressionBond
    long_wing: RegressionBond
    historical_data: HistoricalYields
    body_notional: float = Field(10_000_000)
    lookback_days: int = Field(252)


class RegressionCoefficients(BaseModel):
    short_beta: float
    long_beta: float
    r_squared: float
    residual_std: float


class RegressionLeg(BaseModel):
    cusip: str
    position: str
    notional: float
    regression_weight: float


class RegressionButterflyResponse(BaseModel):
    strategy: str = "regression_butterfly"
    regression_coeffs: RegressionCoefficients
    short_wing_weight: float
    long_wing_weight: float
    signal: str
    signal_strength: float
    legs: list[RegressionLeg]
    expected_convergence_pnl: float


def run_regression(body_yields: np.ndarray, short_yields: np.ndarray, long_yields: np.ndarray):
    X = np.column_stack([np.ones(len(body_yields)), short_yields, long_yields])
    y = body_yields
    
    try:
        betas = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ betas
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        residual_std = np.std(y - y_pred)
        
        return betas[1], betas[2], r_squared, residual_std, y_pred[-1]
    except Exception:
        return 0.5, 0.5, 0.0, 0.01, body_yields[-1]


@router.post("/regression-butterfly", response_model=RegressionButterflyResponse)
def regression_butterfly(req: RegressionButterflyRequest):
    n = min(req.lookback_days, len(req.historical_data.body_yields))
    
    body_yields = np.array(req.historical_data.body_yields[-n:])
    short_yields = np.array(req.historical_data.short_yields[-n:])
    long_yields = np.array(req.historical_data.long_yields[-n:])
    
    short_beta, long_beta, r_squared, residual_std, predicted_body = run_regression(
        body_yields, short_yields, long_yields
    )
    
    total_beta = abs(short_beta) + abs(long_beta)
    if total_beta > 0:
        short_weight = abs(short_beta) / total_beta
        long_weight = abs(long_beta) / total_beta
    else:
        short_weight = 0.5
        long_weight = 0.5
    
    current_body = req.body.yield_to_maturity
    current_short = req.short_wing.yield_to_maturity
    current_long = req.long_wing.yield_to_maturity
    
    fair_value_body = short_beta * current_short + long_beta * current_long
    mispricing = current_body - fair_value_body
    z_score = mispricing / residual_std if residual_std > 0 else 0
    
    if z_score > 1.5:
        signal = "sell_body"
        position_type = "sell_body"
    elif z_score < -1.5:
        signal = "buy_body"
        position_type = "buy_body"
    else:
        signal = "neutral"
        position_type = "sell_body"
    
    signal_strength = min(abs(z_score) / 3.0, 1.0)
    
    short_notional = req.body_notional * short_weight * 2
    long_notional = req.body_notional * long_weight * 2
    
    if position_type == "sell_body":
        legs = [
            RegressionLeg(cusip=req.short_wing.cusip, position="long", notional=short_notional, regression_weight=short_weight),
            RegressionLeg(cusip=req.body.cusip, position="short", notional=req.body_notional, regression_weight=1.0),
            RegressionLeg(cusip=req.long_wing.cusip, position="long", notional=long_notional, regression_weight=long_weight),
        ]
    else:
        legs = [
            RegressionLeg(cusip=req.short_wing.cusip, position="short", notional=short_notional, regression_weight=short_weight),
            RegressionLeg(cusip=req.body.cusip, position="long", notional=req.body_notional, regression_weight=1.0),
            RegressionLeg(cusip=req.long_wing.cusip, position="short", notional=long_notional, regression_weight=long_weight),
        ]
    
    expected_convergence_pnl = abs(mispricing) * req.body_notional * req.body.duration / 10000
    
    return RegressionButterflyResponse(
        regression_coeffs=RegressionCoefficients(
            short_beta=short_beta,
            long_beta=long_beta,
            r_squared=r_squared,
            residual_std=residual_std,
        ),
        short_wing_weight=short_weight,
        long_wing_weight=long_weight,
        signal=signal,
        signal_strength=signal_strength,
        legs=legs,
        expected_convergence_pnl=expected_convergence_pnl,
    )
