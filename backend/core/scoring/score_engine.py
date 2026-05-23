from __future__ import annotations

import logging
from typing import Dict

from .score_dto import ScoreInput, ScoreResult, ScoreBreakdown
from .score_rules import (
    dividend_score,
    value_score,
    growth_score,
    profitability_score,
    risk_score,
)
from .score_weights import as_dict

logger = logging.getLogger(__name__)


def _weighted_final(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    # ignore missing scores and rescale weights
    available = {k: v for k, v in scores.items() if v is not None}
    if not available:
        return 0.0
    total_weight = sum(weights[k] for k in available.keys() if k in weights)
    if total_weight <= 0:
        # fallback to equal weights
        total_weight = len(available)
        weights = {k: 1.0 / total_weight for k in available}

    result = 0.0
    for k, v in available.items():
        w = weights.get(k, 0.0) / total_weight
        result += v * w
    return result


def recommend(final_score: float, thresholds: Dict[str, float] | None = None) -> str:
    t = thresholds or {"buy": 75.0, "hold": 50.0}
    if final_score >= t["buy"]:
        return "BUY"
    if final_score >= t["hold"]:
        return "HOLD"
    return "SELL"


def score(input: ScoreInput, weights_override: Dict[str, float] | None = None) -> ScoreResult:
    w = as_dict()
    if weights_override:
        w.update(weights_override)

    ds = dividend_score(input.dividend_yield, input.payout_ratio, input.dividend_consistency)
    vs = value_score(input.pe, input.pb, input.ev_ebitda)
    gs = growth_score(input.revenue_growth, input.profit_growth)
    ps = profitability_score(input.roe, input.roic, input.net_margin, input.gross_margin)
    rs = risk_score(input.debt_to_equity, input.current_ratio, input.volatility)

    scores = {
        "dividend_score": ds,
        "value_score": vs,
        "growth_score": gs,
        "profitability_score": ps,
        "risk_score": rs,
    }

    final = _weighted_final(scores, w)

    breakdown = ScoreBreakdown(
        dividend_score=ds,
        value_score=vs,
        growth_score=gs,
        profitability_score=ps,
        risk_score=rs,
    )

    rec = recommend(final)
    logger.info("scored ticker: final=%.2f rec=%s", final, rec)
    return ScoreResult(breakdown=breakdown, final_score=float(round(final, 2)), recommendation=rec)


if __name__ == "__main__":
    # Quick example
    import logging
    logging.basicConfig(level=logging.INFO)

    example = ScoreInput(
        dividend_yield=8.43,  # percent -> normalized inside DTO
        payout_ratio=0.45,
        dividend_consistency=0.9,
        pe=12.5,
        pb=1.8,
        ev_ebitda=7.2,
        revenue_growth=0.18,
        profit_growth=0.22,
        roe=0.18,
        roic=0.12,
        net_margin=0.12,
        gross_margin=0.42,
        debt_to_equity=0.9,
        current_ratio=1.4,
        volatility=0.25,
    )

    result = score(example)
    print(result.json(indent=2))
