from datetime import date

from app.modules.rankings.dtos import DividendRankingDTO, DividendRankingItemDTO
from app.modules.rankings.repository import RankingRepository


class RankingService:
    def __init__(self, repository: RankingRepository) -> None:
        self.repository = repository

    async def get_dividend_ranking(
        self,
        reference_date: date | None,
        limit: int,
    ) -> DividendRankingDTO:
        snapshots = await self.repository.get_dividend_ranking(reference_date, limit)
        effective_date = snapshots[0].reference_date if snapshots else reference_date
        return DividendRankingDTO(
            reference_date=effective_date,
            items=[
                DividendRankingItemDTO(
                    position=index,
                    ticker=snapshot.ticker,
                    company_name=snapshot.stock.company_name,
                    sector=snapshot.stock.sector,
                    dividend_yield=snapshot.dividend_yield,
                    composite_score=snapshot.composite_score,
                    recommendation=snapshot.recommendation,
                )
                for index, snapshot in enumerate(snapshots, start=1)
            ],
        )
