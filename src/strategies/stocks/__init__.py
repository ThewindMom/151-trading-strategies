from .price_momentum import router as price_momentum_router
from .earnings_momentum import router as earnings_momentum_router
from .value import router as value_router
from .low_volatility import router as low_volatility_router
from .implied_volatility import router as implied_volatility_router
from .multifactor import router as multifactor_router
from .residual_momentum import router as residual_momentum_router
from .pairs_trading import router as pairs_trading_router
from .mean_reversion_cluster import router as mean_reversion_cluster_router
from .weighted_regression import router as weighted_regression_router
from .single_ma import router as single_ma_router
from .two_ma import router as two_ma_router
from .three_ma import router as three_ma_router
from .support_resistance import router as support_resistance_router
from .channel import router as channel_router
from .event_driven import router as event_driven_router
from .knn import router as knn_router
from .stat_arb import router as stat_arb_router
from .market_making import router as market_making_router
from .alpha_combos import router as alpha_combos_router

all_routers = [
    price_momentum_router,
    earnings_momentum_router,
    value_router,
    low_volatility_router,
    implied_volatility_router,
    multifactor_router,
    residual_momentum_router,
    pairs_trading_router,
    mean_reversion_cluster_router,
    weighted_regression_router,
    single_ma_router,
    two_ma_router,
    three_ma_router,
    support_resistance_router,
    channel_router,
    event_driven_router,
    knn_router,
    stat_arb_router,
    market_making_router,
    alpha_combos_router,
]
