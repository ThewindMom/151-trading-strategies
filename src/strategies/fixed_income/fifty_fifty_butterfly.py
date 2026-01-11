"""
Strategy 5.7: Fifty-Fifty Butterfly
A neutral curve butterfly with equal dollar durations on wings, betting on curve curvature changes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/fixed-income", tags=["fixed-income"])


class FiftyFiftyBond(BaseModel):
    cusip: str
    price: float
    yield_to_maturity: float
    maturity_years: float
    duration: float
    convexity: float


class FiftyFiftyButterflyRequest(BaseModel):
    short_wing: FiftyFiftyBond
    body: FiftyFiftyBond
    long_wing: FiftyFiftyBond
    body_notional: float = Field(10_000_000)
    position_type: str = Field("sell_body", description="sell_body or buy_body")


class FiftyFiftyLeg(BaseModel):
    cusip: str
    position: str
    notional: float
    dollar_duration: float
    weight: float


class FiftyFiftyButterflyResponse(BaseModel):
    strategy: str = "fifty_fifty_butterfly"
    short_wing_weight: float
    long_wing_weight: float
    net_dollar_duration: float
    net_convexity: float
    curvature_exposure: float
    legs: list[FiftyFiftyLeg]
    expected_pnl_hump: float
    expected_pnl_trough: float


@router.post("/fifty-fifty-butterfly", response_model=FiftyFiftyButterflyResponse)
def fifty_fifty_butterfly(req: FiftyFiftyButterflyRequest):
    body_dollar_duration = req.body.duration * req.body_notional / 100
    
    wing_dollar_duration_each = body_dollar_duration / 2
    
    short_notional = (wing_dollar_duration_each * 100) / req.short_wing.duration
    long_notional = (wing_dollar_duration_each * 100) / req.long_wing.duration
    
    total_wing_notional = short_notional + long_notional
    short_weight = short_notional / total_wing_notional
    long_weight = long_notional / total_wing_notional
    
    short_dd = req.short_wing.duration * short_notional / 100
    long_dd = req.long_wing.duration * long_notional / 100
    
    if req.position_type == "sell_body":
        net_dd = short_dd + long_dd - body_dollar_duration
        body_sign = -1
    else:
        net_dd = -short_dd - long_dd + body_dollar_duration
        body_sign = 1
    
    short_conv = req.short_wing.convexity * short_notional / 100
    body_conv = req.body.convexity * req.body_notional / 100
    long_conv = req.long_wing.convexity * long_notional / 100
    
    if req.position_type == "sell_body":
        net_convexity = short_conv + long_conv - body_conv
    else:
        net_convexity = -short_conv - long_conv + body_conv
    
    curvature_exposure = net_convexity / req.body_notional * 10000
    
    legs = [
        FiftyFiftyLeg(
            cusip=req.short_wing.cusip,
            position="long" if req.position_type == "sell_body" else "short",
            notional=short_notional,
            dollar_duration=short_dd,
            weight=0.5,
        ),
        FiftyFiftyLeg(
            cusip=req.body.cusip,
            position="short" if req.position_type == "sell_body" else "long",
            notional=req.body_notional,
            dollar_duration=body_dollar_duration,
            weight=1.0,
        ),
        FiftyFiftyLeg(
            cusip=req.long_wing.cusip,
            position="long" if req.position_type == "sell_body" else "short",
            notional=long_notional,
            dollar_duration=long_dd,
            weight=0.5,
        ),
    ]
    
    curvature_change = 10
    expected_pnl_hump = net_convexity * curvature_change if req.position_type == "sell_body" else -net_convexity * curvature_change
    expected_pnl_trough = -net_convexity * curvature_change if req.position_type == "sell_body" else net_convexity * curvature_change
    
    return FiftyFiftyButterflyResponse(
        short_wing_weight=short_weight,
        long_wing_weight=long_weight,
        net_dollar_duration=net_dd,
        net_convexity=net_convexity,
        curvature_exposure=curvature_exposure,
        legs=legs,
        expected_pnl_hump=expected_pnl_hump,
        expected_pnl_trough=expected_pnl_trough,
    )
