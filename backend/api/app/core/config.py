from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Stock Analysis API"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    debug: bool = False
    enable_docs: bool = True
    api_prefix: str = "/api/v1"

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/stock_analysis"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout_seconds: int = 30

    openai_api_key: str | None = None
    enable_live_llm: bool = False

    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    log_json: bool = True
    sentry_dsn: AnyUrl | None = None

    request_timeout_seconds: int = 30
    nightly_batch_timezone: str = "America/Sao_Paulo"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("enable_docs")
    @classmethod
    def disable_docs_in_production(cls, value: bool, info) -> bool:
        environment = info.data.get("environment")
        if environment == "production":
            return False if value is True else value
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
