from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.stocks.models import Stock, StockAnalysisSnapshot


class StockRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_by_ticker(self, ticker: str) -> Stock | None:
        stmt = select(Stock).where(Stock.ticker == ticker.upper(), Stock.is_active.is_(True))
        return await self.session.scalar(stmt)

    async def get_latest_snapshot(self, ticker: str) -> StockAnalysisSnapshot | None:
        stmt = (
            select(StockAnalysisSnapshot)
            .options(selectinload(StockAnalysisSnapshot.stock))
            .join(Stock)
            .where(StockAnalysisSnapshot.ticker == ticker.upper(), Stock.is_active.is_(True))
            .order_by(StockAnalysisSnapshot.reference_date.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def search(self, query: str, limit: int = 20) -> list[Stock]:
        normalized = f"%{query.strip().upper()}%"
        stmt: Select[tuple[Stock]] = (
            select(Stock)
            .where(
                Stock.is_active.is_(True),
                (func.upper(Stock.ticker).like(normalized))
                | (func.upper(Stock.company_name).like(normalized)),
            )
            .order_by(Stock.ticker.asc())
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())
