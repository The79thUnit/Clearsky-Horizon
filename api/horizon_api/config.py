"""Environment-driven settings for the API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    log_level: str
    cors_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    testing: bool

    @classmethod
    def from_env(cls) -> Settings:
        raw_origins = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173")
        # TRUSTED_HOSTS: comma-separated list of allowed Host header values.
        # Defaults to wildcard ("*") for local dev; production .env sets
        # the canonical hostnames. The starlette TrustedHostMiddleware rejects
        # requests with a Host header not in this list (HTTP 400).
        raw_hosts = os.environ.get(
            "TRUSTED_HOSTS",
            "localhost,127.0.0.1,0.0.0.0",
        )
        return cls(
            database_url=os.environ.get(
                "DATABASE_URL",
                "postgresql://horizon:changeme_local_only@postgres:5432/horizon",
            ).replace("postgresql+asyncpg://", "postgresql://"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            cors_origins=tuple(o.strip() for o in raw_origins.split(",") if o.strip()),
            trusted_hosts=tuple(h.strip() for h in raw_hosts.split(",") if h.strip()),
            testing=os.environ.get("HORIZON_TESTING", "").lower() in {"1", "true", "yes"},
        )


settings = Settings.from_env()
