from collections.abc import Sequence
from datetime import UTC, date, datetime

from core.providers.financial.base import FinancialDataProvider
from core.providers.financial.enums import ProviderCapability, ProviderStatus
from core.providers.financial.errors import ProviderUnavailableError
from core.providers.financial.models import (
    CompanyProfile,
    DividendEvent,
    FinancialProviderHealth,
    FinancialStatementBundle,
    MarketQuote,
    OHLCVBar,
    ProviderMetadata,
    ProviderRequestContext,
    ProviderResponse,
    StockInfo,
    StockMetrics,
)


class NullFinancialProvider(FinancialDataProvider):
    metadata = ProviderMetadata(
        name="null",
        display_name="Null Financial Provider",
        capabilities=frozenset(ProviderCapability),
    )

    async def healthcheck(
        self,
        context: ProviderRequestContext | None = None,
    ) -> FinancialProviderHealth:
        return FinancialProviderHealth(
            provider_name=self.name,
            status=ProviderStatus.DOWN,
            checked_at=datetime.now(UTC),
            message="Null provider is a placeholder and cannot fetch market data.",
        )

    async def get_company_profile(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[CompanyProfile]:
        raise self._unavailable()

    async def get_stock_info(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockInfo]:
        raise self._unavailable()

    async def get_stock_metrics(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockMetrics]:
        raise self._unavailable()

    async def get_market_quote(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[MarketQuote]:
        raise self._unavailable()

    async def get_market_quotes(
        self,
        tickers: Sequence[str],
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[MarketQuote]]:
        raise self._unavailable()

    async def get_ohlcv_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        raise self._unavailable()

    async def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        raise self._unavailable()

    async def get_dividends(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[DividendEvent]]:
        raise self._unavailable()

    async def get_financial_statements(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[FinancialStatementBundle]:
        raise self._unavailable()

    def _unavailable(self) -> ProviderUnavailableError:
        return ProviderUnavailableError(
            self.name,
            "Null provider cannot fetch financial data.",
        )
