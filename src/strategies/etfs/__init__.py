from .sector_momentum import router as sector_momentum_router
from .alpha_rotation import router as alpha_rotation_router
from .r_squared import router as r_squared_router
from .mean_reversion import router as mean_reversion_router
from .leveraged_etfs import router as leveraged_etfs_router
from .multi_asset_trend import router as multi_asset_trend_router

all_routers = [
    sector_momentum_router,
    alpha_rotation_router,
    r_squared_router,
    mean_reversion_router,
    leveraged_etfs_router,
    multi_asset_trend_router,
]
