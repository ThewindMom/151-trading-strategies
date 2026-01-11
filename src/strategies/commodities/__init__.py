from .roll_yields import router as roll_yields_router
from .hedging_pressure import router as hedging_pressure_router
from .portfolio_diversification import router as portfolio_diversification_router
from .commodity_value import router as commodity_value_router
from .skewness_premium import router as skewness_premium_router
from .pricing_models import router as pricing_models_router

all_routers = [
    roll_yields_router,
    hedging_pressure_router,
    portfolio_diversification_router,
    commodity_value_router,
    skewness_premium_router,
    pricing_models_router,
]
