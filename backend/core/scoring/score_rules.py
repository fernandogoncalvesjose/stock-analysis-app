from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def _to_float(value: Optional[Decimal]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _scale_linear(value: float, src_min: float, src_max: float) -> float:
    if src_min >= src_max:
        return 0.0
    v = (value - src_min) / (src_max - src_min)
    return _clamp(v * 100.0, 0.0, 100.0)


def _scale_inverse(value: float, good_max: float, bad_max: float) -> float:
    # lower values are better; map 0..good_max -> 100..(>=bad_max -> 0)
    if value <= 0:
        return 100.0
    if value <= good_max:
        return _scale_linear(good_max - value, 0, good_max)
    if value >= bad_max:
        return 0.0
    # linear from good_max..bad_max
    return _scale_linear(bad_max - value, 0, bad_max - good_max)


def dividend_score(dividend_yield: Optional[Decimal], payout_ratio: Optional[Decimal], consistency: Optional[Decimal]) -> float:
    dy = _to_float(dividend_yield)
    pr = _to_float(payout_ratio)
    cons = _to_float(consistency)

    # dividend yield: 0%->0, 8%->100, cap at 15%
    dy_score = 0.0
    if dy is not None:
        # normalize percent-like values >1
        if dy > 1.0 and dy <= 100.0:
            dy = dy / 100.0
        dy_score = _scale_linear(dy, 0.0, 0.08) if dy is not None else 0.0

    # payout ratio: lower is better (0..0.6 ideal)
    pr_score = 50.0
    if pr is not None:
        if pr <= 0:
            pr_score = 100.0
        else:
            pr_score = _scale_inverse(pr, 0.6, 1.5)

    cons_score = 50.0
    if cons is not None:
        cons_score = _clamp(cons * 100.0, 0.0, 100.0)

    # weights inside dividend score
    final = 0.6 * dy_score + 0.3 * pr_score + 0.1 * cons_score
    logger.debug("dividend_score: dy=%s pr=%s cons=%s -> %s", dy, pr, cons, final)
    return float(_clamp(final, 0.0, 100.0))


def value_score(pe: Optional[Decimal], pb: Optional[Decimal], ev_ebitda: Optional[Decimal]) -> float:
    pe_f = _to_float(pe)
    pb_f = _to_float(pb)
    ev_f = _to_float(ev_ebitda)

    # P/E: lower better; treat <=0 as neutral (50)
    if pe_f is None:
        pe_score = 50.0
    elif pe_f <= 0:
        pe_score = 50.0
    else:
        pe_score = _scale_inverse(pe_f, 8.0, 30.0)

    # P/B: lower better
    if pb_f is None:
        pb_score = 50.0
    else:
        pb_score = _scale_inverse(pb_f, 1.0, 5.0)

    # EV/EBITDA: lower better
    if ev_f is None:
        ev_score = 50.0
    else:
        ev_score = _scale_inverse(ev_f, 6.0, 20.0)

    final = 0.4 * pe_score + 0.3 * pb_score + 0.3 * ev_score
    logger.debug("value_score: pe=%s pb=%s ev=%s -> %s", pe_f, pb_f, ev_f, final)
    return float(_clamp(final, 0.0, 100.0))


def growth_score(revenue_growth: Optional[Decimal], profit_growth: Optional[Decimal]) -> float:
    rg = _to_float(revenue_growth)
    pg = _to_float(profit_growth)
    # treat percent-like
    def norm_pct(x: Optional[float]) -> Optional[float]:
        if x is None:
            return None
        if x > 1.0 and x <= 1000.0:
            return x / 100.0
        return x

    rg = norm_pct(rg)
    pg = norm_pct(pg)

    rg_score = _scale_linear(rg, 0.0, 0.25) if rg is not None else 50.0
    pg_score = _scale_linear(pg, 0.0, 0.25) if pg is not None else 50.0

    final = 0.6 * rg_score + 0.4 * pg_score
    logger.debug("growth_score: rg=%s pg=%s -> %s", rg, pg, final)
    return float(_clamp(final, 0.0, 100.0))


def profitability_score(roe: Optional[Decimal], roic: Optional[Decimal], net_margin: Optional[Decimal], gross_margin: Optional[Decimal]) -> float:
    roe_f = _to_float(roe)
    roic_f = _to_float(roic)
    nm_f = _to_float(net_margin)
    gm_f = _to_float(gross_margin)

    def nm(x: Optional[float]) -> Optional[float]:
        if x is None:
            return None
        if x > 1.0 and x <= 1000.0:
            return x / 100.0
        return x

    roe_f = nm(roe_f)
    roic_f = nm(roic_f)
    nm_f = nm(nm_f)
    gm_f = nm(gm_f)

    roe_score = _scale_linear(roe_f, 0.0, 0.30) if roe_f is not None else 50.0
    roic_score = _scale_linear(roic_f, 0.0, 0.20) if roic_f is not None else 50.0
    net_score = _scale_linear(nm_f, 0.0, 0.20) if nm_f is not None else 50.0
    gross_score = _scale_linear(gm_f, 0.0, 0.50) if gm_f is not None else 50.0

    final = 0.35 * roe_score + 0.25 * roic_score + 0.2 * net_score + 0.2 * gross_score
    logger.debug("profitability_score: roe=%s roic=%s nm=%s gm=%s -> %s", roe_f, roic_f, nm_f, gm_f, final)
    return float(_clamp(final, 0.0, 100.0))


def risk_score(debt_to_equity: Optional[Decimal], current_ratio: Optional[Decimal], volatility: Optional[Decimal]) -> float:
    dte = _to_float(debt_to_equity)
    cr = _to_float(current_ratio)
    vol = _to_float(volatility)

    # debt_to_equity: lower better, ideal 0..0.8, bad >=3
    if dte is None:
        dte_score = 50.0
    else:
        dte_score = _scale_inverse(dte, 0.8, 3.0)

    # current_ratio: higher generally better up to ~3
    if cr is None:
        cr_score = 50.0
    else:
        cr_score = _scale_linear(cr, 0.5, 3.0)

    # volatility: higher worse; assume volatility in fraction (0..1)
    if vol is None:
        vol_score = 50.0
    else:
        vol_score = _scale_inverse(vol, 0.1, 0.6)

    final = 0.5 * dte_score + 0.3 * cr_score + 0.2 * vol_score
    logger.debug("risk_score: dte=%s cr=%s vol=%s -> %s", dte, cr, vol, final)
    return float(_clamp(final, 0.0, 100.0))
