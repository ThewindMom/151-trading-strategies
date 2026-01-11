from .inflation_swaps import router as inflation_swaps_router
from .weather_risk import router as weather_risk_router
from .tips_treasury_arbitrage import router as tips_treasury_arbitrage_router
from .spark_spread import router as spark_spread_router

all_routers = [
    inflation_swaps_router,
    weather_risk_router,
    tips_treasury_arbitrage_router,
    spark_spread_router,
]
