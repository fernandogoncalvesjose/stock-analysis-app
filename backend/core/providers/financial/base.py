from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date

from core.providers.financial.enums import ProviderCapability
from core.providers.financial.errors import UnsupportedProviderCapabilityError
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


class FinancialDataProvider(ABC):
    metadata: ProviderMetadata

    @property
    def name(self) -> str:
        return self.metadata.name

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.metadata.capabilities

    def require_capability(self, capability: ProviderCapability) -> None:
        if not self.supports(capability):
            raise UnsupportedProviderCapabilityError(
                self.name,
                f"Capability {capability.value} is not supported.",
            )

    @abstractmethod
    async def healthcheck(
        self,
        context: ProviderRequestContext | None = None,
    ) -> FinancialProviderHealth:
        raise NotImplementedError

    @abstractmethod
    async def get_company_profile(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[CompanyProfile]:
        raise NotImplementedError

    @abstractmethod
    async def get_stock_info(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockInfo]:
        raise NotImplementedError

    @abstractmethod
    async def get_stock_metrics(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[StockMetrics]:
        raise NotImplementedError

    @abstractmethod
    async def get_market_quote(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[MarketQuote]:
        raise NotImplementedError

    @abstractmethod
    async def get_market_quotes(
        self,
        tickers: Sequence[str],
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[MarketQuote]]:
        raise NotImplementedError

    @abstractmethod
    async def get_ohlcv_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        raise NotImplementedError

    @abstractmethod
    async def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[OHLCVBar]]:
        raise NotImplementedError

    @abstractmethod
    async def get_dividends(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[list[DividendEvent]]:
        raise NotImplementedError

    @abstractmethod
    async def get_financial_statements(
        self,
        ticker: str,
        context: ProviderRequestContext | None = None,
    ) -> ProviderResponse[FinancialStatementBundle]:
        raise NotImplementedError
