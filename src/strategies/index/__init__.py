from .cash_and_carry import router as cash_and_carry_router
from .intraday_index_arb import router as intraday_index_arb_router
from .volatility_targeting import router as volatility_targeting_router

all_routers = [
    cash_and_carry_router,
    intraday_index_arb_router,
    volatility_targeting_router,
]
