from .fx_moving_averages import router as fx_moving_averages_router
from .fx_carry_trade import router as fx_carry_trade_router
from .fx_triangular_arb import router as fx_triangular_arb_router
from .fx_dollar_carry import router as fx_dollar_carry_router
from .fx_momentum_carry_combo import router as fx_momentum_carry_combo_router

all_routers = [
    fx_moving_averages_router,
    fx_carry_trade_router,
    fx_triangular_arb_router,
    fx_dollar_carry_router,
    fx_momentum_carry_combo_router,
]
