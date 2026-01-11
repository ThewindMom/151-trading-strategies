from .fundamental_macro import router as fundamental_macro_router
from .economic_announcements import router as economic_announcements_router
from .global_inflation_hedge import router as global_inflation_hedge_router
from .global_fixed_income import router as global_fixed_income_router

all_routers = [
    fundamental_macro_router,
    economic_announcements_router,
    global_inflation_hedge_router,
    global_fixed_income_router,
]
