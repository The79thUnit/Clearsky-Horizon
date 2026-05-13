"""Environment-driven settings for the worker."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    celery_broker_url: str
    celery_result_backend: str
    user_agent: str
    promed_interval_minutes: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.environ.get(
                "DATABASE_URL_SYNC",
                "postgresql://horizon:changeme_local_only@postgres:5432/horizon",
            ).replace("postgresql+psycopg://", "postgresql://"),
            celery_broker_url=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1"),
            celery_result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
            user_agent=os.environ.get("HORIZON_USER_AGENT", "HORIZON/0.1"),
            promed_interval_minutes=int(
                os.environ.get("CELERY_BEAT_SCHEDULE_PROMED_MINUTES", "15")
            ),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


settings = Settings.from_env()
