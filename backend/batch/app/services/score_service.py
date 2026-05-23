from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.stocks.models import (
    StockMetricsSnapshot,
    Stock,
    StockScore,
)
from core.scoring.score_dto import ScoreInput
from core.scoring.score_engine import score as score_engine

logger = logging.getLogger(__name__)


class ScoreService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_latest_metrics(self, ticker: str) -> StockMetricsSnapshot | None:
        stmt = (
            select(StockMetricsSnapshot)
            .where(StockMetricsSnapshot.ticker == ticker)
            .order_by(StockMetricsSnapshot.reference_date.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def compute_and_persist(self, ticker: str, reference_date: date | None = None) -> dict[str, Any]:
        log_ctx = {"ticker": ticker}
        try:
            metrics = await self._get_latest_metrics(ticker)
            if metrics is None:
                logger.warning("score_no_metrics", extra=log_ctx)
                return {"ok": False, "reason": "no_metrics_found"}

            ref_date = reference_date or metrics.reference_date

            # Build ScoreInput from snapshot + payload
            payload = metrics.payload or {}
            inp = ScoreInput(
                dividend_yield=metrics.dividend_yield,
                payout_ratio=payload.get("payout_ratio") or payload.get("payoutRatio"),
                dividend_consistency=payload.get("dividend_consistency"),
                pe=metrics.trailing_pe,
                pb=metrics.price_to_book,
                ev_ebitda=payload.get("ev_ebitda") or payload.get("evEbitda"),
                revenue_growth=payload.get("revenue_growth"),
                profit_growth=payload.get("profit_growth"),
                roe=payload.get("roe"),
                roic=payload.get("roic"),
                net_margin=payload.get("net_margin"),
                gross_margin=payload.get("gross_margin"),
                debt_to_equity=payload.get("debt_to_equity"),
                current_ratio=payload.get("current_ratio"),
                volatility=payload.get("volatility"),
            )

            result = score_engine(inp)

            # persist idempotent upsert
            async with self.session.begin():
                # ensure stock exists
                stock_stmt = select(Stock).where(Stock.ticker == ticker)
                stock = await self.session.scalar(stock_stmt)
                if stock is None:
                    logger.warning("score_stock_not_found", extra={**log_ctx, "reference_date": str(ref_date)})
                    return {"ok": False, "reason": "stock_not_found"}

                rows = {
                    "stock_id": stock.id,
                    "ticker": ticker,
                    "reference_date": ref_date,
                    "dividend_score": Decimal(str(result.breakdown.dividend_score)),
                    "value_score": Decimal(str(result.breakdown.value_score)),
                    "growth_score": Decimal(str(result.breakdown.growth_score)),
                    "profitability_score": Decimal(str(result.breakdown.profitability_score)),
                    "risk_score": Decimal(str(result.breakdown.risk_score)),
                    "final_score": Decimal(str(result.final_score)),
                    "recommendation": result.recommendation,
                    "payload": {"breakdown": result.breakdown.model_dump(), "input": inp.model_dump()},
                }

                insert_stmt = insert(StockScore).values(rows)
                stmt = insert_stmt.on_conflict_do_update(
                    constraint="uq_stock_score_stock_reference",
                    set_={
                        "dividend_score": insert_stmt.excluded.dividend_score,
                        "value_score": insert_stmt.excluded.value_score,
                        "growth_score": insert_stmt.excluded.growth_score,
                        "profitability_score": insert_stmt.excluded.profitability_score,
                        "risk_score": insert_stmt.excluded.risk_score,
                        "final_score": insert_stmt.excluded.final_score,
                        "recommendation": insert_stmt.excluded.recommendation,
                        "payload": insert_stmt.excluded.payload,
                    },
                )
                await self.session.execute(stmt)

            logger.info("score_persisted", extra={**log_ctx, "final": result.final_score, "rec": result.recommendation})
            return {"ok": True, "result": result.model_dump()}
        except Exception as exc:
            logger.exception("score_failed", extra={**log_ctx, "error": str(exc)})
            return {"ok": False, "reason": "exception", "error": str(exc)}
