import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Awaitable, Callable, TypeVar

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from batch.app.repositories.financial_ingestion_repository import FinancialIngestionRepository
from core.providers.financial.base import FinancialDataProvider
from core.providers.financial.dtos import (
    DividendDTO,
    PriceHistoryBarDTO,
    PriceHistoryDTO,
    StockInfoDTO,
    StockMetricsDTO,
)
from core.providers.financial.models import (
    DividendEvent,
    OHLCVBar,
    ProviderRequestContext,
    StockInfo,
    StockMetrics,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class FinancialIngestionResult:
    ticker: str
    reference_date: date
    provider_name: str
    stock_updated: bool
    metrics_snapshot_created: bool
    prices_saved: int
    dividends_saved: int
    warnings: list[str]
    duration_ms: int


class FinancialIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        provider: FinancialDataProvider,
        retries: int = 3,
        timeout_seconds: int = 30,
    ) -> None:
        self.session = session
        self.provider = provider
        self.repository = FinancialIngestionRepository(session)
        self.retries = retries
        self.timeout_seconds = timeout_seconds

    async def ingest_ticker(
        self,
        ticker: str,
        reference_date: date | None = None,
        history_start_date: date | None = None,
        history_end_date: date | None = None,
    ) -> FinancialIngestionResult:
        started_at = perf_counter()
        normalized_ticker = ticker.upper().replace(".SA", "").strip()
        effective_reference_date = reference_date or datetime.now(UTC).date()
        effective_history_end = history_end_date or effective_reference_date
        effective_history_start = history_start_date or effective_history_end - timedelta(days=365)
        warnings: list[str] = []

        logger.info(
            "financial_ingestion_started",
            extra={
                "ticker": normalized_ticker,
                "provider": self.provider.name,
                "reference_date": str(effective_reference_date),
            },
        )

        try:
            stock_info = await self._fetch_and_validate_stock_info(normalized_ticker)
            stock_metrics = await self._fetch_and_validate_stock_metrics(normalized_ticker)
            prices = await self._fetch_and_validate_prices(
                normalized_ticker,
                effective_history_start,
                effective_history_end,
                warnings,
            )
            dividends = await self._fetch_and_validate_dividends(
                normalized_ticker,
                effective_history_start,
                effective_history_end,
                warnings,
            )

            async with self.session.begin():
                stock = await self.repository.upsert_stock(stock_info)
                await self.repository.upsert_metrics_snapshot(
                    stock_id=stock.id,
                    metrics=stock_metrics,
                    provider_name=self.provider.name,
                    reference_date=effective_reference_date,
                    payload=self._metrics_payload(stock_metrics),
                )
                prices_saved = await self.repository.upsert_price_history(
                    stock_id=stock.id,
                    ticker=normalized_ticker,
                    provider_name=self.provider.name,
                    prices=prices,
                )
                dividends_saved = await self.repository.upsert_dividends(
                    stock_id=stock.id,
                    ticker=normalized_ticker,
                    provider_name=self.provider.name,
                    dividends=dividends,
                )

            result = FinancialIngestionResult(
                ticker=normalized_ticker,
                reference_date=effective_reference_date,
                provider_name=self.provider.name,
                stock_updated=True,
                metrics_snapshot_created=True,
                prices_saved=prices_saved,
                dividends_saved=dividends_saved,
                warnings=warnings,
                duration_ms=round((perf_counter() - started_at) * 1000),
            )
            logger.info("financial_ingestion_completed", extra=asdict(result))
            return result
        except Exception:
            logger.exception(
                "financial_ingestion_failed",
                extra={
                    "ticker": normalized_ticker,
                    "provider": self.provider.name,
                    "reference_date": str(effective_reference_date),
                    "duration_ms": round((perf_counter() - started_at) * 1000),
                },
            )
            raise

    async def ingest_tickers(
        self,
        tickers: list[str],
        reference_date: date | None = None,
        history_start_date: date | None = None,
        history_end_date: date | None = None,
    ) -> tuple[list[FinancialIngestionResult], dict[str, str]]:
        results: list[FinancialIngestionResult] = []
        failures: dict[str, str] = {}

        for ticker in tickers:
            try:
                results.append(
                    await self.ingest_ticker(
                        ticker=ticker,
                        reference_date=reference_date,
                        history_start_date=history_start_date,
                        history_end_date=history_end_date,
                    )
                )
            except Exception as exc:
                failures[ticker] = str(exc)
                logger.error(
                    "financial_ingestion_ticker_failed",
                    extra={"ticker": ticker, "provider": self.provider.name, "error": str(exc)},
                )

        logger.info(
            "financial_ingestion_batch_completed",
            extra={
                "provider": self.provider.name,
                "tickers_requested": len(tickers),
                "tickers_succeeded": len(results),
                "tickers_failed": len(failures),
            },
        )
        return results, failures

    async def _fetch_and_validate_stock_info(self, ticker: str) -> StockInfo:
        response = await self._with_retries(
            lambda: self.provider.get_stock_info(
                ticker,
                self._request_context(),
            ),
            operation="get_stock_info",
            ticker=ticker,
        )
        dto = StockInfoDTO.model_validate(asdict(response.data))
        return StockInfo(
            ticker=dto.ticker,
            company_name=dto.company_name,
            exchange=dto.exchange,
            asset_class=dto.asset_class,
            currency=dto.currency,
            sector=dto.sector,
            industry=dto.industry,
            website=str(dto.website) if dto.website is not None else None,
            description=dto.description,
            market_cap=dto.market_cap,
            employees=dto.employees,
        )

    async def _fetch_and_validate_stock_metrics(self, ticker: str) -> StockMetrics:
        response = await self._with_retries(
            lambda: self.provider.get_stock_metrics(
                ticker,
                self._request_context(),
            ),
            operation="get_stock_metrics",
            ticker=ticker,
        )
        dto = StockMetricsDTO.model_validate(asdict(response.data))
        return StockMetrics(
            ticker=dto.ticker,
            reference_datetime=dto.reference_datetime,
            currency=dto.currency,
            market_cap=dto.market_cap,
            enterprise_value=dto.enterprise_value,
            trailing_pe=dto.trailing_pe,
            forward_pe=dto.forward_pe,
            price_to_book=dto.price_to_book,
            dividend_yield=dto.dividend_yield,
            payout_ratio=dto.payout_ratio,
            beta=dto.beta,
            return_on_equity=dto.return_on_equity,
            return_on_assets=dto.return_on_assets,
            debt_to_equity=dto.debt_to_equity,
            gross_margins=dto.gross_margins,
            operating_margins=dto.operating_margins,
            profit_margins=dto.profit_margins,
        )

    async def _fetch_and_validate_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        warnings: list[str],
    ) -> list[OHLCVBar]:
        try:
            response = await self._with_retries(
                lambda: self.provider.get_price_history(
                    ticker,
                    start_date,
                    end_date,
                    self._request_context(),
                ),
                operation="get_price_history",
                ticker=ticker,
            )
            dto = PriceHistoryDTO.model_validate(
                {
                    "ticker": ticker,
                    "items": [asdict(price) for price in response.data],
                }
            )
            return [
                OHLCVBar(
                    ticker=ticker,
                    date=item.date,
                    open_price=item.open_price,
                    high_price=item.high_price,
                    low_price=item.low_price,
                    close_price=item.close_price,
                    adjusted_close=item.adjusted_close,
                    volume=item.volume,
                )
                for item in dto.items
            ]
        except Exception as exc:
            warning = f"price_history_failed: {exc}"
            warnings.append(warning)
            logger.warning("financial_ingestion_price_history_skipped", extra={"ticker": ticker, "error": str(exc)})
            return []

    async def _fetch_and_validate_dividends(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        warnings: list[str],
    ) -> list[DividendEvent]:
        try:
            response = await self._with_retries(
                lambda: self.provider.get_dividends(
                    ticker,
                    start_date,
                    end_date,
                    self._request_context(),
                ),
                operation="get_dividends",
                ticker=ticker,
            )
            items = [DividendDTO.model_validate(asdict(dividend)) for dividend in response.data]
            return [
                DividendEvent(
                    ticker=item.ticker,
                    ex_date=item.ex_date,
                    payment_date=item.payment_date,
                    amount=item.amount,
                    currency=item.currency,
                )
                for item in items
            ]
        except Exception as exc:
            warning = f"dividends_failed: {exc}"
            warnings.append(warning)
            logger.warning("financial_ingestion_dividends_skipped", extra={"ticker": ticker, "error": str(exc)})
            return []

    async def _with_retries(
        self,
        operation_fn: Callable[[], Awaitable[T]],
        operation: str,
        ticker: str,
    ) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                return await operation_fn()
            except (ValidationError, ValueError):
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "financial_ingestion_provider_call_failed",
                    extra={
                        "ticker": ticker,
                        "provider": self.provider.name,
                        "operation": operation,
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )
                if attempt < self.retries:
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))
        raise RuntimeError(f"{operation} failed for {ticker}: {last_error}")

    def _request_context(self) -> ProviderRequestContext:
        return ProviderRequestContext(
            timeout_seconds=self.timeout_seconds,
            retries=self.retries,
        )

    def _metrics_payload(self, metrics: StockMetrics) -> dict[str, str | None]:
        payload = asdict(metrics)
        return {
            key: self._serialize_payload_value(value)
            for key, value in payload.items()
            if key not in {"ticker", "reference_datetime", "currency"}
        }

    def _serialize_payload_value(self, value) -> str | None:
        if isinstance(value, Decimal):
            return str(value)
        if value is None:
            return None
        return str(value)
