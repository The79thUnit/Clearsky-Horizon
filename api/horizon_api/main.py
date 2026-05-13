"""HORIZON API entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp

from . import __version__
from .config import settings
from .db import close_pool, init_pool
from .routers import cases, clusters, events, incidents, meta, seo, sources

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_pool()
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(
    title="HORIZON API",
    version=__version__,
    description=(
        "HORIZON - hantavirus surveillance with audit-grade source qualification. "
        "Public read-only. UK GDPR Art 6 lawful basis: legitimate interests "
        "(public health information). Not medical advice."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# OWASP API7: Host header injection defence. Requests with a Host header not
# in TRUSTED_HOSTS are rejected with HTTP 400 before they reach any handler.
# In production, TRUSTED_HOSTS is set to the canonical domain(s) in .env.production.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(settings.trusted_hosts),
)

# OWASP API8: strict CORS allowlist; never wildcard in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["accept", "content-type"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def security_headers(request: Request, call_next: ASGIApp) -> Response:
    response: Response = await call_next(request)  # type: ignore[misc, assignment]
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=63072000"
    return response


app.include_router(meta.router)
app.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["clusters"])
app.include_router(incidents.router)
app.include_router(events.router, prefix="/api/v1/stream", tags=["stream"])
app.include_router(seo.router)
