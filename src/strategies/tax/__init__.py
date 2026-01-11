from .muni_tax_arbitrage import router as muni_tax_arbitrage_router
from .cross_border_tax import router as cross_border_tax_router

all_routers = [
    muni_tax_arbitrage_router,
    cross_border_tax_router,
]
