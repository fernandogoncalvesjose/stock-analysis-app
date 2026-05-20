from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

from core.providers.financial.enums import (
    AssetClass,
    Currency,
    Exchange,
    ProviderCapability,
    ProviderStatus,
    StatementPeriodType,
)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ProviderRequestContext:
    request_id: str | None = None
    timeout_seconds: int = 30
    retries: int = 3
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse(Generic[T]):
    provider_name: str
    data: T
    fetched_at: datetime
    source_latency_ms: int | None = None
    raw_payload_hash: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FinancialProviderHealth:
    provider_name: str
    status: ProviderStatus
    checked_at: datetime
    latency_ms: int | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    ticker: str
    company_name: str
    exchange: Exchange
    asset_class: AssetClass
    currency: Currency
    sector: str | None = None
    industry: str | None = None
    website: str | None = None
    description: str | None = None
    market_cap: Decimal | None = None


@dataclass(frozen=True, slots=True)
class StockInfo:
    ticker: str
    company_name: str
    exchange: Exchange
    asset_class: AssetClass
    currency: Currency
    sector: str | None = None
    industry: str | None = None
    website: str | None = None
    description: str | None = None
    market_cap: Decimal | None = None
    employees: int | None = None


@dataclass(frozen=True, slots=True)
class StockMetrics:
    ticker: str
    reference_datetime: datetime
    currency: Currency
    market_cap: Decimal | None = None
    enterprise_value: Decimal | None = None
    trailing_pe: Decimal | None = None
    forward_pe: Decimal | None = None
    price_to_book: Decimal | None = None
    dividend_yield: Decimal | None = None
    payout_ratio: Decimal | None = None
    beta: Decimal | None = None
    return_on_equity: Decimal | None = None
    return_on_assets: Decimal | None = None
    debt_to_equity: Decimal | None = None
    gross_margins: Decimal | None = None
    operating_margins: Decimal | None = None
    profit_margins: Decimal | None = None


@dataclass(frozen=True, slots=True)
class MarketQuote:
    ticker: str
    exchange: Exchange
    currency: Currency
    price: Decimal
    reference_datetime: datetime
    previous_close: Decimal | None = None
    open_price: Decimal | None = None
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    volume: int | None = None


@dataclass(frozen=True, slots=True)
class OHLCVBar:
    ticker: str
    date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    adjusted_close: Decimal | None
    volume: int


@dataclass(frozen=True, slots=True)
class DividendEvent:
    ticker: str
    ex_date: date
    payment_date: date | None
    amount: Decimal
    currency: Currency


@dataclass(frozen=True, slots=True)
class FinancialStatementPeriod:
    fiscal_year: int
    period_type: StatementPeriodType
    period_end_date: date


@dataclass(frozen=True, slots=True)
class IncomeStatementSnapshot:
    ticker: str
    period: FinancialStatementPeriod
    revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    ebitda: Decimal | None = None


@dataclass(frozen=True, slots=True)
class BalanceSheetSnapshot:
    ticker: str
    period: FinancialStatementPeriod
    total_assets: Decimal | None = None
    total_liabilities: Decimal | None = None
    total_equity: Decimal | None = None
    cash_and_equivalents: Decimal | None = None
    total_debt: Decimal | None = None


@dataclass(frozen=True, slots=True)
class CashFlowSnapshot:
    ticker: str
    period: FinancialStatementPeriod
    operating_cash_flow: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    free_cash_flow: Decimal | None = None


@dataclass(frozen=True, slots=True)
class FinancialStatementBundle:
    ticker: str
    income_statements: list[IncomeStatementSnapshot]
    balance_sheets: list[BalanceSheetSnapshot]
    cash_flows: list[CashFlowSnapshot]


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    name: str
    display_name: str
    capabilities: frozenset[ProviderCapability]
