# 151 Trading Strategies API

FastAPI implementation of non-options trading strategies from the paper "151 Trading Strategies" by Zura Kakushadze and Juan Andrés Serur.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
cd src
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

## Implemented Strategies (68 total)

### Stocks (20 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /stocks/price-momentum | 3.1 Price Momentum |
| POST /stocks/earnings-momentum | 3.2 Earnings Momentum (SUE) |
| POST /stocks/value | 3.3 Value (Book-to-Price) |
| POST /stocks/low-volatility | 3.4 Low-Volatility Anomaly |
| POST /stocks/implied-volatility | 3.5 Implied Volatility |
| POST /stocks/multifactor | 3.6 Multifactor Portfolio |
| POST /stocks/residual-momentum | 3.7 Residual Momentum |
| POST /stocks/pairs-trading | 3.8 Pairs Trading |
| POST /stocks/mean-reversion-cluster | 3.9 Mean-Reversion Cluster |
| POST /stocks/weighted-regression | 3.10 Weighted Regression |
| POST /stocks/single-ma | 3.11 Single Moving Average |
| POST /stocks/two-ma | 3.12 Two Moving Averages |
| POST /stocks/three-ma | 3.13 Three Moving Averages |
| POST /stocks/support-resistance | 3.14 Support and Resistance |
| POST /stocks/channel | 3.15 Channel |
| POST /stocks/event-driven | 3.16 Event-Driven (M&A) |
| POST /stocks/knn | 3.17 Machine Learning (KNN) |
| POST /stocks/stat-arb | 3.18 Statistical Arbitrage |
| POST /stocks/market-making | 3.19 Market-Making |
| POST /stocks/alpha-combos | 3.20 Alpha Combos |

### ETFs (6 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /etfs/sector-momentum | 4.1 Sector Momentum |
| POST /etfs/alpha-rotation | 4.2 Alpha Rotation |
| POST /etfs/r-squared | 4.3 R-Squared |
| POST /etfs/mean-reversion-ibs | 4.4 Mean-Reversion (IBS) |
| POST /etfs/leveraged-etfs | 4.5 Leveraged ETFs |
| POST /etfs/multi-asset-trend | 4.6 Multi-Asset Trend |

### Fixed Income (14 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /fixed-income/bullets | 5.2 Bullets |
| POST /fixed-income/barbells | 5.3 Barbells |
| POST /fixed-income/ladders | 5.4 Ladders |
| POST /fixed-income/immunization | 5.5 Bond Immunization |
| POST /fixed-income/dollar-duration-butterfly | 5.6 Dollar-Duration Butterfly |
| POST /fixed-income/fifty-fifty-butterfly | 5.7 Fifty-Fifty Butterfly |
| POST /fixed-income/regression-butterfly | 5.8 Regression Butterfly |
| POST /fixed-income/low-risk-factor | 5.9 Low-Risk Factor |
| POST /fixed-income/value-factor | 5.10 Value Factor |
| POST /fixed-income/carry-factor | 5.11 Carry Factor |
| POST /fixed-income/rolling-down | 5.12 Rolling Down Yield Curve |
| POST /fixed-income/yield-curve-spreads | 5.13 Yield Curve Spreads |
| POST /fixed-income/cds-basis | 5.14 CDS Basis Arbitrage |
| POST /fixed-income/swap-spread | 5.15 Swap-Spread Arbitrage |

### Index (3 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /index/cash-and-carry | 6.2 Cash-and-Carry Arbitrage |
| POST /index/intraday-arb | 6.4 Intraday Index Arbitrage |
| POST /index/volatility-targeting | 6.5 Volatility Targeting |

### Volatility (3 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /volatility/vix-futures-basis | 7.2 VIX Futures Basis |
| POST /volatility/volatility-carry | 7.3 Volatility Carry |
| POST /volatility/variance-swaps | 7.6 Variance Swaps |

### FX (3 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /fx/moving-averages | 8.1 FX Moving Averages |
| POST /fx/carry-trade | 8.2 FX Carry Trade |
| POST /fx/triangular-arb | 8.5 FX Triangular Arbitrage |

### Commodities (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /commodities/roll-yields | 9.1 Roll Yields |
| POST /commodities/hedging-pressure | 9.2 Hedging Pressure |

### Futures (3 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /futures/hedging | 10.1 Hedging with Futures |
| POST /futures/contrarian | 10.3 Contrarian |
| POST /futures/trend-following | 10.4 Trend Following |

### Structured Products (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /structured/cdo-tranche | 11.2-6 CDO Tranche Trading |
| POST /structured/mbs | 11.7 MBS Trading |

### Convertibles (1 strategy)
| Endpoint | Strategy |
|----------|----------|
| POST /convertibles/arbitrage | 12.1 Convertible Arbitrage |

### Tax (1 strategy)
| Endpoint | Strategy |
|----------|----------|
| POST /tax/muni-arbitrage | 13.1 Municipal Tax Arbitrage |

### Misc (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /misc/inflation-swaps | 14.1 Inflation Swaps |
| POST /misc/weather-risk | 14.3 Weather Risk |

### Distressed (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /distressed/distressed-debt | 15.1 Distressed Debt |
| POST /distressed/risk-puzzle | 15.3 Distress Risk Puzzle |

### Real Estate (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /real-estate/diversity | 16.2 Real Estate Diversity |
| POST /real-estate/fix-and-flip | 16.6 Fix-and-Flip |

### Crypto (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /crypto/ann | 18.2 ANN (Neural Network) |
| POST /crypto/sentiment | 18.3 Sentiment Analysis |

### Macro (2 strategies)
| Endpoint | Strategy |
|----------|----------|
| POST /macro/fundamental | 19.2 Fundamental Macro |
| POST /macro/economic-announcements | 19.5 Economic Announcements |

## Example Usage

```python
import requests

# Price Momentum Strategy
response = requests.post("http://localhost:8000/stocks/price-momentum", json={
    "prices": {
        "AAPL": [150, 152, 155, 160, 165, 170, 175, 180, 185, 190, 195, 200, 205],
        "GOOG": [100, 102, 101, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90],
        "MSFT": [200, 205, 210, 215, 220, 225, 230, 235, 240, 245, 250, 255, 260]
    },
    "lookback": 12,
    "long_pct": 0.3,
    "short_pct": 0.3
})
print(response.json())
```

## Excluded Options-Based Strategies

The following strategies from the paper are NOT implemented as they require options:
- Section 2 (all options strategies: covered calls, spreads, straddles, etc.)
- Strategy 6.3 (Dispersion Trading)
- Strategy 7.4 (Volatility Risk Premium)
- Strategy 7.5 (Volatility Skew)
- Strategy 13.2 (Cross-border Tax Arbitrage with options)

## Reference

Kakushadze, Z., & Serur, J. A. (2018). 151 Trading Strategies. SSRN Electronic Journal.
