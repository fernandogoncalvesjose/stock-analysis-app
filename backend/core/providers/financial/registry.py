from collections.abc import Callable

from core.providers.financial.base import FinancialDataProvider

ProviderFactory = Callable[[], FinancialDataProvider]


class FinancialProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, provider_name: str, factory: ProviderFactory) -> None:
        normalized = provider_name.strip().lower()
        if not normalized:
            raise ValueError("provider_name cannot be empty")
        self._factories[normalized] = factory

    def create(self, provider_name: str) -> FinancialDataProvider:
        normalized = provider_name.strip().lower()
        try:
            return self._factories[normalized]()
        except KeyError as exc:
            registered = ", ".join(sorted(self._factories)) or "none"
            raise KeyError(
                f"Financial provider '{provider_name}' is not registered. "
                f"Registered providers: {registered}."
            ) from exc

    def registered_names(self) -> list[str]:
        return sorted(self._factories)
