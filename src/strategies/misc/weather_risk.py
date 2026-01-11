"""
Strategy 14.3: Weather Risk Hedging
Demand hedging using HDD/CDD (Heating/Cooling Degree Days) indices.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/misc", tags=["misc"])


class WeatherRiskRequest(BaseModel):
    historical_hdd: list[float] = Field(..., description="Historical HDD values")
    historical_cdd: list[float] = Field(..., description="Historical CDD values")
    revenue_sensitivity: float = Field(..., description="Revenue per degree day")
    hdd_futures_price: float = Field(..., description="HDD futures price")
    cdd_futures_price: float = Field(..., description="CDD futures price")
    target_revenue: float = Field(..., description="Target revenue to protect")
    hedge_type: str = Field("hdd", description="'hdd' or 'cdd'")


class WeatherRiskResponse(BaseModel):
    strategy: str = "weather_risk"
    signal: int = Field(..., description="1=buy protection, -1=sell protection, 0=neutral")
    expected_degree_days: float = Field(..., description="Expected HDD or CDD")
    degree_day_std: float = Field(..., description="Standard deviation of degree days")
    contracts_needed: float = Field(..., description="Number of contracts for hedge")
    hedge_cost: float = Field(..., description="Cost of hedge position")
    value_at_risk: float = Field(..., description="Revenue VaR without hedge")


class HddCddSpreadRequest(BaseModel):
    historical_hdd: list[float] = Field(..., description="Historical HDD values")
    historical_cdd: list[float] = Field(..., description="Historical CDD values")
    hdd_futures_price: float = Field(..., description="HDD futures price")
    cdd_futures_price: float = Field(..., description="CDD futures price")


class HddCddSpreadResponse(BaseModel):
    strategy: str = "hdd_cdd_spread"
    signal: int = Field(..., description="1=long HDD/short CDD, -1=reverse, 0=neutral")
    hdd_zscore: float
    cdd_zscore: float
    spread_value: float


@router.post("/weather-risk", response_model=WeatherRiskResponse)
def weather_risk(req: WeatherRiskRequest):
    if req.hedge_type == "hdd":
        dd_data = np.array(req.historical_hdd)
        futures_price = req.hdd_futures_price
    else:
        dd_data = np.array(req.historical_cdd)
        futures_price = req.cdd_futures_price

    expected_dd = float(np.mean(dd_data))
    dd_std = float(np.std(dd_data))

    revenue_volatility = dd_std * req.revenue_sensitivity
    value_at_risk = revenue_volatility * 1.65

    contracts_needed = req.target_revenue / (futures_price * req.revenue_sensitivity) if futures_price > 0 else 0
    hedge_cost = contracts_needed * futures_price * 0.01

    if value_at_risk > req.target_revenue * 0.1:
        signal = 1
    elif value_at_risk < req.target_revenue * 0.02:
        signal = -1
    else:
        signal = 0

    return WeatherRiskResponse(
        signal=signal,
        expected_degree_days=expected_dd,
        degree_day_std=dd_std,
        contracts_needed=float(contracts_needed),
        hedge_cost=float(hedge_cost),
        value_at_risk=float(value_at_risk),
    )


@router.post("/hdd-cdd-spread", response_model=HddCddSpreadResponse)
def hdd_cdd_spread(req: HddCddSpreadRequest):
    hdd_mean = float(np.mean(req.historical_hdd))
    hdd_std = float(np.std(req.historical_hdd))
    cdd_mean = float(np.mean(req.historical_cdd))
    cdd_std = float(np.std(req.historical_cdd))

    hdd_zscore = (req.hdd_futures_price - hdd_mean) / hdd_std if hdd_std > 0 else 0
    cdd_zscore = (req.cdd_futures_price - cdd_mean) / cdd_std if cdd_std > 0 else 0

    spread_value = hdd_zscore - cdd_zscore

    if spread_value > 1.5:
        signal = -1
    elif spread_value < -1.5:
        signal = 1
    else:
        signal = 0

    return HddCddSpreadResponse(
        signal=signal,
        hdd_zscore=float(hdd_zscore),
        cdd_zscore=float(cdd_zscore),
        spread_value=float(spread_value),
    )
