from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory
from app.modules.health.dtos import HealthCheckDTO, HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckDTO)
async def health_check() -> HealthCheckDTO:
    settings = get_settings()
    checks: dict[str, HealthStatus] = {"api": "ok", "database": "ok"}

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "down"

    status: HealthStatus = "ok" if all(value == "ok" for value in checks.values()) else "degraded"

    return HealthCheckDTO(
        status=status,
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        checks=checks,
    )
