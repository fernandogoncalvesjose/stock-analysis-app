from apscheduler.schedulers.asyncio import AsyncIOScheduler

from batch.app.jobs.nightly_pipeline import NightlyPipeline


def create_scheduler(timezone: str = "America/Sao_Paulo") -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(NightlyPipeline().run, "cron", hour=2, minute=0, id="nightly_pipeline")
    return scheduler
