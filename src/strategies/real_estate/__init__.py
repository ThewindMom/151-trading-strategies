from .real_estate_diversity import router as real_estate_diversity_router
from .fix_and_flip import router as fix_and_flip_router
from .intra_asset_diversification import router as intra_asset_diversification_router
from .real_estate_momentum import router as real_estate_momentum_router
from .real_estate_inflation_hedge import router as real_estate_inflation_hedge_router

all_routers = [
    real_estate_diversity_router,
    fix_and_flip_router,
    intra_asset_diversification_router,
    real_estate_momentum_router,
    real_estate_inflation_hedge_router,
]
