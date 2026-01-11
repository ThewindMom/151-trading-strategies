from .vix_futures_basis import router as vix_futures_basis_router
from .volatility_carry import router as volatility_carry_router
from .variance_swaps import router as variance_swaps_router

all_routers = [
    vix_futures_basis_router,
    volatility_carry_router,
    variance_swaps_router,
]
