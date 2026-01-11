"""
151 Trading Strategies API
Based on the paper by Zura Kakushadze and Juan Andrés Serur
Implements non-options trading strategies as FastAPI endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from strategies.stocks import all_routers as stock_routers
from strategies.etfs import all_routers as etf_routers
from strategies.fixed_income import all_routers as fixed_income_routers
from strategies.index import all_routers as index_routers
from strategies.volatility import all_routers as volatility_routers
from strategies.fx import all_routers as fx_routers
from strategies.commodities import all_routers as commodity_routers
from strategies.futures import all_routers as futures_routers
from strategies.structured import all_routers as structured_routers
from strategies.convertibles import all_routers as convertibles_routers
from strategies.tax import all_routers as tax_routers
from strategies.misc import all_routers as misc_routers
from strategies.distressed import all_routers as distressed_routers
from strategies.real_estate import all_routers as real_estate_routers
from strategies.crypto import all_routers as crypto_routers
from strategies.macro import all_routers as macro_routers
from strategies.cash import all_routers as cash_routers

app = FastAPI(
    title="151 Trading Strategies API",
    description="""
    Implementation of non-options trading strategies from the paper 
    "151 Trading Strategies" by Kakushadze & Serur.
    
    ## Categories
    - **Stocks**: Price momentum, value, pairs trading, stat arb, etc.
    - **ETFs**: Sector momentum, alpha rotation, leveraged ETF decay
    - **Fixed Income**: Butterflies, carry, yield curve trades
    - **Index**: Cash-and-carry, volatility targeting
    - **Volatility**: VIX basis, variance swaps
    - **FX**: Carry trade, triangular arbitrage
    - **Commodities**: Roll yields, hedging pressure
    - **Futures**: Trend following, contrarian
    - **Structured**: CDO, MBS trading
    - **Convertibles**: Convertible arbitrage
    - **Tax**: Municipal bond arbitrage
    - **Misc**: Inflation swaps, weather risk
    - **Distressed**: Distressed debt, risk puzzle
    - **Real Estate**: Diversification, fix-and-flip
    - **Crypto**: ANN, sentiment analysis
    - **Macro**: Fundamental macro, economic announcements
    - **Cash**: Liquidity management, repo trading, pawnbroking
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in stock_routers:
    app.include_router(router)

for router in etf_routers:
    app.include_router(router)

for router in fixed_income_routers:
    app.include_router(router)

for router in index_routers:
    app.include_router(router)

for router in volatility_routers:
    app.include_router(router)

for router in fx_routers:
    app.include_router(router)

for router in commodity_routers:
    app.include_router(router)

for router in futures_routers:
    app.include_router(router)

for router in structured_routers:
    app.include_router(router)

for router in convertibles_routers:
    app.include_router(router)

for router in tax_routers:
    app.include_router(router)

for router in misc_routers:
    app.include_router(router)

for router in distressed_routers:
    app.include_router(router)

for router in real_estate_routers:
    app.include_router(router)

for router in crypto_routers:
    app.include_router(router)

for router in macro_routers:
    app.include_router(router)

for router in cash_routers:
    app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "151 Trading Strategies API",
        "version": "1.0.0",
        "docs": "/docs",
        "strategies_count": 68,
    }


@app.get("/strategies")
def list_strategies():
    """List all available strategy endpoints"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            if "POST" in route.methods and route.path != "/":
                routes.append({
                    "path": route.path,
                    "name": route.name,
                    "tags": list(route.tags) if hasattr(route, "tags") else [],
                })
    return {"strategies": routes}
