"""
Strategy 12.2: Convertible Option-Adjusted Spread (OAS) Analysis
Identify mispriced convertibles by analyzing option-adjusted spreads.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
import numpy as np

router = APIRouter(prefix="/convertibles", tags=["convertibles"])


class ConvertibleBond(BaseModel):
    symbol: str = Field(..., description="Convertible bond identifier")
    bond_price: float = Field(..., description="Current bond price")
    stock_price: float = Field(..., description="Current underlying stock price")
    conversion_ratio: float = Field(..., description="Shares per bond on conversion")
    coupon_rate: float = Field(..., description="Annual coupon rate")
    years_to_maturity: float = Field(..., description="Years to maturity")
    credit_spread: float = Field(..., description="Credit spread over risk-free (bps)")
    implied_vol: float = Field(..., description="Implied volatility of embedded option")
    call_price: float = Field(None, description="Optional: call price if callable")


class OASArbitrageRequest(BaseModel):
    bonds: list[ConvertibleBond] = Field(..., description="List of convertible bonds to analyze")
    risk_free_rate: float = Field(0.05, description="Risk-free interest rate")
    sector_avg_oas: float = Field(None, description="Optional: sector average OAS for comparison")
    vol_surface: dict[str, float] = Field(None, description="Optional: vol surface for comparison")


class OASAnalysis(BaseModel):
    symbol: str
    signal: int
    parity: float
    bond_floor: float
    option_value: float
    oas: float
    oas_zscore: float
    theoretical_price: float
    mispricing: float
    delta: float
    gamma: float


class OASArbitrageResponse(BaseModel):
    strategy: str = "oas_arbitrage"
    analyses: list[OASAnalysis]
    best_long: str = Field(None, description="Best long opportunity")
    best_short: str = Field(None, description="Best short opportunity")
    portfolio_signal: int = Field(..., description="Overall signal")
    avg_oas: float = Field(..., description="Average OAS across universe")


@router.post("/oas-arbitrage", response_model=OASArbitrageResponse)
def oas_arbitrage(req: OASArbitrageRequest):
    analyses = []
    oas_values = []
    
    for bond in req.bonds:
        parity = bond.stock_price * bond.conversion_ratio
        
        coupon_pv = sum(
            bond.coupon_rate * 100 / ((1 + req.risk_free_rate + bond.credit_spread / 10000) ** t)
            for t in range(1, int(bond.years_to_maturity) + 1)
        )
        principal_pv = 100 / ((1 + req.risk_free_rate + bond.credit_spread / 10000) ** bond.years_to_maturity)
        bond_floor = coupon_pv + principal_pv
        
        moneyness = parity / bond_floor if bond_floor > 0 else 1
        d1 = (np.log(moneyness) + 0.5 * bond.implied_vol ** 2 * bond.years_to_maturity) / (bond.implied_vol * np.sqrt(bond.years_to_maturity)) if bond.years_to_maturity > 0 else 0
        
        from scipy.stats import norm
        delta = float(norm.cdf(d1))
        gamma = float(norm.pdf(d1) / (parity * bond.implied_vol * np.sqrt(bond.years_to_maturity))) if parity > 0 and bond.years_to_maturity > 0 else 0
        
        option_value = parity * delta - bond_floor * np.exp(-req.risk_free_rate * bond.years_to_maturity) * norm.cdf(d1 - bond.implied_vol * np.sqrt(bond.years_to_maturity))
        option_value = max(0, option_value)
        
        theoretical_price = bond_floor + option_value
        
        if bond.years_to_maturity > 0:
            price_diff = theoretical_price - bond.bond_price
            oas = bond.credit_spread + (price_diff / bond.years_to_maturity) * 100
        else:
            oas = bond.credit_spread
        
        oas_values.append(oas)
        
        analyses.append({
            "symbol": bond.symbol,
            "parity": parity,
            "bond_floor": bond_floor,
            "option_value": option_value,
            "oas": oas,
            "theoretical_price": theoretical_price,
            "mispricing": bond.bond_price - theoretical_price,
            "delta": delta,
            "gamma": gamma,
        })
    
    avg_oas = float(np.mean(oas_values)) if oas_values else 0
    std_oas = float(np.std(oas_values)) if len(oas_values) > 1 else 1
    
    if req.sector_avg_oas:
        comparison_oas = req.sector_avg_oas
    else:
        comparison_oas = avg_oas
    
    final_analyses = []
    for a in analyses:
        oas_zscore = (a["oas"] - comparison_oas) / std_oas if std_oas > 0 else 0
        
        if oas_zscore > 1.5 and a["mispricing"] < 0:
            signal = 1
        elif oas_zscore < -1.5 and a["mispricing"] > 0:
            signal = -1
        else:
            signal = 0
        
        final_analyses.append(OASAnalysis(
            symbol=a["symbol"],
            signal=signal,
            parity=float(a["parity"]),
            bond_floor=float(a["bond_floor"]),
            option_value=float(a["option_value"]),
            oas=float(a["oas"]),
            oas_zscore=float(oas_zscore),
            theoretical_price=float(a["theoretical_price"]),
            mispricing=float(a["mispricing"]),
            delta=float(a["delta"]),
            gamma=float(a["gamma"]),
        ))
    
    long_candidates = [a for a in final_analyses if a.signal == 1]
    short_candidates = [a for a in final_analyses if a.signal == -1]
    
    best_long = max(long_candidates, key=lambda a: a.oas_zscore).symbol if long_candidates else None
    best_short = min(short_candidates, key=lambda a: a.oas_zscore).symbol if short_candidates else None
    
    portfolio_signal = 1 if len(long_candidates) > len(short_candidates) else (-1 if len(short_candidates) > len(long_candidates) else 0)
    
    return OASArbitrageResponse(
        analyses=final_analyses,
        best_long=best_long,
        best_short=best_short,
        portfolio_signal=portfolio_signal,
        avg_oas=avg_oas,
    )
