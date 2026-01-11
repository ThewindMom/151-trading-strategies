"""
Strategy 3.17: Machine Learning (KNN)
K-nearest neighbor algorithm using technical indicators.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/stocks", tags=["stocks"])


class KNNRequest(BaseModel):
    features: list[list[float]] = Field(..., description="Historical feature vectors")
    labels: list[int] = Field(..., description="Historical labels (1=up, -1=down)")
    current_features: list[float] = Field(..., description="Current feature vector")
    k: int = Field(5, description="Number of neighbors")


class KNNResponse(BaseModel):
    strategy: str = "knn"
    signal: int
    confidence: float
    neighbor_votes: dict[str, int]


@router.post("/knn", response_model=KNNResponse)
def knn(req: KNNRequest):
    X = np.array(req.features)
    y = np.array(req.labels)
    x_new = np.array(req.current_features)

    distances = np.linalg.norm(X - x_new, axis=1)
    nearest_indices = np.argsort(distances)[: req.k]
    nearest_labels = y[nearest_indices]

    up_votes = int(np.sum(nearest_labels == 1))
    down_votes = int(np.sum(nearest_labels == -1))

    if up_votes > down_votes:
        signal = 1
        confidence = up_votes / req.k
    elif down_votes > up_votes:
        signal = -1
        confidence = down_votes / req.k
    else:
        signal = 0
        confidence = 0.5

    return KNNResponse(
        signal=signal,
        confidence=confidence,
        neighbor_votes={"up": up_votes, "down": down_votes},
    )
