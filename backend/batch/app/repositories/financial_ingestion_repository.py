from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.stocks.models import Stock, StockDividend, StockMetricsSnapshot, StockPriceDaily
from core.providers.financial.models import DividendEvent, OHLCVBar, StockInfo, StockMetrics


class FinancialIngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_stock(self, stock_info: StockInfo) -> Stock:
        stmt = (
            insert(Stock)
            .values(
                id=uuid4(),
                ticker=stock_info.ticker,
                company_name=stock_info.company_name,
                sector=stock_info.sector,
                exchange=stock_info.exchange.value,
                is_active=True,
            )
            .on_conflict_do_update(
                index_elements=[Stock.ticker],
                set_={
                    "company_name": stock_info.company_name,
                    "sector": stock_info.sector,
                    "exchange": stock_info.exchange.value,
                    "is_active": True,
                },
            )
            .returning(Stock)
        )
        return (await self.session.scalars(stmt)).one()

    async def get_stock_by_ticker(self, ticker: str) -> Stock | None:
        return await self.session.scalar(select(Stock).where(Stock.ticker == ticker))

    async def upsert_metrics_snapshot(
        self,
        stock_id: UUID,
        metrics: StockMetrics,
        provider_name: str,
        reference_date: date,
        payload: dict[str, Any],
    ) -> None:
        stmt = (
            insert(StockMetricsSnapshot)
            .values(
                id=uuid4(),
                stock_id=stock_id,
                ticker=metrics.ticker,
                reference_date=reference_date,
                provider_name=provider_name,
                market_cap=metrics.market_cap,
                dividend_yield=metrics.dividend_yield,
                trailing_pe=metrics.trailing_pe,
                price_to_book=metrics.price_to_book,
                payload=payload,
            )
            .on_conflict_do_update(
                constraint="uq_stock_metrics_ticker_reference_date",
                set_={
                    "provider_name": provider_name,
                    "market_cap": metrics.market_cap,
                    "dividend_yield": metrics.dividend_yield,
                    "trailing_pe": metrics.trailing_pe,
                    "price_to_book": metrics.price_to_book,
                    "payload": payload,
                },
            )
        )
        await self.session.execute(stmt)

    async def upsert_price_history(
        self,
        stock_id: UUID,
        ticker: str,
        provider_name: str,
        prices: list[OHLCVBar],
    ) -> int:
        if not prices:
            return 0

        rows = [
            {
                "id": uuid4(),
                "stock_id": stock_id,
                "ticker": ticker,
                "price_date": price.date,
                "provider_name": provider_name,
                "open_price": price.open_price,
                "high_price": price.high_price,
                "low_price": price.low_price,
                "close_price": price.close_price,
                "adjusted_close": price.adjusted_close,
                "volume": price.volume,
            }
            for price in prices
        ]
        insert_stmt = insert(StockPriceDaily).values(rows)
        stmt = insert_stmt.on_conflict_do_update(
            constraint="uq_stock_price_ticker_price_date",
            set_={
                "provider_name": provider_name,
                "open_price": insert_stmt.excluded.open_price,
                "high_price": insert_stmt.excluded.high_price,
                "low_price": insert_stmt.excluded.low_price,
                "close_price": insert_stmt.excluded.close_price,
                "adjusted_close": insert_stmt.excluded.adjusted_close,
                "volume": insert_stmt.excluded.volume,
            },
        )
        await self.session.execute(stmt)
        return len(rows)

    async def upsert_dividends(
        self,
        stock_id: UUID,
        ticker: str,
        provider_name: str,
        dividends: list[DividendEvent],
    ) -> int:
        if not dividends:
            return 0

        rows = [
            {
                "id": uuid4(),
                "stock_id": stock_id,
                "ticker": ticker,
                "ex_date": dividend.ex_date,
                "payment_date": dividend.payment_date,
                "provider_name": provider_name,
                "amount": dividend.amount,
                "currency": dividend.currency.value,
            }
            for dividend in dividends
        ]
        insert_stmt = insert(StockDividend).values(rows)
        stmt = insert_stmt.on_conflict_do_update(
            constraint="uq_stock_dividend_ticker_ex_date_amount",
            set_={
                "payment_date": insert_stmt.excluded.payment_date,
                "provider_name": provider_name,
                "currency": insert_stmt.excluded.currency,
            },
        )
        await self.session.execute(stmt)
        return len(rows)
