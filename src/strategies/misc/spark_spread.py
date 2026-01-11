"""
Strategy 14.4: Energy Spark Spread
Trading the price differential between natural gas and electricity prices.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/misc", tags=["misc"])


class SparkSpreadRequest(BaseModel):
    electricity_price: float = Field(..., description="Electricity price ($/MWh)")
    gas_price: float = Field(..., description="Natural gas price ($/MMBtu)")
    heat_rate: float = Field(7.0, description="Heat rate - MMBtu gas per MWh electricity")
    historical_spark_spread: float = Field(..., description="Historical average spark spread")
    variable_om_cost: float = Field(3.0, description="Variable O&M cost ($/MWh)")
    capacity_factor: float = Field(0.85, description="Plant capacity factor (0-1)")
    carbon_price: float = Field(0.0, description="Carbon price ($/ton CO2)")
    gas_carbon_intensity: float = Field(0.053, description="Gas CO2 emissions (tons/MMBtu)")


class SparkSpreadResponse(BaseModel):
    strategy: str = "spark_spread"
    signal: int = Field(..., description="1=long spark spread, -1=short, 0=neutral")
    current_spark_spread: float = Field(..., description="Current spark spread ($/MWh)")
    clean_spark_spread: float = Field(..., description="Spark spread net of carbon cost")
    spread_zscore: float = Field(..., description="Current spread vs historical (z-score approx)")
    plant_margin: float = Field(..., description="Implied generation margin ($/MWh)")
    breakeven_gas_price: float = Field(..., description="Gas price where spread = 0")


@router.post("/spark-spread", response_model=SparkSpreadResponse)
def spark_spread(req: SparkSpreadRequest):
    gas_cost_per_mwh = req.gas_price * req.heat_rate

    current_spark_spread = req.electricity_price - gas_cost_per_mwh

    carbon_cost_per_mwh = req.carbon_price * req.gas_carbon_intensity * req.heat_rate
    clean_spark_spread = current_spark_spread - carbon_cost_per_mwh

    spread_deviation = current_spark_spread - req.historical_spark_spread
    spread_zscore = spread_deviation / 5.0

    plant_margin = clean_spark_spread - req.variable_om_cost

    if req.heat_rate > 0:
        breakeven_gas_price = (req.electricity_price - req.variable_om_cost - carbon_cost_per_mwh) / req.heat_rate
    else:
        breakeven_gas_price = 0.0

    if spread_zscore > 1.0 and clean_spark_spread > req.historical_spark_spread:
        signal = 1
    elif spread_zscore < -1.0 and clean_spark_spread < req.historical_spark_spread:
        signal = -1
    else:
        signal = 0

    return SparkSpreadResponse(
        signal=signal,
        current_spark_spread=float(current_spark_spread),
        clean_spark_spread=float(clean_spark_spread),
        spread_zscore=float(spread_zscore),
        plant_margin=float(plant_margin),
        breakeven_gas_price=float(breakeven_gas_price),
    )
