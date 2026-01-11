from .ann_crypto import router as ann_crypto_router
from .sentiment_crypto import router as sentiment_crypto_router

all_routers = [
    ann_crypto_router,
    sentiment_crypto_router,
]
