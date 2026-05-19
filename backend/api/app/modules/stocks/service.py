from app.modules.stocks.dtos import (
    ScoreBreakdownDTO,
    StockDTO,
    StockSearchResultDTO,
    StockSnapshotDTO,
)
from app.modules.stocks.repository import StockRepository
from app.shared.errors import NotFoundError


class StockService:
    def __init__(self, repository: StockRepository) -> None:
        self.repository = repository

    async def get_stock(self, ticker: str) -> StockDTO:
        stock = await self.repository.get_active_by_ticker(ticker)
        if stock is None:
            raise NotFoundError("Stock", ticker.upper())
        return StockDTO.model_validate(stock)

    async def get_latest_snapshot(self, ticker: str) -> StockSnapshotDTO:
        snapshot = await self.repository.get_latest_snapshot(ticker)
        if snapshot is None:
            raise NotFoundError("Stock snapshot", ticker.upper())

        payload = snapshot.payload or {}
        stock = snapshot.stock
        return StockSnapshotDTO(
            ticker=snapshot.ticker,
            company_name=stock.company_name,
            sector=stock.sector,
            reference_date=snapshot.reference_date,
            recommendation=snapshot.recommendation,
            composite_score=snapshot.composite_score,
            dividend_yield=snapshot.dividend_yield,
            score_breakdown=ScoreBreakdownDTO.model_validate(
                payload.get("score_breakdown", {})
            ),
            ai_summary=payload.get("ai_summary"),
            risk_flags=payload.get("risk_flags", []),
            updated_at=snapshot.updated_at,
        )

    async def search(self, query: str, limit: int) -> list[StockSearchResultDTO]:
        if len(query.strip()) < 2:
            return []
        stocks = await self.repository.search(query, limit)
        return [
            StockSearchResultDTO(
                ticker=stock.ticker,
                company_name=stock.company_name,
                sector=stock.sector,
            )
            for stock in stocks
        ]
