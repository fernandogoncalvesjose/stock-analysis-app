from __future__ import annotations

import argparse
import asyncio
import logging
import os
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Iterable
import sys

# adjust pythonpath so we can import app and core packages when script is executed directly
backend_root = Path(__file__).resolve().parents[3]
api_root = backend_root / "api"
core_root = backend_root
for path in (api_root, core_root):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

# Remove empty environment variables so Pydantic Settings can fall back to defaults
for key in list(os.environ):
    if os.environ.get(key, None) == "":
        del os.environ[key]

if os.environ.get("CORS_ORIGINS", "").strip() == "":
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from batch.app.services.score_service import ScoreService
from app.modules.stocks.models import Stock

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    os.environ.get("database_url", "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_analysis"),
)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
)
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


logger = logging.getLogger(__name__)


async def _worker(ticker: str, semaphore: asyncio.Semaphore, results: dict) -> None:
    async with semaphore:
        start = perf_counter()
        try:
            async with AsyncSessionFactory() as session:
                svc = ScoreService(session)
                res = await svc.compute_and_persist(ticker)

            duration_ms = round((perf_counter() - start) * 1000, 2)
            if res.get("ok"):
                logger.info("score_ok", extra={"ticker": ticker, "duration_ms": duration_ms})
                results["success"].append(ticker)
            else:
                logger.warning("score_failed", extra={"ticker": ticker, "reason": res.get("reason"), "error": res.get("error")})
                results["failed"].append({"ticker": ticker, "reason": res.get("reason"), "error": res.get("error")})
        except Exception as exc:  # pragma: no cover - defensive
            duration_ms = round((perf_counter() - start) * 1000, 2)
            logger.exception("score_exception", extra={"ticker": ticker, "duration_ms": duration_ms, "error": str(exc)})
            results["failed"].append({"ticker": ticker, "reason": "exception", "error": str(exc)})


async def compute_scores(tickers: Iterable[str] | None = None, concurrency: int = 8) -> dict:
    """Compute and persist scores for a list of `tickers`. If `tickers` is None,
    the function will process all active stocks from the database.

    Returns a summary dict with counts and failures.
    """
    started_at = perf_counter()
    results: dict = {"success": [], "failed": []}

    # resolve tickers from DB when not provided
    if not tickers:
        async with AsyncSessionFactory() as session:
            stmt = select(Stock.ticker).where(Stock.is_active == True)
            resp = await session.execute(stmt)
            tickers = [row[0] for row in resp.all()]

    tickers = list(dict.fromkeys(tickers))  # preserve order, remove duplicates
    total = len(tickers)
    logger.info("compute_scores_start", extra={"total": total})

    sem = asyncio.Semaphore(concurrency)
    tasks = [asyncio.create_task(_worker(t, sem, results)) for t in tickers]

    # run tasks, tolerate failures
    await asyncio.gather(*tasks)

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    summary = {
        "total": total,
        "succeeded": len(results["success"]),
        "failed": len(results["failed"]),
        "duration_ms": duration_ms,
        "failures": results["failed"],
    }

    logger.info("compute_scores_completed", extra=summary)
    return summary


def _parse_tickers(value: str) -> list[str]:
    return [t.strip().upper() for t in value.split(",") if t.strip()]


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch compute stock scores.")
    parser.add_argument("--tickers", help="Comma-separated list of tickers to process (optional).")
    parser.add_argument("--concurrency", type=int, default=8, help="Number of concurrent workers.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    args = parser.parse_args(argv)

    _configure_logging(args.log_level)

    tickers = _parse_tickers(args.tickers) if args.tickers else None

    try:
        summary = asyncio.run(compute_scores(tickers=tickers, concurrency=args.concurrency))
        # print concise final summary
        print(f"Processed {summary['total']} tickers — succeeded={summary['succeeded']} failed={summary['failed']} duration_ms={summary['duration_ms']}")
        if summary["failed"]:
            print("Failures:")
            for f in summary["failures"]:
                print(f" - {f['ticker']}: {f.get('reason')} {f.get('error') or ''}")
        return 0
    except Exception as exc:  # pragma: no cover - top-level safety
        logger.exception("batch_run_failed", extra={"error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
