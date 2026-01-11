from .liquidity_management import router as liquidity_management_router
from .repo_trading import router as repo_trading_router
from .pawnbroking import router as pawnbroking_router

all_routers = [
    liquidity_management_router,
    repo_trading_router,
    pawnbroking_router,
]
