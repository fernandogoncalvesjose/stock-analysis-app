from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ScoreWeights:
    dividend_score: float = 0.30
    profitability_score: float = 0.25
    value_score: float = 0.20
    risk_score: float = 0.15
    growth_score: float = 0.10


DEFAULT_WEIGHTS = ScoreWeights()


def as_dict(weights: ScoreWeights | None = None) -> Dict[str, float]:
    w = weights or DEFAULT_WEIGHTS
    return {
        "dividend_score": w.dividend_score,
        "profitability_score": w.profitability_score,
        "value_score": w.value_score,
        "risk_score": w.risk_score,
        "growth_score": w.growth_score,
    }
