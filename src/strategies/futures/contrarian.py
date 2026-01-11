"""
Strategy 10.3: Contrarian
Weekly mean-reversion relative to market index.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/futures", tags=["futures"])


class FuturesAsset(BaseModel):
    symbol: str = Field(..., description="Futures symbol")
    weekly_returns: list[float] = Field(..., description="Weekly return series")


class ContrarianRequest(BaseModel):
    assets: list[FuturesAsset] = Field(..., description="List of futures assets")
    market_returns: list[float] = Field(..., description="Market index weekly returns")
    lookback: int = Field(4, description="Lookback weeks for relative performance")
    top_n: int = Field(3, description="Number of assets to long/short")


class ContrarianPosition(BaseModel):
    symbol: str
    signal: int
    relative_return: float
    zscore: float


class ContrarianResponse(BaseModel):
    strategy: str = "contrarian"
    positions: list[ContrarianPosition]
    long_assets: list[str]
    short_assets: list[str]
    market_return: float


@router.post("/contrarian", response_model=ContrarianResponse)
def contrarian(req: ContrarianRequest):
    market = np.array(req.market_returns[-req.lookback:])
    market_cum_return = float(np.prod(1 + market) - 1)

    relative_data = []
    for asset in req.assets:
        returns = np.array(asset.weekly_returns[-req.lookback:])
        asset_cum_return = float(np.prod(1 + returns) - 1)
        relative_return = asset_cum_return - market_cum_return
        relative_data.append({
            "symbol": asset.symbol,
            "relative_return": relative_return,
        })

    rel_returns = np.array([d["relative_return"] for d in relative_data])
    mean_rel = float(np.mean(rel_returns))
    std_rel = float(np.std(rel_returns))

    for d in relative_data:
        d["zscore"] = (d["relative_return"] - mean_rel) / std_rel if std_rel > 0 else 0

    sorted_by_rel = sorted(relative_data, key=lambda x: x["relative_return"])

    positions = []
    long_assets = []
    short_assets = []

    for i, item in enumerate(sorted_by_rel):
        if i < req.top_n:
            positions.append(ContrarianPosition(
                symbol=item["symbol"],
                signal=1,
                relative_return=item["relative_return"],
                zscore=item["zscore"],
            ))
            long_assets.append(item["symbol"])
        elif i >= len(sorted_by_rel) - req.top_n:
            positions.append(ContrarianPosition(
                symbol=item["symbol"],
                signal=-1,
                relative_return=item["relative_return"],
                zscore=item["zscore"],
            ))
            short_assets.append(item["symbol"])

    return ContrarianResponse(
        positions=positions,
        long_assets=long_assets,
        short_assets=short_assets,
        market_return=market_cum_return,
    )
