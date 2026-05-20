from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from core.providers.financial.enums import AssetClass, Currency, Exchange


class FinancialBaseDTO(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
        use_enum_values=False,
    )

    @staticmethod
    def normalize_ticker(value: str) -> str:
        return value.upper().replace(".SA", "").strip()

    @staticmethod
    def normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class StockInfoDTO(FinancialBaseDTO):
    ticker: str = Field(min_length=5, max_length=12, examples=["ITUB4"])
    company_name: str = Field(
        min_length=1,
        max_length=255,
        validation_alias="companyName",
    )
    exchange: Exchange = Exchange.B3
    asset_class: AssetClass = AssetClass.STOCK
    currency: Currency = Currency.BRL
    sector: str | None = Field(default=None, max_length=120)
    industry: str | None = Field(default=None, max_length=160)
    website: HttpUrl | None = None
    description: str | None = None
    market_cap: Decimal | None = Field(default=None, ge=0)
    employees: int | None = Field(default=None, ge=0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker_field(cls, value: str) -> str:
        return cls.normalize_ticker(value)

    @field_validator("company_name", "sector", "industry", "description", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls.normalize_optional_text(value)
        return value


class StockMetricsDTO(FinancialBaseDTO):
    ticker: str = Field(min_length=5, max_length=12)
    reference_datetime: datetime = Field(validation_alias="referenceDatetime")
    currency: Currency = Currency.BRL
    market_cap: Decimal | None = Field(default=None, ge=0, validation_alias="marketCap")
    enterprise_value: Decimal | None = Field(
        default=None,
        validation_alias="enterpriseValue",
    )
    trailing_pe: Decimal | None = Field(default=None, validation_alias="trailingPE")
    forward_pe: Decimal | None = Field(default=None, validation_alias="forwardPE")
    price_to_book: Decimal | None = Field(default=None, ge=0, validation_alias="priceToBook")
    dividend_yield: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        validation_alias="dividendYield",
    )
    payout_ratio: Decimal | None = Field(default=None, ge=0, validation_alias="payoutRatio")
    beta: Decimal | None = None
    return_on_equity: Decimal | None = Field(default=None, validation_alias="returnOnEquity")
    return_on_assets: Decimal | None = Field(default=None, validation_alias="returnOnAssets")
    debt_to_equity: Decimal | None = Field(default=None, validation_alias="debtToEquity")
    gross_margins: Decimal | None = Field(default=None, validation_alias="grossMargins")
    operating_margins: Decimal | None = Field(default=None, validation_alias="operatingMargins")
    profit_margins: Decimal | None = Field(default=None, validation_alias="profitMargins")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker_field(cls, value: str) -> str:
        return cls.normalize_ticker(value)


class PriceHistoryBarDTO(FinancialBaseDTO):
    date: date
    open_price: Decimal = Field(gt=0, validation_alias="open")
    high_price: Decimal = Field(gt=0, validation_alias="high")
    low_price: Decimal = Field(gt=0, validation_alias="low")
    close_price: Decimal = Field(gt=0, validation_alias="close")
    adjusted_close: Decimal | None = Field(default=None, gt=0, validation_alias="adjustedClose")
    volume: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_price_range(self) -> "PriceHistoryBarDTO":
        max_price = max(self.open_price, self.close_price, self.high_price, self.low_price)
        min_price = min(self.open_price, self.close_price, self.high_price, self.low_price)
        if self.high_price < max_price:
            raise ValueError("high_price must be greater than or equal to all OHLC prices")
        if self.low_price > min_price:
            raise ValueError("low_price must be less than or equal to all OHLC prices")
        return self


class PriceHistoryDTO(FinancialBaseDTO):
    ticker: str = Field(min_length=5, max_length=12)
    currency: Currency = Currency.BRL
    items: list[PriceHistoryBarDTO] = Field(default_factory=list)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker_field(cls, value: str) -> str:
        return cls.normalize_ticker(value)

    @field_validator("items")
    @classmethod
    def sort_items(cls, value: list[PriceHistoryBarDTO]) -> list[PriceHistoryBarDTO]:
        return sorted(value, key=lambda item: item.date)


class DividendDTO(FinancialBaseDTO):
    ticker: str = Field(min_length=5, max_length=12)
    ex_date: date = Field(validation_alias="exDate")
    payment_date: date | None = Field(default=None, validation_alias="paymentDate")
    amount: Decimal = Field(gt=0)
    currency: Currency = Currency.BRL

    @field_validator("ticker")
    @classmethod
    def normalize_ticker_field(cls, value: str) -> str:
        return cls.normalize_ticker(value)

    @model_validator(mode="after")
    def validate_payment_date(self) -> "DividendDTO":
        if self.payment_date is not None and self.payment_date < self.ex_date:
            raise ValueError("payment_date cannot be before ex_date")
        return self
