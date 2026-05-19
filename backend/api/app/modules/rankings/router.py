from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.rankings.dependencies import get_ranking_service
from app.modules.rankings.dtos import DividendRankingDTO
from app.modules.rankings.service import RankingService

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/dividends", response_model=DividendRankingDTO)
async def get_dividend_ranking(
    service: Annotated[RankingService, Depends(get_ranking_service)],
    date_: Annotated[date | None, Query(alias="date")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DividendRankingDTO:
    return await service.get_dividend_ranking(date_, limit)
