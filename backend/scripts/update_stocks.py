#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT))

from api.app.db.session import AsyncSessionFactory
from batch.app.services.financial_ingestion_service import FinancialIngestionService
from core.providers.financial.factory import create_default_financial_provider_registry


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Atualiza informações de ações em lote usando o provedor financeiro configurado."
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Lista de tickers para atualizar (ex: ITUB4 VALE3).",
    )
    parser.add_argument(
        "--tickers-file",
        type=Path,
        help="Arquivo de texto com um ticker por linha.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Número máximo de tickers processados em paralelo por lote.",
    )
    parser.add_argument(
        "--provider",
        default="yahoo_finance",
        help="Provedor financeiro a ser usado (default: yahoo_finance).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Número de tentativas de reexecução em caso de falha no provedor.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Timeout por chamada ao provedor, em segundos.",
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=365,
        help="Quantidade de dias de histórico de preços e dividendos a buscar.",
    )
    return parser.parse_args()


def load_tickers(args: argparse.Namespace) -> list[str]:
    tickers: list[str] = []

    if args.tickers_file:
        if not args.tickers_file.exists():
            raise FileNotFoundError(f"Arquivo de tickers não encontrado: {args.tickers_file}")
        tickers.extend(
            line.strip() for line in args.tickers_file.read_text(encoding="utf-8").splitlines() if line.strip()
        )

    if args.tickers:
        tickers.extend(args.tickers)

    normalized = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    if not normalized:
        raise ValueError("Nenhum ticker informado. Use argumentos ou --tickers-file.")
    return normalized


def print_progress(completed: int, total: int) -> None:
    width = 40
    filled = int(width * completed / total)
    bar = "#" * filled + "." * (width - filled)
    print(f"\r[{bar}] {completed}/{total} concluídos", end="", flush=True)


async def process_ticker(
    ticker: str,
    provider_name: str,
    retries: int,
    timeout_seconds: int,
    history_start_date: date,
    history_end_date: date,
) -> tuple[str, bool, str | None]:
    provider = create_default_financial_provider_registry().create(provider_name)
    async with AsyncSessionFactory() as session:
        service = FinancialIngestionService(
            session=session,
            provider=provider,
            retries=retries,
            timeout_seconds=timeout_seconds,
        )
        try:
            await service.ingest_ticker(
                ticker=ticker,
                history_start_date=history_start_date,
                history_end_date=history_end_date,
            )
            return ticker, True, None
        except Exception as exc:
            logging.error("Falha ao processar %s: %s", ticker, exc)
            return ticker, False, str(exc)


async def run_batch(
    tickers: list[str],
    batch_size: int,
    provider_name: str,
    retries: int,
    timeout_seconds: int,
    history_days: int,
) -> tuple[list[str], dict[str, str]]:
    total = len(tickers)
    completed = 0
    successes: list[str] = []
    failures: dict[str, str] = {}

    history_end_date = datetime.utcnow().date()
    history_start_date = history_end_date - timedelta(days=history_days)

    for offset in range(0, total, batch_size):
        batch = tickers[offset : offset + batch_size]
        logging.info("Iniciando lote %d/%d: %s", offset // batch_size + 1, (total + batch_size - 1) // batch_size, ", ".join(batch))

        tasks = [process_ticker(ticker, provider_name, retries, timeout_seconds, history_start_date, history_end_date) for ticker in batch]
        for coro in asyncio.as_completed(tasks):
            ticker, success, error = await coro
            completed += 1
            print_progress(completed, total)
            if success:
                successes.append(ticker)
                logging.info("Ticker atualizado com sucesso: %s", ticker)
            else:
                failures[ticker] = error or "erro desconhecido"
                logging.warning("Ticker falhou: %s", ticker)
        print()

    logging.info(
        "Atualização de ações finalizada. Sucesso=%d Falhas=%d",
        len(successes),
        len(failures),
    )
    return successes, failures


def main() -> int:
    configure_logging()
    args = parse_arguments()

    try:
        tickers = load_tickers(args)
    except Exception as exc:
        logging.error("Erro ao carregar tickers: %s", exc)
        return 1

    logging.info("Iniciando atualização para %d tickers", len(tickers))

    if args.batch_size < 1:
        logging.error("batch-size deve ser maior que zero")
        return 1

    try:
        successes, failures = asyncio.run(
            run_batch(
                tickers=tickers,
                batch_size=args.batch_size,
                provider_name=args.provider,
                retries=args.retries,
                timeout_seconds=args.timeout_seconds,
                history_days=args.history_days,
            )
        )
    except Exception as exc:
        logging.exception("Execução interrompida por erro inesperado")
        return 1

    logging.info("Resumo: %d tickers atualizados, %d falhas", len(successes), len(failures))
    if failures:
        logging.warning("Falhas: %s", failures)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
