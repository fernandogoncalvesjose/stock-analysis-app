from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.stocks.repository import StockRepository
from app.modules.stocks.service import StockService


def get_stock_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StockRepository:
    return StockRepository(session)


def get_stock_service(
    repository: Annotated[StockRepository, Depends(get_stock_repository)],
) -> StockService:
    return StockService(repository)
