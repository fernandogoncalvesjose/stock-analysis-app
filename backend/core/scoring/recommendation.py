from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Recommendation(StrEnum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


@dataclass(frozen=True)
class ScoreInput:
    composite_score: Decimal
    risk_flags: tuple[str, ...] = ()


class RecommendationEngine:
    def decide(self, score_input: ScoreInput) -> Recommendation:
        score = score_input.composite_score
        if "ACCOUNTING_RISK" in score_input.risk_flags:
            return Recommendation.SELL
        if score >= Decimal("70"):
            return Recommendation.BUY
        if score >= Decimal("45"):
            return Recommendation.HOLD
        return Recommendation.SELL
