from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.stocks.dependencies import get_stock_service
from app.modules.stocks.dtos import StockDTO, StockSearchResultDTO, StockSnapshotDTO
from app.modules.stocks.service import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=list[StockSearchResultDTO])
async def search_stocks(
    service: Annotated[StockService, Depends(get_stock_service)],
    q: Annotated[str, Query(min_length=2, max_length=80)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[StockSearchResultDTO]:
    return await service.search(q, limit)


@router.get("/{ticker}", response_model=StockSnapshotDTO)
async def get_latest_snapshot(
    ticker: str,
    service: Annotated[StockService, Depends(get_stock_service)],
) -> StockSnapshotDTO:
    return await service.get_latest_snapshot(ticker)


@router.get("/{ticker}/profile", response_model=StockDTO)
async def get_stock(
    ticker: str,
    service: Annotated[StockService, Depends(get_stock_service)],
) -> StockDTO:
    return await service.get_stock(ticker)
