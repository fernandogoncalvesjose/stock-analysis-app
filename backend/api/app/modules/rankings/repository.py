from datetime import date

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.stocks.models import Stock, StockMetricsSnapshot, StockScore


class RankingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_latest_score_date(self) -> date | None:
        return await self.session.scalar(
            select(StockScore.reference_date).order_by(StockScore.reference_date.desc()).limit(1)
        )

    async def get_dividend_ranking(
        self,
        reference_date: date | None,
        limit: int,
    ) -> list[tuple[StockScore, StockMetricsSnapshot]]:
        if reference_date is None:
            reference_date = await self._get_latest_score_date()

        if reference_date is None:
            return []

        payout_ratio = func.coalesce(
            StockMetricsSnapshot.payload["payout_ratio"].astext.cast(Float),
            StockMetricsSnapshot.payload["payoutRatio"].astext.cast(Float),
        )

        stmt = (
            select(StockScore, StockMetricsSnapshot)
            .options(selectinload(StockScore.stock))
            .join(Stock)
            .join(
                StockMetricsSnapshot,
                (StockMetricsSnapshot.ticker == StockScore.ticker)
                & (StockMetricsSnapshot.reference_date == StockScore.reference_date),
            )
            .where(
                Stock.is_active.is_(True),
                StockScore.reference_date == reference_date,
                StockMetricsSnapshot.dividend_yield > 4,
                payout_ratio < 0.9,
                StockScore.final_score >= 50,
            )
            .order_by(
                StockScore.dividend_score.desc().nullslast(),
                StockScore.final_score.desc().nullslast(),
                StockScore.risk_score.desc().nullslast(),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(score, metrics) for score, metrics in result.all()]
