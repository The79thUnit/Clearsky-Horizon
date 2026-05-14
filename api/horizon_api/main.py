"""HORIZON API entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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
        "**Cite:** https://hantavirus.software/CITATION.cff\n\n"
        "**Citation (CSL-JSON):** https://hantavirus.software/api/v1/meta/citation\n\n"
        "**Bulk export (NDJSON, streaming):** "
        "https://hantavirus.software/api/v1/cases/bulk/ndjson\n\n"
        "**Source registry:** https://hantavirus.software/api/v1/sources\n\n"
        "**Methodology:** https://hantavirus.software/methodology"
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "79th Unit Limited",
        "url": "https://hantavirus.software/methodology",
        "email": "info@79thunit.co.uk",
    },
    license_info={
        "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    terms_of_service="https://hantavirus.software/methodology",
    openapi_tags=[
        {
            "name": "cases",
            "description": "Individual case reports ingested from 65+ sources. "
                           "Each record carries NATO Admiralty Scale qualification and "
                           "Berkeley Protocol SHA-256 chain-of-custody hash.",
            "externalDocs": {
                "description": "Methodology and source qualification",
                "url": "https://hantavirus.software/methodology",
            },
        },
        {
            "name": "sources",
            "description": "Registry of all 65+ ingestion sources with NATO Admiralty "
                           "Scale reliability and credibility ratings.",
        },
        {
            "name": "clusters",
            "description": "Aggregated outbreak clusters grouping related case reports "
                           "by geographic proximity, serotype, and time window.",
        },
        {
            "name": "stream",
            "description": "Chronological event feed — de-duplicated by content topic hash, "
                           "newest-first. Suitable for RSS-equivalent integration.",
        },
        {
            "name": "meta",
            "description": "Global counters, controlled vocabulary (MeSH / ICD-10 / "
                           "serotypes), and bibliographic citation in CSL-JSON format.",
            "externalDocs": {
                "description": "CITATION.cff",
                "url": "https://hantavirus.software/CITATION.cff",
            },
        },
    ],
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
    # Linked Data / academic discovery headers.
    # RFC 8288 Link headers let institutional harvesters (OpenAIRE, DataCite,
    # Europe PMC, HealthDCAT-AP) auto-discover machine-readable metadata
    # without parsing HTML.  Added to all responses so they're visible on
    # API endpoints, HTML pages, and static assets alike.
    content_type = response.headers.get("content-type", "")
    link_parts = [
        '<https://hantavirus.software/api/v1/meta/dcat>; rel="describedby"; type="application/ld+json"',
        '<https://hantavirus.software/api/v1/meta/citation>; rel="cite-as"; type="application/vnd.citationstyles.csl+json"',
        '<https://hantavirus.software/CITATION.cff>; rel="describedby"; type="text/yaml"',
    ]
    if "text/html" in content_type:
        # Canonical entity link for knowledge-graph crawlers (Google, Bing,
        # Wikidata). Only on HTML responses to avoid confusing API clients.
        link_parts.append(
            '<https://hantavirus.software/#dataset>; rel="canonical"'
        )
    existing_link = response.headers.get("link", "")
    new_link = ", ".join(link_parts)
    response.headers["Link"] = f"{existing_link}, {new_link}".lstrip(", ") if existing_link else new_link
    return response


app.include_router(meta.router)
app.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["clusters"])
app.include_router(incidents.router)
app.include_router(events.router, prefix="/api/v1/stream", tags=["stream"])
app.include_router(seo.router)


def _custom_openapi() -> dict[str, Any]:
    """Extend the standard OpenAPI schema with APIs.guru and academic extensions."""
    if app.openapi_schema:
        return app.openapi_schema  # type: ignore[return-value]
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        contact=app.contact,  # type: ignore[arg-type]
        license_info=app.license_info,  # type: ignore[arg-type]
        terms_of_service=app.terms_of_service,
        openapi_version="3.1.0",
        tags=app.openapi_tags,
        routes=app.routes,
        servers=[{"url": "https://hantavirus.software", "description": "Production"}],
    )
    # APIs.guru extension: logo shown in their API catalogue and in ReDoc.
    schema["info"]["x-logo"] = {
        "url": "https://hantavirus.software/og-image.png",
        "altText": "HORIZON Hantavirus Surveillance Platform",
    }
    # Data provenance extension for academic / institutional harvesters
    # (HealthDCAT-AP, Europe PMC connector, OpenAIRE).
    schema["info"]["x-data-provenance"] = {
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "citation": "https://hantavirus.software/CITATION.cff",
        "citation_csl_json": "https://hantavirus.software/api/v1/meta/citation",
        "bulk_export_ndjson": "https://hantavirus.software/api/v1/cases/bulk/ndjson",
        "methodology": "https://hantavirus.software/methodology",
        "source_count": 65,
        "unique_datasets": [
            "Oxford Kraemer Lab MV Hondius ANDV individual line list (CC0, github.com/kraemer-lab/Hondius_hantavirus_h2026)",
            "NCBI RefSeq Orthohantavirus reference genome set / HantaNet (CDC, PMC10675615)",
        ],
        "qualification_standard": "NATO Admiralty Scale — STANAG 2511",
        "chain_of_custody": "Berkeley Protocol SHA-256 content hash",
        "mesh": ["D006362", "D018353", "D006484", "D004813", "D016097"],
        "icd10": ["A98.5", "B33.4"],
    }
    # ExternalDocs at root level — ReDoc renders this as a prominent button.
    schema["externalDocs"] = {
        "description": "Methodology, source qualification, and data documentation",
        "url": "https://hantavirus.software/methodology",
    }
    app.openapi_schema = schema
    return schema  # type: ignore[return-value]


app.openapi = _custom_openapi  # type: ignore[method-assign]
