from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.stocks.dependencies import get_stock_service, get_score_service, get_stock_repository
from app.modules.stocks.dtos import (
    StockDTO,
    StockSearchResultDTO,
    StockSnapshotDTO,
    StockScoreDTO,
    RecalculateResponseDTO,
)
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


@router.post("/{ticker}/scores/recalculate", response_model=RecalculateResponseDTO)
async def recalculate_score(
    ticker: str,
    score_service: Annotated[object, Depends(get_score_service)],
) -> RecalculateResponseDTO:
    """Recalcula o score para o `ticker` usando o motor de scoring e persiste em `stock_scores`.

    - busca as últimas métricas
    - calcula os scores e recommendation
    - persiste com idempotência (upsert por stock_id+reference_date)
    """
    res = await score_service.compute_and_persist(ticker)
    if not res.get("ok"):
        # mapear erros para HTTP
        reason = res.get("reason") or "error"
        if reason == "no_metrics_found":
            raise HTTPException(status_code=404, detail="Métricas não encontradas para o ticker")
        if reason == "stock_not_found":
            raise HTTPException(status_code=404, detail="Ação não encontrada")
        raise HTTPException(status_code=500, detail=res.get("error") or "Falha ao calcular score")

    # transformar result em DTO
    data = res.get("result")
    dto = StockScoreDTO(**data)
    return RecalculateResponseDTO(ok=True, result=dto)


@router.get("/{ticker}/scores/latest", response_model=StockScoreDTO)
async def get_latest_score(
    ticker: str,
    session: Annotated[AsyncSession, Depends(lambda: None)],
) -> StockScoreDTO:
    """Retorna o último score calculado para o ticker."""
    # lazy import to avoid circular
    from app.db.session import AsyncSessionFactory
    from app.modules.stocks.models import StockScore

    async with AsyncSessionFactory() as session:
        subq = select(func.max(StockScore.reference_date)).where(StockScore.ticker == ticker).scalar_subquery()
        stmt = select(StockScore).where(StockScore.ticker == ticker, StockScore.reference_date == subq).limit(1)
        row = await session.scalar(stmt)
        if not row:
            raise HTTPException(status_code=404, detail="Score não encontrado para o ticker")
        return StockScoreDTO(
            ticker=row.ticker,
            reference_date=row.reference_date,
            dividend_score=row.dividend_score,
            value_score=row.value_score,
            growth_score=row.growth_score,
            profitability_score=row.profitability_score,
            risk_score=row.risk_score,
            final_score=row.final_score,
            recommendation=row.recommendation,
            payload=row.payload,
        )


@router.get("/top-dividends", response_model=list[StockScoreDTO])
async def top_dividends(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    """Retorna as ações com maior `dividend_score` no último `reference_date` disponível por ticker."""
    from app.db.session import AsyncSessionFactory
    from app.modules.stocks.models import StockScore

    async with AsyncSessionFactory() as session:
        # subquery: latest date per ticker
        latest = (
            select(StockScore.ticker, func.max(StockScore.reference_date).label("md"))
            .group_by(StockScore.ticker)
            .subquery()
        )
        stmt = (
            select(StockScore)
            .join(latest, (StockScore.ticker == latest.c.ticker) & (StockScore.reference_date == latest.c.md))
            .order_by(StockScore.dividend_score.desc().nullslast())
            .limit(limit)
        )
        rows = (await session.scalars(stmt)).all()
        return [
            StockScoreDTO(
                ticker=r.ticker,
                reference_date=r.reference_date,
                dividend_score=r.dividend_score,
                value_score=r.value_score,
                growth_score=r.growth_score,
                profitability_score=r.profitability_score,
                risk_score=r.risk_score,
                final_score=r.final_score,
                recommendation=r.recommendation,
                payload=r.payload,
            )
            for r in rows
        ]
