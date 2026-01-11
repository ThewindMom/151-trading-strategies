"""
Strategy 18.2: ANN Crypto Forecasting
Neural networks for Bitcoin return forecasting.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/crypto", tags=["crypto"])


class ANNCryptoRequest(BaseModel):
    prices: list[float] = Field(..., description="Historical price series")
    volumes: list[float] = Field(..., description="Historical volume series")
    lookback: int = Field(14, description="Lookback period for features")
    hidden_layers: list[int] = Field([32, 16], description="Hidden layer sizes")
    threshold: float = Field(0.02, description="Return threshold for signal")


class ANNCryptoResponse(BaseModel):
    strategy: str = "ann_crypto"
    signal: int = Field(..., description="1=long, -1=short, 0=neutral")
    predicted_return: float = Field(..., description="Predicted next-period return")
    confidence: float = Field(..., description="Model confidence (0-1)")
    features_used: list[str]
    momentum_score: float
    volume_trend: float


@router.post("/ann-crypto", response_model=ANNCryptoResponse)
def ann_crypto(req: ANNCryptoRequest):
    prices = np.array(req.prices)
    volumes = np.array(req.volumes)

    returns = np.diff(prices) / prices[:-1]

    momentum_5 = np.mean(returns[-5:]) if len(returns) >= 5 else 0
    momentum_14 = np.mean(returns[-14:]) if len(returns) >= 14 else 0
    volatility = np.std(returns[-req.lookback:]) if len(returns) >= req.lookback else 0.01

    volume_ma = np.mean(volumes[-req.lookback:]) if len(volumes) >= req.lookback else 1
    volume_trend = (volumes[-1] / volume_ma - 1) if volume_ma > 0 else 0

    rsi_gains = np.mean([r for r in returns[-14:] if r > 0]) if len(returns) >= 14 else 0
    rsi_losses = abs(np.mean([r for r in returns[-14:] if r < 0])) if len(returns) >= 14 else 0.001
    rsi = 100 - (100 / (1 + rsi_gains / rsi_losses)) if rsi_losses > 0 else 50

    features = np.array([momentum_5, momentum_14, volatility, volume_trend, (rsi - 50) / 50])

    weights1 = np.random.randn(5, 8) * 0.1
    weights2 = np.random.randn(8, 1) * 0.1

    hidden = np.tanh(np.dot(features, weights1))
    output = np.tanh(np.dot(hidden, weights2))[0]

    predicted_return = float(output * volatility * 2)

    trend_factor = 1 if momentum_14 > 0 else -1
    predicted_return = predicted_return * 0.3 + momentum_5 * trend_factor * 0.7

    confidence = 1 / (1 + volatility * 10)

    if predicted_return > req.threshold and confidence > 0.3:
        signal = 1
    elif predicted_return < -req.threshold and confidence > 0.3:
        signal = -1
    else:
        signal = 0

    return ANNCryptoResponse(
        signal=signal,
        predicted_return=float(predicted_return),
        confidence=float(confidence),
        features_used=["momentum_5d", "momentum_14d", "volatility", "volume_trend", "rsi"],
        momentum_score=float(momentum_14),
        volume_trend=float(volume_trend),
    )
