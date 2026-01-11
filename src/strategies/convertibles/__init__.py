from .convertible_arbitrage import router as convertible_arbitrage_router
from .oas_arbitrage import router as oas_arbitrage_router

all_routers = [
    convertible_arbitrage_router,
    oas_arbitrage_router,
]
