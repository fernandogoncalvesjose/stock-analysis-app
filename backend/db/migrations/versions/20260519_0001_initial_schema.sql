CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(12) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(120),
    exchange VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id UUID NOT NULL,
    CONSTRAINT pk_stocks PRIMARY KEY (id),
    CONSTRAINT uq_stocks_ticker UNIQUE (ticker)
);

CREATE INDEX IF NOT EXISTS ix_stocks_ticker ON stocks (ticker);

CREATE TABLE IF NOT EXISTS stock_analysis_snapshots (
    stock_id UUID NOT NULL,
    ticker VARCHAR(12) NOT NULL,
    reference_date DATE NOT NULL,
    recommendation VARCHAR(8) NOT NULL,
    composite_score NUMERIC(5, 2) NOT NULL,
    dividend_yield NUMERIC(8, 4),
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id UUID NOT NULL,
    CONSTRAINT pk_stock_analysis_snapshots PRIMARY KEY (id),
    CONSTRAINT fk_stock_analysis_snapshots_stock_id_stocks
        FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    CONSTRAINT uq_snapshot_ticker_reference_date UNIQUE (ticker, reference_date)
);

CREATE INDEX IF NOT EXISTS ix_snapshot_recommendation_reference_date
    ON stock_analysis_snapshots (recommendation, reference_date);

CREATE INDEX IF NOT EXISTS ix_snapshot_ticker_reference_date
    ON stock_analysis_snapshots (ticker, reference_date);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num)
VALUES ('20260519_0001')
ON CONFLICT (version_num) DO NOTHING;
