CREATE TABLE IF NOT EXISTS stock_metrics_snapshots (
    stock_id UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ticker VARCHAR(12) NOT NULL,
    reference_date DATE NOT NULL,
    provider_name VARCHAR(80) NOT NULL,
    market_cap NUMERIC(24, 4),
    dividend_yield NUMERIC(12, 6),
    trailing_pe NUMERIC(12, 4),
    price_to_book NUMERIC(12, 4),
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id UUID NOT NULL,
    CONSTRAINT pk_stock_metrics_snapshots PRIMARY KEY (id),
    CONSTRAINT uq_stock_metrics_ticker_reference_date UNIQUE (ticker, reference_date)
);

CREATE INDEX IF NOT EXISTS ix_stock_metrics_ticker_reference_date
    ON stock_metrics_snapshots (ticker, reference_date);

CREATE TABLE IF NOT EXISTS stock_prices_daily (
    stock_id UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ticker VARCHAR(12) NOT NULL,
    price_date DATE NOT NULL,
    provider_name VARCHAR(80) NOT NULL,
    open_price NUMERIC(18, 6) NOT NULL,
    high_price NUMERIC(18, 6) NOT NULL,
    low_price NUMERIC(18, 6) NOT NULL,
    close_price NUMERIC(18, 6) NOT NULL,
    adjusted_close NUMERIC(18, 6),
    volume INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id UUID NOT NULL,
    CONSTRAINT pk_stock_prices_daily PRIMARY KEY (id),
    CONSTRAINT uq_stock_price_ticker_price_date UNIQUE (ticker, price_date)
);

CREATE INDEX IF NOT EXISTS ix_stock_price_ticker_price_date
    ON stock_prices_daily (ticker, price_date);

CREATE TABLE IF NOT EXISTS stock_dividends (
    stock_id UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ticker VARCHAR(12) NOT NULL,
    ex_date DATE NOT NULL,
    payment_date DATE,
    provider_name VARCHAR(80) NOT NULL,
    amount NUMERIC(18, 6) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    id UUID NOT NULL,
    CONSTRAINT pk_stock_dividends PRIMARY KEY (id),
    CONSTRAINT uq_stock_dividend_ticker_ex_date_amount UNIQUE (ticker, ex_date, amount)
);

CREATE INDEX IF NOT EXISTS ix_stock_dividend_ticker_ex_date
    ON stock_dividends (ticker, ex_date);

DELETE FROM alembic_version;

INSERT INTO alembic_version (version_num)
VALUES ('20260519_0002');
