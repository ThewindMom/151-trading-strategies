from .bullets import router as bullets_router
from .barbells import router as barbells_router
from .ladders import router as ladders_router
from .bond_immunization import router as bond_immunization_router
from .dollar_duration_butterfly import router as dollar_duration_butterfly_router
from .fifty_fifty_butterfly import router as fifty_fifty_butterfly_router
from .regression_butterfly import router as regression_butterfly_router
from .low_risk_factor import router as low_risk_factor_router
from .value_factor import router as value_factor_router
from .carry_factor import router as carry_factor_router
from .rolling_down_yield_curve import router as rolling_down_yield_curve_router
from .yield_curve_spreads import router as yield_curve_spreads_router
from .cds_basis_arbitrage import router as cds_basis_arbitrage_router
from .swap_spread_arbitrage import router as swap_spread_arbitrage_router

all_routers = [
    bullets_router,
    barbells_router,
    ladders_router,
    bond_immunization_router,
    dollar_duration_butterfly_router,
    fifty_fifty_butterfly_router,
    regression_butterfly_router,
    low_risk_factor_router,
    value_factor_router,
    carry_factor_router,
    rolling_down_yield_curve_router,
    yield_curve_spreads_router,
    cds_basis_arbitrage_router,
    swap_spread_arbitrage_router,
]
