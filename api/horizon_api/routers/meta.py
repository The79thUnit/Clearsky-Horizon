"""Meta endpoints: /health, /api/v1/meta/stats, /api/v1/meta/citation."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, RedirectResponse

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


_WELL_KNOWN_DATASET = {
    "name": "HORIZON Hantavirus Surveillance Dataset",
    "url": "https://hantavirus.software/",
    "dcat": "https://hantavirus.software/api/v1/meta/dcat",
    "citation_csl": "https://hantavirus.software/api/v1/meta/citation",
    "citation_cff": "https://hantavirus.software/CITATION.cff",
    "openapi": "https://hantavirus.software/api/openapi.json",
    "bulk_export": "https://hantavirus.software/api/v1/cases/bulk/ndjson",
    "methodology": "https://hantavirus.software/methodology",
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "publisher": "79th Unit Limited",
    "publisher_url": "https://79thunit.co.uk",
    "contact": "info@79thunit.co.uk",
    "doi": "10.5281/zenodo.PENDING",
}


@router.get(
    "/.well-known/dataset",
    summary="Machine-readable dataset discovery (RFC 8615 well-known URI)",
    include_in_schema=False,
)
async def well_known_dataset() -> JSONResponse:
    """Well-known dataset discovery endpoint following RFC 8615.

    Returns a compact JSON summary of all machine-readable access points
    for the HORIZON dataset. Indexed by OpenAIRE, DataCite, and institutional
    harvester bots that probe /.well-known/ before crawling the full site.
    """
    return JSONResponse(
        content=_WELL_KNOWN_DATASET,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=86400", "Access-Control-Allow-Origin": "*"},
    )


@router.get(
    "/.well-known/void",
    summary="VoID dataset descriptor redirect (Linked Data discovery)",
    include_in_schema=False,
)
async def well_known_void() -> RedirectResponse:
    """Redirect /.well-known/void to the DCAT-AP JSON-LD endpoint.

    VoID (Vocabulary of Interlinked Datasets) discovery bots probe this URL.
    We redirect to our full DCAT-AP descriptor which is a superset of VoID.
    """
    return RedirectResponse(
        url="/api/v1/meta/dcat",
        status_code=303,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get(
    "/api/v1/meta/badge/sources",
    summary="Shield.io endpoint badge: active source count",
    include_in_schema=False,
)
async def badge_sources() -> JSONResponse:
    """Returns a shields.io endpoint-badge JSON for the active source count.

    Embed in GitHub READMEs and research papers::

        ![Sources](https://img.shields.io/endpoint?url=https://hantavirus.software/api/v1/meta/badge/sources)
    """
    async with acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*)::int AS n FROM sources WHERE enabled")
    count = row["n"] if row else 0
    return JSONResponse(
        content={
            "schemaVersion": 1,
            "label": "sources",
            "message": str(count),
            "color": "informational",
            "style": "flat",
        },
        headers={"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"},
    )


@router.get(
    "/api/v1/meta/badge/cases",
    summary="Shield.io endpoint badge: total ingested reports",
    include_in_schema=False,
)
async def badge_cases() -> JSONResponse:
    """Returns a shields.io endpoint-badge JSON for total ingested case reports.

    Embed in GitHub READMEs::

        ![Reports](https://img.shields.io/endpoint?url=https://hantavirus.software/api/v1/meta/badge/cases)
    """
    async with acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*)::int AS n FROM case_reports")
    count = row["n"] if row else 0
    label = f"{count:,}" if count >= 1000 else str(count)
    return JSONResponse(
        content={
            "schemaVersion": 1,
            "label": "reports ingested",
            "message": label,
            "color": "success",
            "style": "flat",
        },
        headers={"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"},
    )


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


_DCAT_AP = {
    "@context": {
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "schema": "https://schema.org/",
        "vcard": "http://www.w3.org/2006/vcard/ns#",
        "healthdcat": "http://healthdcat-ap.eu/",
    },
    "@type": "dcat:Dataset",
    "@id": "https://hantavirus.software/#dataset",
    "dct:title": [
        {"@language": "en", "@value": "HORIZON: Real-Time Hantavirus Outbreak Surveillance Dataset"},
        {"@language": "es", "@value": "HORIZON: Conjunto de datos de vigilancia de brotes de hantavirus en tiempo real"},
        {"@language": "pt", "@value": "HORIZON: Conjunto de dados de vigilância de surtos de hantavírus em tempo real"},
    ],
    "dct:description": [
        {
            "@language": "en",
            "@value": (
                "Open dataset of hantavirus outbreak case reports aggregated from 65+ "
                "authoritative sources: WHO Disease Outbreak News, US CDC Health Alert "
                "Network (HAN), ECDC Communicable Disease Threats Report, PAHO "
                "Epidemiological Alerts, ProMED-mail, THL Finland, national health "
                "ministries (Argentina, Chile, Brazil), wire services (Reuters, AP, "
                "AFP, BBC, EFE, Mercopress), peer-reviewed literature (Europe PMC, "
                "bioRxiv, medRxiv, Crossref, arXiv), and ecological indicators (NOAA "
                "ENSO, NASA MODIS NDVI). Includes the Oxford Kraemer Lab MV Hondius "
                "individual-level ANDV line list (CC0) and the NCBI RefSeq "
                "Orthohantavirus reference genome set (HantaNet, CDC). Every record "
                "carries NATO Admiralty Scale dual-axis source qualification, Berkeley "
                "Protocol SHA-256 chain-of-custody hash, and a dual confidence model."
            ),
        }
    ],
    "dct:publisher": {
        "@type": "foaf:Organization",
        "foaf:name": "79th Unit Limited",
        "foaf:homepage": {"@id": "https://79thunit.co.uk"},
    },
    "dct:creator": {"@id": "https://hantavirus.software/#org"},
    "dct:issued": {"@type": "xsd:date", "@value": "2026-04-17"},
    "dct:modified": {"@type": "xsd:date", "@value": "2026-05-14"},
    "dct:language": [
        {"@id": "http://publications.europa.eu/resource/authority/language/ENG"},
        {"@id": "http://publications.europa.eu/resource/authority/language/SPA"},
        {"@id": "http://publications.europa.eu/resource/authority/language/POR"},
    ],
    "dct:license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
    "dct:rights": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
    "dct:accessRights": {"@id": "http://publications.europa.eu/resource/authority/access-right/PUBLIC"},
    "dct:spatial": {"@id": "http://www.geonames.org/6295630"},
    "dct:temporal": {
        "@type": "dct:PeriodOfTime",
        "schema:startDate": {"@type": "xsd:date", "@value": "1993-01-01"},
    },
    "dct:subject": [
        {"@id": "http://id.loc.gov/authorities/subjects/sh85059518"},
        {"@id": "https://meshb.nlm.nih.gov/record/ui?ui=D006362"},
        {"@id": "https://meshb.nlm.nih.gov/record/ui?ui=D018353"},
        {"@id": "https://meshb.nlm.nih.gov/record/ui?ui=D006484"},
    ],
    "dcat:theme": [
        {"@id": "http://publications.europa.eu/resource/authority/data-theme/HEAL"},
        {"@id": "http://publications.europa.eu/resource/authority/data-theme/SCIE"},
    ],
    "dcat:keyword": [
        "hantavirus", "Orthohantavirus", "outbreak surveillance", "epidemiology",
        "Andes virus", "Sin Nombre virus", "Puumala virus", "Hantaan virus",
        "MV Hondius", "HPS", "HFRS", "open data", "CC BY 4.0",
        "Oxford Kraemer Lab", "HantaNet", "NCBI RefSeq",
    ],
    "dcat:landingPage": {"@id": "https://hantavirus.software/"},
    "dcat:distribution": [
        {
            "@type": "dcat:Distribution",
            "dct:title": {"@language": "en", "@value": "Case reports JSON API"},
            "dcat:accessURL": {"@id": "https://hantavirus.software/api/v1/cases"},
            "dcat:mediaType": {"@id": "https://www.iana.org/assignments/media-types/application/json"},
            "dct:license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
        },
        {
            "@type": "dcat:Distribution",
            "dct:title": {"@language": "en", "@value": "Bulk NDJSON streaming export"},
            "dcat:accessURL": {"@id": "https://hantavirus.software/api/v1/cases/bulk/ndjson"},
            "dcat:mediaType": {"@id": "https://www.iana.org/assignments/media-types/application/x-ndjson"},
            "dct:license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
        },
        {
            "@type": "dcat:Distribution",
            "dct:title": {"@language": "en", "@value": "OpenAPI specification"},
            "dcat:accessURL": {"@id": "https://hantavirus.software/api/openapi.json"},
            "dcat:mediaType": {"@id": "https://www.iana.org/assignments/media-types/application/json"},
        },
    ],
    "dcat:contactPoint": {
        "@type": "vcard:Organization",
        "vcard:fn": "79th Unit Limited",
        "vcard:hasEmail": {"@id": "mailto:info@79thunit.co.uk"},
        "vcard:hasURL": {"@id": "https://hantavirus.software/methodology"},
    },
    "dct:conformsTo": {"@id": "https://bioschemas.org/profiles/Dataset/1.1-RELEASE"},
}


@router.get(
    "/api/v1/meta/dcat",
    summary="DCAT-AP 3.0 JSON-LD dataset descriptor (EU open data portal standard)",
    tags=["meta"],
    response_model=None,
)
async def dcat() -> JSONResponse:
    """Returns DCAT-AP 3.0 compliant JSON-LD describing the HORIZON dataset.

    Compatible with the EU Open Data Portal (data.europa.eu), data.gov.uk,
    European Health Data Space (HealthDCAT-AP), OpenAIRE, and any catalogue
    that harvests DCAT. The ``Content-Type`` is set to
    ``application/ld+json`` for automatic detection.

    Catalogue submitters: submit this URL to data.europa.eu/data/datasets/suggest
    or to your national data portal's DCAT harvester. The endpoint returns a
    valid DCAT-AP Dataset description with distributions, publisher, licence,
    temporal coverage, and subject classification.
    """
    return JSONResponse(
        content=_DCAT_AP,
        media_type="application/ld+json",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Link": '<https://hantavirus.software/#dataset>; rel="canonical"',
        },
    )


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


_CSL_JSON = {
    "id": "horizon-hantavirus-dataset",
    "type": "dataset",
    "title": "HORIZON: Real-Time Hantavirus Outbreak Surveillance Dataset",
    "abstract": (
        "Open dataset of hantavirus outbreak case reports aggregated from 65+ "
        "authoritative sources: WHO Disease Outbreak News, US CDC Health Alert "
        "Network (HAN), ECDC Communicable Disease Threats Report, PAHO "
        "Epidemiological Alerts, ProMED-mail, THL Finland, national health "
        "ministries (Argentina, Chile, Brazil), wire services (Reuters, AP, "
        "AFP, BBC, EFE, Mercopress), and peer-reviewed literature (Europe PMC, "
        "bioRxiv, medRxiv, Crossref, arXiv). Includes the Oxford Kraemer Lab "
        "MV Hondius individual-level ANDV line list (CC0, Dr Moritz Kraemer / "
        "Oxford, Sam Scarpino, Andrew Rambaut / Edinburgh-Nextstrain) and the "
        "NCBI RefSeq Orthohantavirus reference genome set (HantaNet, CDC "
        "Molecular Epidemiology, PMC10675615). Every record carries NATO "
        "Admiralty Scale dual-confidence source qualification and Berkeley "
        "Protocol SHA-256 chain-of-custody hash."
    ),
    "author": [
        {"literal": "79th Unit Limited"}
    ],
    "issued": {"date-parts": [[2026, 4, 17]]},
    "publisher": "79th Unit Limited",
    "URL": "https://hantavirus.software/",
    "version": __version__,
    "keyword": [
        "hantavirus", "Orthohantavirus", "Andes virus", "ANDV",
        "Sin Nombre virus", "SNV", "Puumala virus", "hantavirus pulmonary syndrome",
        "haemorrhagic fever with renal syndrome", "HPS", "HFRS",
        "outbreak surveillance", "epidemiology", "open data", "CC BY 4.0",
        "MV Hondius", "MV Hondius 2026", "Oxford Kraemer Lab",
        "HantaNet", "NCBI RefSeq", "NATO Admiralty Scale",
        "Berkeley Protocol", "dual confidence model",
        "MeSH:D006362", "MeSH:D018353", "ICD-10:A98.5", "ICD-10:B33.4",
    ],
    "note": (
        "Data available under Creative Commons Attribution 4.0 International "
        "(CC BY 4.0). Bulk NDJSON export: "
        "https://hantavirus.software/api/v1/cases/bulk/ndjson. "
        "OpenAPI: https://hantavirus.software/api/openapi.json. "
        "CITATION.cff: https://hantavirus.software/CITATION.cff."
    ),
    "DOI": "10.5281/zenodo.PENDING",
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "genre": "Dataset",
    "dimensions": "65+ ingestion sources, global coverage, 1993-present",
}


@router.get(
    "/api/v1/meta/citation",
    summary="Bibliographic citation in CSL-JSON format (Zotero / Mendeley / Paperpile compatible)",
    tags=["meta"],
    response_model=None,
)
async def citation() -> JSONResponse:
    """Returns the HORIZON dataset citation as a CSL-JSON object.

    Compatible with Zotero, Mendeley, Paperpile, JabRef, and any application
    that can import CSL-JSON citations. The ``Content-Type`` header is set to
    ``application/vnd.citationstyles.csl+json`` so reference managers
    auto-detect the format.

    The Zotero translator will fire on this endpoint if the URL is submitted
    via the Zotero Connector browser extension. See also:
    https://hantavirus.software/CITATION.cff (CFF format)
    """
    return JSONResponse(
        content=_CSL_JSON,
        media_type="application/vnd.citationstyles.csl+json",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


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
