"""financial ingestion tables

Revision ID: 20260519_0002
Revises: 20260519_0001
Create Date: 2026-05-19 22:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260519_0002"
down_revision: str | None = "20260519_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_metrics_snapshots",
        sa.Column("stock_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("market_cap", sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("trailing_pe", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("price_to_book", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "reference_date", name="uq_stock_metrics_ticker_reference_date"),
    )
    op.create_index(
        "ix_stock_metrics_ticker_reference_date",
        "stock_metrics_snapshots",
        ["ticker", "reference_date"],
    )

    op.create_table(
        "stock_prices_daily",
        sa.Column("stock_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "price_date", name="uq_stock_price_ticker_price_date"),
    )
    op.create_index(
        "ix_stock_price_ticker_price_date",
        "stock_prices_daily",
        ["ticker", "price_date"],
    )

    op.create_table(
        "stock_dividends",
        sa.Column("stock_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "ex_date", "amount", name="uq_stock_dividend_ticker_ex_date_amount"),
    )
    op.create_index("ix_stock_dividend_ticker_ex_date", "stock_dividends", ["ticker", "ex_date"])


def downgrade() -> None:
    op.drop_index("ix_stock_dividend_ticker_ex_date", table_name="stock_dividends")
    op.drop_table("stock_dividends")
    op.drop_index("ix_stock_price_ticker_price_date", table_name="stock_prices_daily")
    op.drop_table("stock_prices_daily")
    op.drop_index("ix_stock_metrics_ticker_reference_date", table_name="stock_metrics_snapshots")
    op.drop_table("stock_metrics_snapshots")
