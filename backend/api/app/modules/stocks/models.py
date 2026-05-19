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
