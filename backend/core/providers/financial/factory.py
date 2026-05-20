from core.providers.financial.null_provider import NullFinancialProvider
from core.providers.financial.registry import FinancialProviderRegistry
from core.providers.financial.yahoo_finance_provider import YahooFinanceProvider


def create_default_financial_provider_registry() -> FinancialProviderRegistry:
    registry = FinancialProviderRegistry()
    registry.register("null", NullFinancialProvider)
    registry.register("yahoo_finance", YahooFinanceProvider)
    registry.register("yahoo", YahooFinanceProvider)
    return registry
