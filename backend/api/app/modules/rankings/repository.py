from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.stocks.models import Stock, StockAnalysisSnapshot


class RankingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_dividend_ranking(
        self,
        reference_date: date | None,
        limit: int,
    ) -> list[StockAnalysisSnapshot]:
        if reference_date is None:
            latest_date = await self.session.scalar(
                select(StockAnalysisSnapshot.reference_date)
                .order_by(StockAnalysisSnapshot.reference_date.desc())
                .limit(1)
            )
            reference_date = latest_date

        if reference_date is None:
            return []

        stmt = (
            select(StockAnalysisSnapshot)
            .options(selectinload(StockAnalysisSnapshot.stock))
            .join(Stock)
            .where(
                Stock.is_active.is_(True),
                StockAnalysisSnapshot.reference_date == reference_date,
            )
            .order_by(
                StockAnalysisSnapshot.dividend_yield.desc().nullslast(),
                StockAnalysisSnapshot.composite_score.desc(),
            )
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
