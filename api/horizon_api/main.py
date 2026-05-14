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
        "HORIZON — hantavirus outbreak surveillance with audit-grade source qualification. "
        "65+ sources. Public read-only. UK GDPR Art 6 lawful basis: legitimate interests "
        "(public health information). Not medical advice.\n\n"
        "**Unique data:** Oxford Kraemer Lab individual-level MV Hondius ANDV line list "
        "(Dr Moritz Kraemer / Oxford, Sam Scarpino, Andrew Rambaut / Edinburgh-Nextstrain). "
        "28-column per-person resolution — symptom onset, outcome, nationality, treatment, "
        "Pathoplexus accession IDs. CC0. Cross-referenced WHO DON600 + national health "
        "authority press releases for every row. "
        "Also: full Orthohantavirus NCBI RefSeq reference genome set "
        "(HantaNet, CDC Molecular Epidemiology, PMC10675615) — S/M/L segments, all major "
        "serotypes, permanent genomic annotation layer.\n\n"
        "**MeSH descriptors:** "
        "D006362 Hantavirus Infections | "
        "D018353 Hantavirus Pulmonary Syndrome | "
        "D006484 Hemorrhagic Fever with Renal Syndrome | "
        "D004813 Epidemiologic Monitoring | "
        "D016097 Virus Diseases — surveillance.\n\n"
        "**ICD-10:** A98.5 Haemorrhagic fever with renal syndrome | "
        "B33.4 Hantavirus (cardio-)pulmonary syndrome.\n\n"
        "**License:** CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/\n\n"
        "**Cite:** https://hantavirus.software/CITATION.cff"
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
    # OWASP hardening
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=63072000"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    # Open data attribution -- required by CC BY 4.0 and institutional
    # data governance processes at WHO, CDC, and academic repositories.
    response.headers["X-Data-License"] = "CC-BY-4.0"
    response.headers["X-Data-License-URL"] = "https://creativecommons.org/licenses/by/4.0/"
    response.headers["X-Attribution"] = "HORIZON Hantavirus Surveillance Platform, 79th Unit Limited"
    response.headers["X-Attribution-URL"] = "https://hantavirus.software/"
    return response


app.include_router(meta.router)
app.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["clusters"])
app.include_router(incidents.router)
app.include_router(events.router, prefix="/api/v1/stream", tags=["stream"])
app.include_router(seo.router)
