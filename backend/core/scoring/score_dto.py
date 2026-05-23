from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ScoreInput(BaseModel):
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    # Dividend / payout
    dividend_yield: Optional[Decimal] = None  # fraction (0.05) or percent (5 or 5.0)
    payout_ratio: Optional[Decimal] = None
    dividend_consistency: Optional[Decimal] = None  # 0..1

    # Value
    pe: Optional[Decimal] = None
    pb: Optional[Decimal] = None
    ev_ebitda: Optional[Decimal] = None

    # Growth (decimal fraction or percent)
    revenue_growth: Optional[Decimal] = None
    profit_growth: Optional[Decimal] = None

    # Profitability (fractions)
    roe: Optional[Decimal] = None
    roic: Optional[Decimal] = None
    net_margin: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None

    # Risk/capital structure
    debt_to_equity: Optional[Decimal] = None
    current_ratio: Optional[Decimal] = None
    volatility: Optional[Decimal] = None  # optional risk metric

    @field_validator(
        "dividend_yield",
        "payout_ratio",
        "dividend_consistency",
        "revenue_growth",
        "profit_growth",
        "roe",
        "roic",
        "net_margin",
        "gross_margin",
        "debt_to_equity",
        "current_ratio",
        "volatility",
        mode="before",
    )
    @classmethod
    def _coerce_decimal_like(cls, v):
        if v is None:
            return None
        try:
            # allow Decimal, int, float, str
            return Decimal(str(v))
        except Exception:
            return None

    @field_validator("dividend_yield", mode="after")
    @classmethod
    def _normalize_dividend_yield(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is None:
            return None
        # if returned as percent like 8.43 -> convert to 0.0843
        if v > Decimal("1") and v <= Decimal("100"):
            return (v / Decimal("100")).quantize(Decimal("0.0000001"))
        return v


class ScoreBreakdown(BaseModel):
    dividend_score: float
    value_score: float
    growth_score: float
    profitability_score: float
    risk_score: float


class ScoreResult(BaseModel):
    breakdown: ScoreBreakdown
    final_score: float
    recommendation: str
