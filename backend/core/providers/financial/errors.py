class FinancialProviderError(Exception):
    def __init__(self, provider_name: str, message: str) -> None:
        self.provider_name = provider_name
        self.message = message
        super().__init__(f"{provider_name}: {message}")


class ProviderUnavailableError(FinancialProviderError):
    pass


class ProviderRateLimitError(FinancialProviderError):
    pass


class ProviderPayloadError(FinancialProviderError):
    pass


class UnsupportedProviderCapabilityError(FinancialProviderError):
    pass
