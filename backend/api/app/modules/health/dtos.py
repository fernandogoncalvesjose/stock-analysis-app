from datetime import datetime
from typing import Literal

from pydantic import BaseModel


HealthStatus = Literal["ok", "degraded", "down"]


class HealthCheckDTO(BaseModel):
    status: HealthStatus
    app: str
    version: str
    environment: str
    timestamp: datetime
    checks: dict[str, HealthStatus]
