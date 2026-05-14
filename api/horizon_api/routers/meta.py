"""Meta endpoints: /health and /api/v1/meta/stats (global counters)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .. import __version__
from ..config import settings
from ..db import acquire
from ..schemas import (
    BreakdownEntry,
    EventList,
    EventRecord,
    HealthResponse,
    StatsResponse,
)

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


# Counter query. The authoritative case numbers come from
# incident_authoritative_counts (one row per incident-source-time snapshot;
# we use the LATEST one per incident from the HIGHEST-NATO source). The
# report counters come from case_reports (ingested articles).
_QUERY_COUNTERS = """
WITH latest_count_per_incident AS (
    SELECT DISTINCT ON (iac.incident_id)
        iac.incident_id,
        iac.confirmed_cases,
        iac.suspected_cases,
        iac.deaths,
        iac.recovered,
        iac.reported_at,
        iac.source_id
    FROM incident_authoritative_counts iac
    JOIN incidents i ON i.id = iac.incident_id
    WHERE i.status IN ('active', 'monitoring')
    ORDER BY
        iac.incident_id,
        iac.nato_reliability ASC,
        iac.nato_credibility ASC,
        iac.reported_at DESC
)
SELECT
    COALESCE((SELECT SUM(confirmed_cases)::int FROM latest_count_per_incident), 0)
        AS total_confirmed_cases_authoritative,
    COALESCE((SELECT SUM(suspected_cases)::int FROM latest_count_per_incident), 0)
        AS total_suspected_cases_authoritative,
    COALESCE((SELECT SUM(deaths)::int FROM latest_count_per_incident), 0)
        AS total_deaths_authoritative,
    (SELECT COUNT(*)::int FROM incidents WHERE status IN ('active','monitoring'))
        AS total_active_incidents,
    (SELECT COUNT(*)::int FROM case_reports)
        AS total_reports_ingested,
    (SELECT COUNT(DISTINCT country_iso2)::int
        FROM case_reports WHERE country_iso2 IS NOT NULL)
        AS total_countries_in_reports,
    (SELECT COUNT(*)::int FROM clusters WHERE status = 'active')
        AS total_clusters_active,
    (SELECT COUNT(DISTINCT serotype_id)::int
        FROM case_reports WHERE serotype_id IS NOT NULL)
        AS total_serotypes_seen,
    (SELECT COUNT(*)::int FROM sources WHERE enabled)
        AS total_sources_enabled,
    (SELECT COUNT(*)::int FROM case_reports
        WHERE ingested_at >= NOW() - INTERVAL '24 hours')
        AS reports_last_24h,
    (SELECT COUNT(*)::int FROM case_reports
        WHERE ingested_at >= NOW() - INTERVAL '7 days')
        AS reports_last_7d,
    (SELECT COUNT(*)::int FROM case_reports
        WHERE ingested_at >= NOW() - INTERVAL '14 days')
        AS reports_last_14d
"""

_QUERY_BY_SEROTYPE = """
SELECT
    COALESCE(s.code, cr.serotype_text, 'unknown') AS label,
    COUNT(*)::int                                  AS count
FROM case_reports cr
LEFT JOIN serotypes s ON s.id = cr.serotype_id
GROUP BY 1
ORDER BY count DESC
LIMIT 10
"""

_QUERY_BY_COUNTRY = """
SELECT
    country_iso2  AS label,
    COUNT(*)::int AS count
FROM case_reports
WHERE country_iso2 IS NOT NULL
GROUP BY 1
ORDER BY count DESC
LIMIT 10
"""


@router.get(
    "/api/v1/meta/stats",
    response_model=StatsResponse,
    summary="Global counters: authoritative cases (from WHO/CDC) + ingestion telemetry",
)
async def stats() -> StatsResponse:
    async with acquire() as conn:
        counters = await conn.fetchrow(_QUERY_COUNTERS)
        by_serotype = await conn.fetch(_QUERY_BY_SEROTYPE)
        by_country = await conn.fetch(_QUERY_BY_COUNTRY)

    data = dict(counters) if counters else {}
    data["by_serotype"] = [BreakdownEntry(**dict(r)) for r in by_serotype]
    data["by_country"] = [BreakdownEntry(**dict(r)) for r in by_country]
    return StatsResponse.model_validate(data)


# Events feed: hard-filtered to the active outbreak window and de-duplicated
# by topic hash so multi-source coverage of one news event collapses to one
# row. Strict chronological ordering (newest first).
_QUERY_EVENTS = """
WITH ranked AS (
    SELECT
        cr.id,
        cr.reported_date,
        cr.ingested_at,
        cr.title,
        cr.summary,
        cr.country_iso2,
        cr.raw_url,
        cr.death_count,
        cr.serotype_id,
        cr.source_id,
        cr.content_topic_hash,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(cr.content_topic_hash, cr.id::text)
            ORDER BY
                CASE WHEN src.tier = 1 THEN 0 ELSE 1 END,
                COALESCE(cr.reported_date, cr.ingested_at::date) ASC
        ) AS rn
    FROM case_reports cr
    JOIN sources src ON src.id = cr.source_id
    WHERE
      -- Drop reports outside the active-outbreak window. The window start
      -- is controlled by EVENTS_WINDOW_START env var (default 2026-03-01)
      -- so it can be updated for future outbreaks without code changes.
      (
        cr.reported_date >= $2::date
        OR (cr.reported_date IS NULL AND cr.ingested_at >= ($2::date - INTERVAL '1 day')::timestamptz)
      )
      -- Drop SEO explainer pieces.
      AND NOT (LOWER(cr.title) ~ '(what is hantavirus|how worried|should i be worried|what comes next|symptoms you need|how it differs|everything you need to know|tell us:|inside the laboratory|hantavirus[: ]+the silent|hantavirus[: ]+the .* virus|hantavirus[: ]+how|hantavirus[: ]+what|jersey hantavirus risk|rapid reaction)')
      -- Drop annual epidemiological reports (historical ECDC/PAHO archive).
      AND NOT (LOWER(cr.title) ~ '(annual epidemiological report|annual report for 20\\d{2}|vol\\. \\d+, no\\. \\d+|epidemiological situation .* in (brazil|argentina|chile))')
      -- Drop stock-market / vaccine-investment chatter (off-topic noise).
      AND NOT (LOWER(cr.title) ~ '(stock surges|stock extends|biotech stocks|pharma stocks|vaccine.*stock|next frontier|moderna)')
      -- Drop opinion / advice columns that aren't outbreak events.
      AND NOT (LOWER(cr.title) ~ '(how to avoid|how to stay safe|what you need to know|could.*be the next|is hantavirus contagious|covid-era lockdowns)')
)
SELECT
    r.id::text                   AS id,
    COALESCE(r.reported_date, r.ingested_at::date) AS occurred_at,
    CASE
        WHEN r.death_count > 0 THEN 'fatality'
        ELSE 'case'
    END                          AS event_type,
    CASE
        WHEN r.death_count > 0 THEN 'critical'
        ELSE 'info'
    END                          AS severity,
    r.title,
    NULL::text                   AS summary,
    r.country_iso2,
    sero.code                    AS serotype_code,
    src.code                     AS source_code,
    r.raw_url                    AS source_url,
    NULL::text                   AS cluster_id
FROM ranked r
JOIN sources src             ON src.id = r.source_id
LEFT JOIN serotypes sero     ON sero.id = r.serotype_id
WHERE r.rn = 1
ORDER BY
    COALESCE(r.reported_date, r.ingested_at::date) DESC,
    r.ingested_at DESC
LIMIT $1
"""


_VOCABULARY: dict = {
    "mesh": [
        {"id": "D006362", "name": "Hantavirus Infections",
         "url": "https://meshb.nlm.nih.gov/record/ui?ui=D006362"},
        {"id": "D018353", "name": "Hantavirus Pulmonary Syndrome",
         "url": "https://meshb.nlm.nih.gov/record/ui?ui=D018353"},
        {"id": "D006484", "name": "Hemorrhagic Fever with Renal Syndrome",
         "url": "https://meshb.nlm.nih.gov/record/ui?ui=D006484"},
        {"id": "D004813", "name": "Epidemiologic Monitoring",
         "url": "https://meshb.nlm.nih.gov/record/ui?ui=D004813"},
        {"id": "D016097", "name": "Virus Diseases",
         "url": "https://meshb.nlm.nih.gov/record/ui?ui=D016097"},
    ],
    "icd10": [
        {"code": "A98.5",
         "name": "Haemorrhagic fever with renal syndrome",
         "syndromes": ["HFRS"],
         "serotypes": ["PUUV", "HTNV", "SEOV", "DOBV", "TULV", "SAAV"]},
        {"code": "B33.4",
         "name": "Hantavirus (cardio-)pulmonary syndrome",
         "syndromes": ["HPS"],
         "serotypes": ["ANDV", "SNV", "BAYV", "BCCV", "LANV", "CHOV"]},
    ],
    "source_qualification": {
        "reliability_scale": "NATO Admiralty Scale — STANAG 2511 (A–F)",
        "credibility_scale": "NATO Admiralty Scale — STANAG 2511 (1–6)",
        "independence_principle": (
            "Reliability and credibility are assessed independently. "
            "A source rated A (completely reliable) may still yield a 6 "
            "(truth cannot be judged) item if the content is unverifiable."
        ),
        "chain_of_custody": "Berkeley Protocol SHA-256 content hash",
        "methodology": "ICD 206 Source Reference Citation",
    },
    "serotypes": [
        {"code": "ANDV", "name": "Andes virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Oligoryzomys longicaudatus", "region": "South America"},
        {"code": "SNV", "name": "Sin Nombre virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Peromyscus maniculatus", "region": "North America"},
        {"code": "PUUV", "name": "Puumala virus",
         "icd10": "A98.5", "syndrome": "HFRS (NE)",
         "reservoir": "Myodes glareolus", "region": "Europe"},
        {"code": "HTNV", "name": "Hantaan virus",
         "icd10": "A98.5", "syndrome": "HFRS",
         "reservoir": "Apodemus agrarius", "region": "East Asia"},
        {"code": "SEOV", "name": "Seoul virus",
         "icd10": "A98.5", "syndrome": "HFRS (mild)",
         "reservoir": "Rattus norvegicus", "region": "Global"},
        {"code": "DOBV", "name": "Dobrava-Belgrade virus",
         "icd10": "A98.5", "syndrome": "HFRS",
         "reservoir": "Apodemus flavicollis", "region": "Balkans / Europe"},
        {"code": "BAYV", "name": "Bayou virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Oryzomys palustris", "region": "Southern USA"},
        {"code": "BCCV", "name": "Black Creek Canal virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Sigmodon hispidus", "region": "Florida, USA"},
        {"code": "LANV", "name": "Laguna Negra virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Calomys laucha", "region": "Paraguay, Bolivia"},
        {"code": "CHOV", "name": "Choclo virus",
         "icd10": "B33.4", "syndrome": "HPS",
         "reservoir": "Oligoryzomys fulvescens", "region": "Panama"},
        {"code": "SAAV", "name": "Saaremaa virus",
         "icd10": "A98.5", "syndrome": "HFRS (mild)",
         "reservoir": "Apodemus agrarius", "region": "Northern Europe"},
        {"code": "TULV", "name": "Tula virus",
         "icd10": "A98.5", "syndrome": "HFRS (mild / subclinical)",
         "reservoir": "Microtus arvalis", "region": "Central Europe"},
    ],
}


@router.get(
    "/api/v1/meta/vocabulary",
    summary="Controlled vocabulary: MeSH descriptors, ICD-10 codes, serotype registry",
    tags=["meta"],
    response_model=None,
)
async def vocabulary() -> dict:
    """Machine-readable controlled vocabulary for academic search engine indexing.

    Returns MeSH descriptors, ICD-10 codes, source-qualification methodology
    references, and the full serotype registry with reservoir and geographic
    context. Suitable for integration with ECDC TESSy, WHO EIOS pipelines,
    HealthDCAT-AP catalogues, and bibliographic systems (PubMed, Europe PMC).
    """
    return _VOCABULARY


@router.get(
    "/api/v1/meta/events",
    response_model=EventList,
    summary="Chronological feed of significant events in the last 30 days",
)
async def events(
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
) -> EventList:
    async with acquire() as conn:
        rows = await conn.fetch(_QUERY_EVENTS, limit, settings.events_window_start)
    items = [EventRecord.model_validate(dict(r)) for r in rows]
    return EventList(items=items, total=len(items))
