import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Recommendation(StrEnum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class Stock(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(120))
    exchange: Mapped[str] = mapped_column(String(20), default="B3", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    snapshots: Mapped[list["StockAnalysisSnapshot"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    metric_snapshots: Mapped[list["StockMetricsSnapshot"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    prices: Mapped[list["StockPriceDaily"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    dividends: Mapped[list["StockDividend"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )


class StockAnalysisSnapshot(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_analysis_snapshots"
    __table_args__ = (
        UniqueConstraint("ticker", "reference_date", name="uq_snapshot_ticker_reference_date"),
        Index("ix_snapshot_ticker_reference_date", "ticker", "reference_date"),
        Index("ix_snapshot_recommendation_reference_date", "recommendation", "reference_date"),
    )

    stock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    recommendation: Mapped[Recommendation] = mapped_column(String(8), nullable=False)
    composite_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    stock: Mapped[Stock] = relationship(back_populates="snapshots")


class StockMetricsSnapshot(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_metrics_snapshots"
    __table_args__ = (
        UniqueConstraint("ticker", "reference_date", name="uq_stock_metrics_ticker_reference_date"),
        Index("ix_stock_metrics_ticker_reference_date", "ticker", "reference_date"),
    )

    stock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    trailing_pe: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_to_book: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    stock: Mapped[Stock] = relationship(back_populates="metric_snapshots")


class StockPriceDaily(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_prices_daily"
    __table_args__ = (
        UniqueConstraint("ticker", "price_date", name="uq_stock_price_ticker_price_date"),
        Index("ix_stock_price_ticker_price_date", "ticker", "price_date"),
    )

    stock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volume: Mapped[int] = mapped_column(nullable=False)

    stock: Mapped[Stock] = relationship(back_populates="prices")


class StockDividend(Base, TimestampMixin, UUIDPrimaryKeyMixin):
    __tablename__ = "stock_dividends"
    __table_args__ = (
        UniqueConstraint("ticker", "ex_date", "amount", name="uq_stock_dividend_ticker_ex_date_amount"),
        Index("ix_stock_dividend_ticker_ex_date", "ticker", "ex_date"),
    )

    stock_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    stock: Mapped[Stock] = relationship(back_populates="dividends")
