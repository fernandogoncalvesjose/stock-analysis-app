from enum import StrEnum


class AssetClass(StrEnum):
    STOCK = "STOCK"
    ETF = "ETF"
    FII = "FII"
    BDR = "BDR"


class Currency(StrEnum):
    BRL = "BRL"
    USD = "USD"


class Exchange(StrEnum):
    B3 = "B3"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


class ProviderCapability(StrEnum):
    COMPANY_PROFILE = "COMPANY_PROFILE"
    MARKET_QUOTES = "MARKET_QUOTES"
    OHLCV_HISTORY = "OHLCV_HISTORY"
    DIVIDENDS = "DIVIDENDS"
    FINANCIAL_STATEMENTS = "FINANCIAL_STATEMENTS"


class ProviderStatus(StrEnum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class StatementPeriodType(StrEnum):
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
