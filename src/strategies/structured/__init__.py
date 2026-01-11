from .cdo_tranche import router as cdo_tranche_router
from .mbs_trading import router as mbs_trading_router
from .cdo_equity_carry import router as cdo_equity_carry_router
from .cdo_senior_carry import router as cdo_senior_carry_router
from .cdo_tranche_hedging import router as cdo_tranche_hedging_router
from .cdo_cds_hedging import router as cdo_cds_hedging_router
from .cdo_curve_trades import router as cdo_curve_trades_router

all_routers = [
    cdo_tranche_router,
    mbs_trading_router,
    cdo_equity_carry_router,
    cdo_senior_carry_router,
    cdo_tranche_hedging_router,
    cdo_cds_hedging_router,
    cdo_curve_trades_router,
]
