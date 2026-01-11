"""
Strategy 18.3: Sentiment-Based Crypto Trading
Naive Bayes classification of Twitter/social sentiment for crypto signals.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/crypto", tags=["crypto"])


class SentimentCryptoRequest(BaseModel):
    sentiment_scores: list[float] = Field(..., description="Sentiment scores (-1 to 1) from recent posts")
    sentiment_volumes: list[int] = Field(..., description="Number of posts per period")
    prices: list[float] = Field(..., description="Corresponding price series")
    lookback: int = Field(24, description="Lookback periods (e.g., hours)")
    sentiment_threshold: float = Field(0.2, description="Sentiment threshold for signal")


class SentimentCryptoResponse(BaseModel):
    strategy: str = "sentiment_crypto"
    signal: int = Field(..., description="1=long, -1=short, 0=neutral")
    aggregate_sentiment: float = Field(..., description="Volume-weighted sentiment")
    sentiment_momentum: float = Field(..., description="Change in sentiment")
    bullish_probability: float = Field(..., description="Naive Bayes P(bullish|sentiment)")
    bearish_probability: float = Field(..., description="Naive Bayes P(bearish|sentiment)")
    social_volume_zscore: float


@router.post("/sentiment-crypto", response_model=SentimentCryptoResponse)
def sentiment_crypto(req: SentimentCryptoRequest):
    sentiments = np.array(req.sentiment_scores[-req.lookback:])
    volumes = np.array(req.sentiment_volumes[-req.lookback:])
    prices = np.array(req.prices[-req.lookback:])

    total_volume = np.sum(volumes)
    aggregate_sentiment = float(np.sum(sentiments * volumes) / total_volume) if total_volume > 0 else 0

    half = len(sentiments) // 2
    recent_sentiment = np.mean(sentiments[half:]) if len(sentiments) > half else 0
    older_sentiment = np.mean(sentiments[:half]) if len(sentiments) > half else 0
    sentiment_momentum = recent_sentiment - older_sentiment

    returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else np.array([0])
    bullish_periods = returns > 0.01
    bearish_periods = returns < -0.01

    sentiment_when_bullish = np.mean(sentiments[1:][bullish_periods]) if np.any(bullish_periods) else 0.1
    sentiment_when_bearish = np.mean(sentiments[1:][bearish_periods]) if np.any(bearish_periods) else -0.1

    prior_bullish = 0.5
    prior_bearish = 0.5

    likelihood_bullish = np.exp(-((aggregate_sentiment - sentiment_when_bullish) ** 2) / 0.5)
    likelihood_bearish = np.exp(-((aggregate_sentiment - sentiment_when_bearish) ** 2) / 0.5)

    total = likelihood_bullish * prior_bullish + likelihood_bearish * prior_bearish
    bullish_probability = (likelihood_bullish * prior_bullish / total) if total > 0 else 0.5
    bearish_probability = (likelihood_bearish * prior_bearish / total) if total > 0 else 0.5

    volume_mean = np.mean(volumes)
    volume_std = np.std(volumes) + 0.001
    social_volume_zscore = (volumes[-1] - volume_mean) / volume_std

    if aggregate_sentiment > req.sentiment_threshold and bullish_probability > 0.6:
        signal = 1
    elif aggregate_sentiment < -req.sentiment_threshold and bearish_probability > 0.6:
        signal = -1
    else:
        signal = 0

    return SentimentCryptoResponse(
        signal=signal,
        aggregate_sentiment=float(aggregate_sentiment),
        sentiment_momentum=float(sentiment_momentum),
        bullish_probability=float(bullish_probability),
        bearish_probability=float(bearish_probability),
        social_volume_zscore=float(social_volume_zscore),
    )
