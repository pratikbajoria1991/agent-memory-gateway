from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AMG_", env_file=".env", extra="ignore")

    backend: Literal["sqlite", "redis"] = "sqlite"
    sqlite_path: str = ":memory:"
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "amg"

    otel_enabled: bool = False
    otel_service_name: str = "agent-memory-gateway"


@lru_cache
def get_settings() -> Settings:
    return Settings()