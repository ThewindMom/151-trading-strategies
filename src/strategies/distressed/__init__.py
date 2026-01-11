from .distressed_debt import router as distressed_debt_router
from .distress_risk_puzzle import router as distress_risk_puzzle_router
from .active_distressed import router as active_distressed_router

all_routers = [
    distressed_debt_router,
    distress_risk_puzzle_router,
    active_distressed_router,
]
