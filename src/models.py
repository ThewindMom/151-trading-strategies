from pydantic import BaseModel, Field
from typing import Optional
import numpy as np


class PriceData(BaseModel):
    prices: list[float] = Field(..., description="Historical price series")
    dates: Optional[list[str]] = Field(None, description="ISO date strings")


class OHLCData(BaseModel):
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: Optional[list[float]] = None
    dates: Optional[list[str]] = None


class MultiAssetData(BaseModel):
    assets: dict[str, list[float]] = Field(..., description="Asset name to price series")
    dates: Optional[list[str]] = None


class StrategyResult(BaseModel):
    strategy: str
    signals: list[int] = Field(..., description="1=long, -1=short, 0=neutral")
    weights: Optional[list[float]] = None
    metadata: Optional[dict] = None


class PortfolioResult(BaseModel):
    strategy: str
    weights: dict[str, float] = Field(..., description="Asset to weight mapping")
    metadata: Optional[dict] = None
