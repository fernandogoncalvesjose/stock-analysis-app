import asyncio
import hashlib
import logging
import math
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from time import perf_counter
from typing import Any, TypeVar

import yfinance as yf

from core.providers.financial.base import FinancialDataProvider
from core.providers.financial.enums import (
    AssetClass,
    Currency,
    Exchange,
    ProviderCapability,
    ProviderStatus,
    StatementPeriodType,
)
from core.providers.financial.errors import ProviderPayloadError, ProviderUnavailableError
from core.providers.financial.models import (
    BalanceSheetSnapshot,
    CashFlowSnapshot,
    CompanyProfile,
    DividendEvent,
    FinancialProviderHealth,
    FinancialStatementBundle,
    FinancialStatementPeriod,
    IncomeStatementSnapshot,
    MarketQuote,
    OHLCVBar,
    ProviderMetadata,
    ProviderRequestContext,
    ProviderResponse,
    StockInfo,
    StockMetrics,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


class YahooFinanceProvider(FinancialDataProvider):
    metadata = ProviderMetadata(
        name="yahoo_finance",
        display_name="Yahoo Finance",
        capabilities=frozenset(
            {
                ProviderCapability.COMPANY_PROFILE,
                ProviderCapability.MARKET_QUOTES,
                ProviderCapability.OHLCV_HISTORY,
                ProviderCapability.DIVIDENDS,
                ProviderCapability.FINANCIAL_STATEMENTS,
            }
        ),
    )

    _METRIC_FIELD_ALIASES = {
        "market_cap": ["marketCap", "market_cap", "market_capitalization"],
        "enterprise_value": ["enterpriseValue", "enterprise_value", "enterpriseVal"],
        "trailing_pe": ["trailingPE", "trailing_pe", "trailingPERatio"],
        "forward_pe": ["forwardPE", "forward_pe", "forwardPERatio"],
        "price_to_book": ["priceToBook", "price_to_book", "pbRatio"],
        "dividend_yield": ["dividendYield", "dividend_yield", "dividendYieldPercent"],
        "payout_ratio": ["payoutRatio", "payout_ratio"],
        "beta": ["beta"],
        "return_on_equity": ["returnOnEquity", "returnOnEquityMRQ"],
        "return_on_assets": ["returnOnAssets", "returnOnAssetsMRQ"],
        "debt_to_equity": ["debtToEquity", "debtToEquityMRQ"],
        "gross_margins": ["grossMargins", "gross_profit_margin"],
        "operating_margins": ["operatingMargins", "operating_margin"],
        "profit_margins": ["profitMargins", "profit_margin"],
    }

    _STATEMENT_ROW_ALIASES = {
        "total_revenue": ["Total Revenue", "Revenue", "Total Revenue Net", "Net Revenue"],
        "gross_profit": ["Gross Profit", "Gross Profit (Reported)"],
        "operating_income": ["Operating Income", "Operating Income or Loss", "Income From Continuing Operations"] ,
        "net_income": ["Net Income", "Net Income Applicable To Common Shares", "Net Income Available To Common Shareholders"],
        "ebitda": ["EBITDA", "Ebitda", "Earnings Before Interest, Taxes, Depreciation, and Amortization"],
        "total_assets": ["Total Assets", "Assets"],
        "total_liabilities": ["Total Liab", "Total Liabilities", "Total Liabilities Net Minority Interest"],
        "total_equity": ["Stockholders Equity", "Total Stockholder Equity", "Total Equity", "Shareholders Equity"],
        "cash_and_equivalents": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash And Short Term Investments"],
        "total_debt": ["Total Debt", "Long Term Debt", "Debt"],
        "operating_cash_flow": ["Operating Cash Flow", "Net Cash Provided By Operating Activities"],
        "investing_cash_flow": ["Investing Cash Flow", "Net Cash Used For Investing Activities"],
        "financing_cash_flow": ["Financing Cash Flow", "Net Cash Used Provided By Financing Activities"],
        "free_cash_flow": ["Free Cash Flow", "Free Cash Flow (FFO)"],
    }

    def __init__(self, default_timeout_seconds: int = 30, default_retries: int = 3) -> None:
        self.default_timeout_seconds = default_timeout_seconds
        self.default_retries = default_retries

    async def healthcheck(
        self,
        context: ProviderRequestContext | None = None,
    ) -> FinancialProviderHealth:
        started_at = perf_counter()
        try:
            await self.get_market_quote("ITUB4", context)
            status = ProviderStatus.OK
            message = None
        except Exception as exc:
            logger.warning("yahoo_finance_healthcheck_failed", extra={"error": str(exc)})
            status = ProviderStatus.DOWN
            message = str(exc)

        return FinancialProviderHealth(
            provider_name=self.name,
            status=status,
            checked_at=datetime.now(UTC),
            latency_ms=round((perf_counter() - started_at) * 1000),
            message=message,
        )

    async def get_stock_info(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockInfo]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        info = await self._run_with_retries(
            lambda: self._fetch_info(normalized_ticker),
            operation="get_stock_info",
            ticker=normalized_ticker,
            context=context,
        )
        stock_info = self._normalize_stock_info(ticker, info)
        return self._response(stock_info, started_at, info)

    async def get_stock_metrics(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockMetrics]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        info = await self._run_with_retries(
            lambda: self._fetch_info(normalized_ticker),
            operation="get_stock_metrics",
            ticker=normalized_ticker,
            context=context,
        )
        metrics = self._normalize_stock_metrics(ticker, info)
        return self._response(metrics, started_at, info)

    async def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        return await self.get_ohlcv_history(ticker, start_date, end_date, context)

    async def get_company_profile(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[CompanyProfile]:
        response = await self.get_stock_info(ticker, context)
        info = response.data
        return ProviderResponse(
            provider_name=self.name,
            data=CompanyProfile(
                ticker=info.ticker,
                company_name=info.company_name,
                exchange=info.exchange,
                asset_class=info.asset_class,
                currency=info.currency,
                sector=info.sector,
                industry=info.industry,
                website=info.website,
                description=info.description,
                market_cap=info.market_cap,
            ),
            fetched_at=response.fetched_at,
            source_latency_ms=response.source_latency_ms,
            raw_payload_hash=response.raw_payload_hash,
            metadata=response.metadata,
        )

    async def get_market_quote(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[MarketQuote]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        info = await self._run_with_retries(
            lambda: self._fetch_info(normalized_ticker),
            operation="get_market_quote",
            ticker=normalized_ticker,
            context=context,
        )
        quote = self._normalize_market_quote(ticker, info)
        return self._response(quote, started_at, info)

    async def get_market_quotes(
        self,
        tickers: Sequence[str],
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[MarketQuote]]:
        started_at = perf_counter()
        quotes: list[MarketQuote] = []
        errors: dict[str, str] = {}

        for ticker in tickers:
            try:
                quotes.append((await self.get_market_quote(ticker, context)).data)
            except Exception as exc:
                errors[ticker] = str(exc)
                logger.warning(
                    "yahoo_finance_quote_failed",
                    extra={"ticker": ticker, "error": str(exc)},
                )

        if not quotes and errors:
            raise ProviderUnavailableError(self.name, f"All quote requests failed: {errors}")

        return ProviderResponse(
            provider_name=self.name,
            data=quotes,
            fetched_at=datetime.now(UTC),
            source_latency_ms=round((perf_counter() - started_at) * 1000),
            metadata={"errors": str(errors)} if errors else {},
        )

    async def get_ohlcv_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        history = await self._run_with_retries(
            lambda: self._fetch_history(normalized_ticker, start_date, end_date),
            operation="get_ohlcv_history",
            ticker=normalized_ticker,
            context=context,
        )
        bars = self._normalize_ohlcv_history(ticker, history)
        return self._response(bars, started_at, {"rows": len(bars)})

    async def get_dividends(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[DividendEvent]]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        dividends = await self._run_with_retries(
            lambda: self._fetch_dividends(normalized_ticker, start_date, end_date),
            operation="get_dividends",
            ticker=normalized_ticker,
            context=context,
        )
        events = self._normalize_dividends(ticker, dividends)
        return self._response(events, started_at, {"rows": len(events)})

    async def get_financial_statements(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[FinancialStatementBundle]:
        normalized_ticker = self._normalize_ticker(ticker)
        started_at = perf_counter()
        payload = await self._run_with_retries(
            lambda: self._fetch_financial_statements(normalized_ticker),
            operation="get_financial_statements",
            ticker=normalized_ticker,
            context=context,
        )
        bundle = self._normalize_financial_statements(ticker, payload)
        return self._response(bundle, started_at, {"ticker": ticker})

    async def _run_with_retries(
        self,
        operation_fn: Callable[[], T],
        operation: str,
        ticker: str,
        context: ProviderRequestContext | None,
    ) -> T:
        effective_context = context or ProviderRequestContext(
            timeout_seconds=self.default_timeout_seconds,
            retries=self.default_retries,
        )
        retries = max(effective_context.retries, 1)
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    "yahoo_finance_request_started",
                    extra={"operation": operation, "ticker": ticker, "attempt": attempt},
                )
                return await asyncio.wait_for(
                    asyncio.to_thread(operation_fn),
                    timeout=effective_context.timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "yahoo_finance_request_timeout",
                    extra={"operation": operation, "ticker": ticker, "attempt": attempt},
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "yahoo_finance_request_failed",
                    extra={
                        "operation": operation,
                        "ticker": ticker,
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )

            if attempt < retries:
                await asyncio.sleep(min(2 ** (attempt - 1), 8))

        raise ProviderUnavailableError(
            self.name,
            f"{operation} failed for {ticker}: {last_error}",
        )

    def _fetch_info(self, yahoo_ticker: str) -> dict[str, Any]:
        info = yf.Ticker(yahoo_ticker).get_info()
        if not isinstance(info, dict) or not info:
            raise ProviderPayloadError(self.name, f"Empty info payload for {yahoo_ticker}.")
        return info

    def _fetch_history(self, yahoo_ticker: str, start_date: date, end_date: date):
        history = yf.Ticker(yahoo_ticker).history(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            auto_adjust=False,
            actions=False,
            raise_errors=True,
        )
        if history is None or history.empty:
            raise ProviderPayloadError(self.name, f"Empty history payload for {yahoo_ticker}.")
        return history

    def _fetch_dividends(self, yahoo_ticker: str, start_date: date, end_date: date):
        dividends = yf.Ticker(yahoo_ticker).dividends
        if dividends is None or dividends.empty:
            return dividends
        return dividends[(dividends.index.date >= start_date) & (dividends.index.date <= end_date)]

    def _fetch_financial_statements(self, yahoo_ticker: str) -> dict[str, Any]:
        ticker = yf.Ticker(yahoo_ticker)
        return {
            "income_stmt": ticker.income_stmt,
            "balance_sheet": ticker.balance_sheet,
            "cashflow": ticker.cashflow,
        }

    def _normalize_stock_info(self, original_ticker: str, info: dict[str, Any]) -> StockInfo:
        ticker = self._canonical_ticker(original_ticker)
        return StockInfo(
            ticker=ticker,
            company_name=self._string(info, "longName", "shortName", default=ticker),
            exchange=self._exchange(info),
            asset_class=self._asset_class(info),
            currency=self._currency(info),
            sector=self._optional_string(info, "sector"),
            industry=self._optional_string(info, "industry"),
            website=self._optional_string(info, "website"),
            description=self._optional_string(info, "longBusinessSummary"),
            market_cap=self._decimal(info.get("marketCap")),
            employees=self._int(info.get("fullTimeEmployees")),
        )

    def _normalize_stock_metrics(self, original_ticker: str, info: dict[str, Any]) -> StockMetrics:
        return StockMetrics(
            ticker=self._canonical_ticker(original_ticker),
            reference_datetime=datetime.now(UTC),
            currency=self._currency(info),
            market_cap=self._numeric_field(info, "market_cap"),
            enterprise_value=self._numeric_field(info, "enterprise_value"),
            trailing_pe=self._numeric_field(info, "trailing_pe"),
            forward_pe=self._numeric_field(info, "forward_pe"),
            price_to_book=self._numeric_field(info, "price_to_book"),
            dividend_yield=self._normalize_ratio(self._numeric_field(info, "dividend_yield")),
            payout_ratio=self._normalize_ratio(self._numeric_field(info, "payout_ratio")),
            beta=self._numeric_field(info, "beta"),
            return_on_equity=self._normalize_ratio(self._numeric_field(info, "return_on_equity")),
            return_on_assets=self._normalize_ratio(self._numeric_field(info, "return_on_assets")),
            debt_to_equity=self._normalize_ratio(self._numeric_field(info, "debt_to_equity")),
            gross_margins=self._normalize_ratio(self._numeric_field(info, "gross_margins")),
            operating_margins=self._normalize_ratio(self._numeric_field(info, "operating_margins")),
            profit_margins=self._normalize_ratio(self._numeric_field(info, "profit_margins")),
        )

    def _normalize_market_quote(self, original_ticker: str, info: dict[str, Any]) -> MarketQuote:
        price = self._first_numeric(
            info,
            ["regularMarketPrice", "currentPrice", "previousClose", "ask", "bid"],
        )
        if price is None:
            raise ProviderPayloadError(self.name, f"Missing price for {original_ticker}.")

        return MarketQuote(
            ticker=self._canonical_ticker(original_ticker),
            exchange=self._exchange(info),
            currency=self._currency(info),
            price=price,
            reference_datetime=datetime.now(UTC),
            previous_close=self._numeric_field(info, "previousClose"),
            open_price=self._numeric_field(info, "open"),
            day_high=self._numeric_field(info, "dayHigh"),
            day_low=self._numeric_field(info, "dayLow"),
            volume=self._int(info.get("volume") or info.get("averageDailyVolume10Day") or info.get("volume24Hr")),
        )

    def _normalize_ohlcv_history(self, original_ticker: str, history) -> list[OHLCVBar]:
        bars: list[OHLCVBar] = []
        for index, row in history.iterrows():
            open_price = self._decimal(row.get("Open"))
            high_price = self._decimal(row.get("High"))
            low_price = self._decimal(row.get("Low"))
            close_price = self._decimal(row.get("Close"))
            volume = self._int(row.get("Volume"))
            if None in (open_price, high_price, low_price, close_price) or volume is None:
                continue

            bars.append(
                OHLCVBar(
                    ticker=self._canonical_ticker(original_ticker),
                    date=index.date(),
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    adjusted_close=self._decimal(row.get("Adj Close")),
                    volume=volume,
                )
            )
        return bars

    def _normalize_dividends(self, original_ticker: str, dividends) -> list[DividendEvent]:
        if dividends is None or dividends.empty:
            return []

        events: list[DividendEvent] = []
        for index, amount in dividends.items():
            decimal_amount = self._decimal(amount)
            if decimal_amount is None or decimal_amount <= Decimal("0"):
                continue
            events.append(
                DividendEvent(
                    ticker=self._canonical_ticker(original_ticker),
                    ex_date=index.date(),
                    payment_date=None,
                    amount=decimal_amount,
                    currency=Currency.BRL if self._is_b3_ticker(original_ticker) else Currency.USD,
                )
            )
        return events

    def _normalize_financial_statements(
        self,
        original_ticker: str,
        payload: dict[str, Any],
    ) -> FinancialStatementBundle:
        ticker = self._canonical_ticker(original_ticker)
        return FinancialStatementBundle(
            ticker=ticker,
            income_statements=[
                IncomeStatementSnapshot(
                    ticker=ticker,
                    period=period,
                    revenue=self._statement_value(payload["income_stmt"], column, "total_revenue"),
                    gross_profit=self._statement_value(payload["income_stmt"], column, "gross_profit"),
                    operating_income=self._statement_value(payload["income_stmt"], column, "operating_income"),
                    net_income=self._statement_value(payload["income_stmt"], column, "net_income"),
                    ebitda=self._statement_value(payload["income_stmt"], column, "ebitda"),
                )
                for column, period in self._statement_periods(payload.get("income_stmt"))
            ],
            balance_sheets=[
                BalanceSheetSnapshot(
                    ticker=ticker,
                    period=period,
                    total_assets=self._statement_value(payload["balance_sheet"], column, "total_assets"),
                    total_liabilities=self._statement_value(payload["balance_sheet"], column, "total_liabilities"),
                    total_equity=self._statement_value(payload["balance_sheet"], column, "total_equity"),
                    cash_and_equivalents=self._statement_value(payload["balance_sheet"], column, "cash_and_equivalents"),
                    total_debt=self._statement_value(payload["balance_sheet"], column, "total_debt"),
                )
                for column, period in self._statement_periods(payload.get("balance_sheet"))
            ],
            cash_flows=[
                CashFlowSnapshot(
                    ticker=ticker,
                    period=period,
                    operating_cash_flow=self._statement_value(payload["cashflow"], column, "operating_cash_flow"),
                    investing_cash_flow=self._statement_value(payload["cashflow"], column, "investing_cash_flow"),
                    financing_cash_flow=self._statement_value(payload["cashflow"], column, "financing_cash_flow"),
                    free_cash_flow=self._statement_value(payload["cashflow"], column, "free_cash_flow"),
                )
                for column, period in self._statement_periods(payload.get("cashflow"))
            ],
        )

    def _statement_periods(self, statement) -> list[tuple[Any, FinancialStatementPeriod]]:
        if statement is None or getattr(statement, "empty", True):
            return []

        periods: list[tuple[Any, FinancialStatementPeriod]] = []
        for column in statement.columns:
            try:
                period_end = column.date()
            except AttributeError:
                try:
                    period_end = datetime.fromisoformat(str(column)).date()
                except Exception:
                    continue
            periods.append(
                (
                    column,
                    FinancialStatementPeriod(
                        fiscal_year=period_end.year,
                        period_type=StatementPeriodType.ANNUAL,
                        period_end_date=period_end,
                    ),
                )
            )
        return periods

    def _statement_value(self, statement, column: Any, row_key: str) -> Decimal | None:
        if statement is None or getattr(statement, "empty", True):
            return None

        aliases = self._STATEMENT_ROW_ALIASES.get(row_key, [row_key])
        for alias in aliases:
            if alias in statement.index:
                return self._decimal(statement.at[alias, column])
        return None

    def _response(self, data: T, started_at: float, raw_payload: Any) -> ProviderResponse[T]:
        return ProviderResponse(
            provider_name=self.name,
            data=data,
            fetched_at=datetime.now(UTC),
            source_latency_ms=round((perf_counter() - started_at) * 1000),
            raw_payload_hash=self._payload_hash(raw_payload),
        )

    def _normalize_ticker(self, ticker: str) -> str:
        canonical = self._canonical_ticker(ticker)
        return f"{canonical}.SA" if self._is_b3_ticker(canonical) else canonical

    def _canonical_ticker(self, ticker: str) -> str:
        return ticker.upper().replace(".SA", "").strip()

    def _is_b3_ticker(self, ticker: str) -> bool:
        canonical = self._canonical_ticker(ticker)
        return len(canonical) >= 5 and canonical[-1].isdigit()

    def _currency(self, info: dict[str, Any]) -> Currency:
        currency = str(info.get("currency") or "").upper()
        if currency == Currency.USD:
            return Currency.USD
        return Currency.BRL

    def _exchange(self, info: dict[str, Any]) -> Exchange:
        exchange = str(info.get("exchange") or info.get("fullExchangeName") or "").upper()
        if "NASDAQ" in exchange:
            return Exchange.NASDAQ
        if "NYSE" in exchange:
            return Exchange.NYSE
        return Exchange.B3

    def _asset_class(self, info: dict[str, Any]) -> AssetClass:
        quote_type = str(info.get("quoteType") or "").upper()
        if quote_type == "ETF":
            return AssetClass.ETF
        return AssetClass.STOCK

    def _string(self, payload: dict[str, Any], *keys: str, default: str) -> str:
        for key in keys:
            value = self._optional_string(payload, key)
            if value:
                return value
        return default

    def _numeric_field(self, payload: dict[str, Any], field_name: str) -> Decimal | None:
        for alias in self._METRIC_FIELD_ALIASES.get(field_name, [field_name]):
            if alias in payload:
                value = payload.get(alias)
                numeric = self._decimal(value)
                if numeric is not None:
                    return numeric
        return None

    def _normalize_ratio(self, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if value > Decimal("1") and value <= Decimal("100"):
            return (value / Decimal("100")).quantize(Decimal("0.0000001"))
        return value

    def _first_numeric(self, payload: dict[str, Any], field_names: list[str]) -> Decimal | None:
        for field_name in field_names:
            numeric = self._decimal(payload.get(field_name))
            if numeric is not None:
                return numeric
        return None

    def _optional_string(self, payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _int(self, value: Any) -> int | None:
        decimal_value = self._decimal(value)
        if decimal_value is None:
            return None
        return int(decimal_value)

    def _payload_hash(self, payload: Any) -> str:
        return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
