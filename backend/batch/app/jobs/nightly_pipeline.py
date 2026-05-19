from datetime import date
from time import perf_counter

import logging

logger = logging.getLogger(__name__)


class NightlyPipeline:
    steps = (
        "sync_tickers",
        "ingest_metrics",
        "compute_scores",
        "ingest_news",
        "generate_ai_narratives",
        "publish_snapshots",
    )

    async def run(self, reference_date: date) -> None:
        started_at = perf_counter()
        logger.info("nightly_pipeline_started", extra={"reference_date": str(reference_date)})

        for step in self.steps:
            step_started_at = perf_counter()
            await self.run_step(step, reference_date)
            logger.info(
                "nightly_pipeline_step_completed",
                extra={
                    "step": step,
                    "reference_date": str(reference_date),
                    "duration_ms": round((perf_counter() - step_started_at) * 1000, 2),
                },
            )

        logger.info(
            "nightly_pipeline_completed",
            extra={
                "reference_date": str(reference_date),
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )

    async def run_step(self, step: str, reference_date: date) -> None:
        # Placeholder intentionally idempotent. Real implementations should upsert by reference_date.
        _ = (step, reference_date)
