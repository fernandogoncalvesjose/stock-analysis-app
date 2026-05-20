import argparse
import asyncio
from datetime import UTC, date, datetime

from batch.app.bootstrap import configure_batch_pythonpath

configure_batch_pythonpath()

from batch.app.jobs.nightly_pipeline import NightlyPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run stock analysis batch jobs.")
    parser.add_argument(
        "--reference-date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date(),
        help="Reference date in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(NightlyPipeline().run(args.reference_date))
