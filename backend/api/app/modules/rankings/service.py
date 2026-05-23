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
        rows = await self.repository.get_dividend_ranking(reference_date, limit)
        effective_date = rows[0][0].reference_date if rows else reference_date
        return DividendRankingDTO(
            reference_date=effective_date,
            items=[
                DividendRankingItemDTO(
                    position=index,
                    ticker=score.ticker,
                    company_name=score.stock.company_name,
                    sector=score.stock.sector,
                    dividend_yield=metrics.dividend_yield,
                    payout_ratio=(
                        metrics.payload.get("payout_ratio")
                        or metrics.payload.get("payoutRatio")
                    ),
                    dividend_score=score.dividend_score,
                    final_score=score.final_score,
                    risk_score=score.risk_score,
                    recommendation=score.recommendation,
                )
                for index, (score, metrics) in enumerate(rows, start=1)
            ],
        )
