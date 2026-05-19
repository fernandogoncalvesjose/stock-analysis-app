"""initial schema

Revision ID: 20260519_0001
Revises:
Create Date: 2026-05-19 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260519_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("exchange", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stocks")),
        sa.UniqueConstraint("ticker", name=op.f("uq_stocks_ticker")),
    )
    op.create_index(op.f("ix_stocks_ticker"), "stocks", ["ticker"], unique=False)

    op.create_table(
        "stock_analysis_snapshots",
        sa.Column("stock_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("recommendation", sa.String(length=8), nullable=False),
        sa.Column("composite_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("dividend_yield", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], name=op.f("fk_stock_analysis_snapshots_stock_id_stocks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_analysis_snapshots")),
        sa.UniqueConstraint("ticker", "reference_date", name="uq_snapshot_ticker_reference_date"),
    )
    op.create_index(
        "ix_snapshot_recommendation_reference_date",
        "stock_analysis_snapshots",
        ["recommendation", "reference_date"],
        unique=False,
    )
    op.create_index(
        "ix_snapshot_ticker_reference_date",
        "stock_analysis_snapshots",
        ["ticker", "reference_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_snapshot_ticker_reference_date", table_name="stock_analysis_snapshots")
    op.drop_index("ix_snapshot_recommendation_reference_date", table_name="stock_analysis_snapshots")
    op.drop_table("stock_analysis_snapshots")
    op.drop_index(op.f("ix_stocks_ticker"), table_name="stocks")
    op.drop_table("stocks")
