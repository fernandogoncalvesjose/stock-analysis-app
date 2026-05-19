from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.rankings.repository import RankingRepository
from app.modules.rankings.service import RankingService


def get_ranking_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RankingRepository:
    return RankingRepository(session)


def get_ranking_service(
    repository: Annotated[RankingRepository, Depends(get_ranking_repository)],
) -> RankingService:
    return RankingService(repository)
