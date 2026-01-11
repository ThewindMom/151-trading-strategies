from .hedging_with_futures import router as hedging_with_futures_router
from .contrarian import router as contrarian_router
from .trend_following import router as trend_following_router
from .calendar_spread import router as calendar_spread_router

all_routers = [
    hedging_with_futures_router,
    contrarian_router,
    trend_following_router,
    calendar_spread_router,
]
