"""HORIZON SEO router.

Serves:

  * /sitemap.xml              — sitemap-index pointing at sub-sitemaps
  * /sitemap-main.xml         — static topic clusters
  * /sitemap-serotypes.xml    — per-serotype URLs
  * /sitemap-countries.xml    — per-country URLs
  * /sitemap-incidents.xml    — per-incident URLs
  * /sitemap-articles.xml     — per-article URLs (case_reports)
  * /news-sitemap.xml         — Google News format, last 48h

  * /rss.xml                  — RSS 2.0
  * /atom.xml                 — Atom 1.0
  * /feed.json                — JSON Feed 1.1

  * /hantavirus               — overview hub page (HTML)
  * /hantavirus/symptoms      — symptoms page (HTML)
  * /hantavirus/transmission  — transmission page (HTML)
  * /hantavirus/prevention    — prevention page (HTML)
  * /hantavirus/treatment     — treatment page (HTML)
  * /hantavirus/{slug}        — per-serotype page (HTML)
  * /outbreaks                — outbreaks hub (HTML)
  * /outbreaks/{slug}         — per-incident page (HTML)
  * /countries                — countries hub (HTML)
  * /countries/{iso}          — per-country page (HTML)
  * /articles                 — articles hub (HTML)
  * /articles/{id}            — per-article page (HTML)
  * /sources                  — source registry (HTML)
  * /methodology              — methodology (HTML)
  * /glossary                 — glossary (HTML)
  * /faq                      — FAQ (HTML)

All HTML responses are server-rendered, fully populated, and crawler-
friendly. They link to each other for internal PageRank flow and link
back to the live SPA via `/`.

Caching: HTML pages are cacheable for 5–30 min depending on freshness
expectations. Sitemaps and feeds are cacheable for 5 min. The
`Last-Modified` header is set to the actual data freshness time.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response as FastResponse

from ..db import acquire
from ..seo import content as seo_content
from ..seo import feeds, i18n, i18n_pt, jsonld, sitemaps
from ..seo.common import (
    BASE_URL,
    COUNTRY_NAMES,
    SEROTYPES,
    country_name,
    esc,
    iso_dt,
    serotype_by_code,
    serotype_by_slug,
)
from ..seo.html_shell import Breadcrumb, PageSpec, render_page

router = APIRouter(tags=["seo"])


# ---------------------------------------------------------------------------
# Caching helpers
# ---------------------------------------------------------------------------


def _cache_response(content: str, media_type: str, max_age: int = 300) -> Response:
    """Return a Response with strong caching + ETag + Last-Modified headers.

    Crawlers (Googlebot, Bingbot) honour ETag/304 properly; this saves
    bandwidth and signals freshness.
    """
    etag = '"' + hashlib.md5(content.encode("utf-8")).hexdigest()[:16] + '"'
    return FastResponse(
        content=content,
        media_type=media_type,
        headers={
            "Cache-Control": f"public, max-age={max_age}, s-maxage={max_age}, stale-while-revalidate=600",
            "ETag": etag,
            "X-Robots-Tag": "all, max-snippet:-1, max-image-preview:large",
        },
    )


def _conditional_get_304(request: Request, etag: str) -> Response | None:
    if request.headers.get("if-none-match") == etag:
        return FastResponse(status_code=304)
    return None


# ---------------------------------------------------------------------------
# DB helpers (small focussed queries — none of these are user-driven)
# ---------------------------------------------------------------------------


_Q_INCIDENTS = """
SELECT i.id::text AS id, i.code, i.name, i.summary, i.status,
       i.started_at, i.ended_at, i.updated_at,
       sero.code AS serotype_code,
       i.primary_vessel_name, i.primary_vessel_imo, i.primary_vessel_mmsi,
       (SELECT array_agg(country_iso2 ORDER BY confirmed_count DESC)
          FROM incident_countries ic WHERE ic.incident_id = i.id) AS countries,
       (SELECT COALESCE(SUM(confirmed_count),0)::int FROM incident_countries ic
          WHERE ic.incident_id = i.id) AS sum_confirmed,
       (SELECT COALESCE(SUM(deaths),0)::int FROM incident_countries ic
          WHERE ic.incident_id = i.id) AS sum_deaths
FROM incidents i
LEFT JOIN serotypes sero ON sero.id = i.serotype_id
ORDER BY
    CASE i.status WHEN 'active' THEN 0 WHEN 'monitoring' THEN 1 ELSE 2 END,
    i.started_at DESC NULLS LAST
"""

_Q_INCIDENT_COUNTRIES = """
SELECT country_iso2, confirmed_count, suspected_count, deaths, first_reported_at
FROM incident_countries
WHERE incident_id = $1
ORDER BY confirmed_count DESC, deaths DESC, country_iso2
"""

_Q_INCIDENT_HISTORY = """
SELECT iac.confirmed_cases, iac.suspected_cases, iac.deaths, iac.recovered,
       s.code AS source_code, s.name AS source_name,
       iac.reported_at, iac.nato_reliability, iac.nato_credibility,
       iac.src_citation
FROM incident_authoritative_counts iac
JOIN sources s ON s.id = iac.source_id
WHERE iac.incident_id = $1
ORDER BY iac.reported_at DESC LIMIT 12
"""

_Q_INCIDENT_ARTICLES = """
SELECT cr.id::text AS id, cr.title, cr.summary, cr.reported_date, cr.ingested_at,
       cr.country_iso2, cr.raw_url, s.code AS source_code, s.name AS source_name
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
WHERE cr.incident_id = $1
ORDER BY COALESCE(cr.reported_date, cr.ingested_at::date) DESC, cr.ingested_at DESC
LIMIT 30
"""

_Q_INCIDENT_BY_CODE = """
SELECT i.id::text AS id, i.code, i.name, i.summary, i.status,
       i.started_at, i.ended_at, i.updated_at,
       sero.code AS serotype_code,
       i.primary_vessel_name, i.primary_vessel_imo, i.primary_vessel_mmsi,
       i.primary_location_country_iso2, i.primary_location_name
FROM incidents i
LEFT JOIN serotypes sero ON sero.id = i.serotype_id
WHERE i.code = $1 OR i.id::text = $1
"""

_Q_ARTICLES = """
SELECT cr.id::text AS id, cr.title, cr.summary, cr.country_iso2,
       cr.reported_date, cr.ingested_at, cr.raw_url,
       s.code AS source_code, s.name AS source_name,
       sero.code AS serotype_code,
       qs.nato_reliability, qs.nato_credibility
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
LEFT JOIN serotypes sero ON sero.id = cr.serotype_id
LEFT JOIN qualification_scores qs ON qs.case_report_id = cr.id
WHERE cr.id = $1::uuid
"""

_Q_RECENT_ARTICLES = """
SELECT cr.id::text AS id, cr.title, cr.summary, cr.country_iso2,
       cr.reported_date, cr.ingested_at, cr.raw_url,
       s.code AS source_code, s.name AS source_name,
       sero.code AS serotype_code,
       qs.nato_reliability, qs.nato_credibility
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
LEFT JOIN serotypes sero ON sero.id = cr.serotype_id
LEFT JOIN qualification_scores qs ON qs.case_report_id = cr.id
WHERE cr.ingested_at >= $1
ORDER BY cr.ingested_at DESC
LIMIT $2
"""

_Q_COUNTRY_ARTICLES = """
SELECT cr.id::text AS id, cr.title, cr.summary, cr.reported_date,
       cr.ingested_at, cr.raw_url, s.code AS source_code, s.name AS source_name,
       sero.code AS serotype_code
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
LEFT JOIN serotypes sero ON sero.id = cr.serotype_id
WHERE cr.country_iso2 = $1
ORDER BY cr.ingested_at DESC LIMIT 50
"""

_Q_COUNTRY_LIST = """
SELECT country_iso2 AS iso, COUNT(*)::int AS n
FROM case_reports
WHERE country_iso2 IS NOT NULL
GROUP BY 1 ORDER BY n DESC
"""

_Q_SOURCES = """
SELECT s.code, s.name, s.tier, s.nato_reliability, s.nato_credibility,
       s.enabled, s.provenance_type,
       (SELECT MAX(fetched_at) FROM source_quality_log WHERE source_id = s.id) AS last_fetched
FROM sources s
WHERE s.enabled = TRUE
ORDER BY s.tier, s.code
"""

_Q_LAST_MODIFIED = """
SELECT GREATEST(
    (SELECT MAX(ingested_at) FROM case_reports),
    (SELECT MAX(updated_at) FROM incidents)
) AS lm
"""


# ---------------------------------------------------------------------------
# Sitemaps
# ---------------------------------------------------------------------------


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_index() -> Response:
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_sitemap_index(now), "application/xml", max_age=300
    )


@router.get("/sitemap-main.xml", response_class=Response)
async def sitemap_main() -> Response:
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_main_sitemap(now), "application/xml", max_age=600
    )


@router.get("/sitemap-serotypes.xml", response_class=Response)
async def sitemap_serotypes() -> Response:
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_serotypes_sitemap(now), "application/xml", max_age=3600
    )


@router.get("/sitemap-countries.xml", response_class=Response)
async def sitemap_countries() -> Response:
    async with acquire() as conn:
        rows = await conn.fetch(_Q_COUNTRY_LIST)
    isos = [r["iso"] for r in rows if r["iso"]]
    # Add cluster-relevant countries even if no case reports yet
    for iso in ["AR", "NL", "FR", "US", "ZA", "GB", "ES", "DE", "PT", "CV", "SH"]:
        if iso not in isos:
            isos.append(iso)
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_countries_sitemap(isos, now), "application/xml", max_age=600
    )


@router.get("/sitemap-incidents.xml", response_class=Response)
async def sitemap_incidents() -> Response:
    async with acquire() as conn:
        rows = await conn.fetch(_Q_INCIDENTS)
    items = [
        {
            "code": r["code"],
            "name": r["name"],
            "lastmod": r["updated_at"] or r["started_at"] or datetime.now(timezone.utc),
        }
        for r in rows
    ]
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_incidents_sitemap(items, now), "application/xml", max_age=300
    )


@router.get("/sitemap-articles.xml", response_class=Response)
async def sitemap_articles() -> Response:
    async with acquire() as conn:
        # Last 90 days, cap at 50k (Google sitemap limit per file)
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 50000)
    items = [
        {
            "id": r["id"],
            "title": r["title"] or "Untitled",
            "lastmod": r["ingested_at"],
        }
        for r in rows
    ]
    now = datetime.now(timezone.utc)
    return _cache_response(
        sitemaps.render_articles_sitemap(items, now), "application/xml", max_age=300
    )


@router.get("/news-sitemap.xml", response_class=Response)
async def news_sitemap() -> Response:
    async with acquire() as conn:
        # Google News: only articles from last 48h. We pull 72h to give
        # the cutoff filter room.
        cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 1000)
    now = datetime.now(timezone.utc)
    items = [
        {
            "id": r["id"],
            "title": r["title"] or "Untitled",
            "published": r["reported_date"] and datetime.combine(r["reported_date"], datetime.min.time(), tzinfo=timezone.utc) or r["ingested_at"],
            "keywords": ",".join(filter(None, [
                "hantavirus",
                r["serotype_code"].lower() if r["serotype_code"] else None,
                country_name(r["country_iso2"]).lower() if r["country_iso2"] else None,
                "outbreak", "surveillance",
            ])),
        }
        for r in rows
    ]
    return _cache_response(
        sitemaps.render_news_sitemap(items, now), "application/xml", max_age=180
    )


# ---------------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------------


async def _fetch_events_for_feed(limit: int = 50) -> list[dict]:
    """Pull the chronology feed for RSS/Atom/JSON."""
    async with acquire() as conn:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, limit)
    return [
        {
            "id": r["id"],
            "title": r["title"] or "Untitled",
            "summary": r["summary"],
            "url": f"{BASE_URL}/articles/{r['id']}",
            "source_url": r["raw_url"],
            "source_code": r["source_code"],
            "country_iso2": r["country_iso2"],
            "serotype_code": r["serotype_code"],
            "occurred_at": (
                datetime.combine(r["reported_date"], datetime.min.time(), tzinfo=timezone.utc)
                if r["reported_date"] else r["ingested_at"]
            ),
        }
        for r in rows
    ]


@router.get("/rss.xml", response_class=Response)
async def rss_feed() -> Response:
    events = await _fetch_events_for_feed(50)
    now = datetime.now(timezone.utc)
    return _cache_response(feeds.render_rss(events, now), "application/rss+xml", max_age=300)


@router.get("/atom.xml", response_class=Response)
async def atom_feed() -> Response:
    events = await _fetch_events_for_feed(50)
    now = datetime.now(timezone.utc)
    return _cache_response(feeds.render_atom(events, now), "application/atom+xml", max_age=300)


@router.get("/feed.json", response_class=Response)
async def json_feed() -> Response:
    events = await _fetch_events_for_feed(50)
    now = datetime.now(timezone.utc)
    return _cache_response(feeds.render_json_feed(events, now), "application/feed+json", max_age=300)


# ---------------------------------------------------------------------------
# HTML topic-cluster pages
# ---------------------------------------------------------------------------


def _home_crumb() -> Breadcrumb:
    return Breadcrumb(name="HORIZON", url=f"{BASE_URL}/")


@router.get("/hantavirus", response_class=HTMLResponse)
async def page_hantavirus() -> Response:
    spec = PageSpec(
        path="/hantavirus",
        title="Hantavirus — Symptoms, Serotypes, Transmission, Outbreaks (2026) · HORIZON",
        description=(
            "Complete reference on hantavirus disease: 12 orthohantavirus serotypes, "
            "HPS and HFRS clinical syndromes, transmission routes, prevention, treatment, "
            "and live outbreak surveillance from WHO, CDC, ECDC, PAHO, and ProMED."
        ),
        h1="Hantavirus — Live Surveillance and Reference",
        body_html=seo_content.HANTAVIRUS_HUB_BODY,
        breadcrumbs=[_home_crumb(), Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus")],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus",
                "Hantavirus — Live Surveillance and Reference",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus, orthohantavirus, ANDV, SNV, PUUV, HTNV, SEOV, DOBV, HPS, HFRS, outbreak, surveillance, WHO, CDC, ECDC",
        news_keywords="hantavirus, Andes virus, Sin Nombre, MV Hondius, outbreak",
        og_type="article",
        article_section="Public Health",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/hantavirus/symptoms", response_class=HTMLResponse)
async def page_symptoms() -> Response:
    spec = PageSpec(
        path="/hantavirus/symptoms",
        title="Hantavirus Symptoms — HPS vs HFRS, Prodrome, Critical-Care Triad · HORIZON",
        description=(
            "Detailed hantavirus symptom progression: 1–8 week incubation, flu-like prodrome, "
            "then HPS (pulmonary collapse, 30–50% CFR for Andes virus) or HFRS (renal failure, "
            "haemorrhage). Differential diagnosis and when to seek care."
        ),
        h1="Hantavirus Symptoms — Clinical Course of HPS and HFRS",
        body_html=seo_content.SYMPTOMS_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus"),
            Breadcrumb(name="Symptoms", url=f"{BASE_URL}/hantavirus/symptoms"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus/symptoms",
                "Hantavirus Symptoms",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus symptoms, HPS symptoms, HFRS symptoms, hantavirus prodrome, pulmonary syndrome, renal syndrome, thrombocytopenia",
        news_keywords="hantavirus symptoms, HPS, HFRS, prodrome",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/hantavirus/transmission", response_class=HTMLResponse)
async def page_transmission() -> Response:
    spec = PageSpec(
        path="/hantavirus/transmission",
        title="Hantavirus Transmission — Rodent Aerosols, Andes-Virus P2P · HORIZON",
        description=(
            "How hantavirus spreads: rodent-to-human aerosol inhalation is the primary route. "
            "Andes virus is the only orthohantavirus with documented person-to-person transmission. "
            "Reservoir species map, transmission myths debunked."
        ),
        h1="Hantavirus Transmission — Primary, Secondary, and Person-to-Person Routes",
        body_html=seo_content.TRANSMISSION_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus"),
            Breadcrumb(name="Transmission", url=f"{BASE_URL}/hantavirus/transmission"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus/transmission",
                "Hantavirus Transmission",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus transmission, how is hantavirus spread, andes virus person to person, rodent aerosol, reservoir species",
        news_keywords="hantavirus transmission, andes virus, person-to-person",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/hantavirus/prevention", response_class=HTMLResponse)
async def page_prevention() -> Response:
    spec = PageSpec(
        path="/hantavirus/prevention",
        title="Hantavirus Prevention — Rodent Control, Cleaning, N95 Protocols · HORIZON",
        description=(
            "Evidence-based hantavirus prevention: rodent exclusion, safe cleaning of "
            "contaminated areas (CDC bleach protocol, N95/FFP3), travel precautions for "
            "endemic regions. Vaccine status 2026."
        ),
        h1="Hantavirus Prevention — Exposure Control",
        body_html=seo_content.PREVENTION_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus"),
            Breadcrumb(name="Prevention", url=f"{BASE_URL}/hantavirus/prevention"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus/prevention",
                "Hantavirus Prevention",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus prevention, rodent control, hantavirus cleaning protocol, hantavirus N95, hantavirus vaccine, Hantavax",
        news_keywords="hantavirus prevention, vaccine, Hantavax",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/hantavirus/treatment", response_class=HTMLResponse)
async def page_treatment() -> Response:
    spec = PageSpec(
        path="/hantavirus/treatment",
        title="Hantavirus Treatment — ICU Care, ECMO, Ribavirin · HORIZON",
        description=(
            "Hantavirus treatment 2026: no licensed antiviral, supportive critical care, "
            "ECMO for HPS, ribavirin for early HFRS, monoclonal antibody trials. "
            "Long-term sequelae and rehabilitation."
        ),
        h1="Hantavirus Treatment — Supportive Critical Care",
        body_html=seo_content.TREATMENT_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus"),
            Breadcrumb(name="Treatment", url=f"{BASE_URL}/hantavirus/treatment"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus/treatment",
                "Hantavirus Treatment",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus treatment, HPS treatment, HFRS treatment, ribavirin hantavirus, ECMO hantavirus, hantavirus survival",
        news_keywords="hantavirus treatment, ribavirin, ECMO",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/hantavirus/{slug}", response_class=HTMLResponse)
async def page_serotype(slug: str) -> Response:
    s = serotype_by_slug(slug)
    if s is None:
        raise HTTPException(404, f"Unknown serotype slug: {slug!r}")

    spec = PageSpec(
        path=f"/hantavirus/{slug}",
        title=f"{s['name']} — Reservoir, Endemic Range, CFR, Outbreaks · HORIZON",
        description=(
            f"{s['name']}: {s['syndrome']}, reservoir {s['reservoir']}, "
            f"endemic to {s['endemic']}. Case-fatality {s['cfr']}. "
            f"Live surveillance, authoritative WHO/CDC sources, related serotypes."
        ),
        h1=s["name"],
        body_html=seo_content.render_serotype_body(s),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/hantavirus"),
            Breadcrumb(name=s["name"], url=f"{BASE_URL}/hantavirus/{slug}"),
        ],
        jsonld_nodes=[
            jsonld.serotype_node(s),
            jsonld.medical_web_page(
                f"{BASE_URL}/hantavirus/{slug}",
                s["name"],
                f"{BASE_URL}/hantavirus/{slug}#condition",
            ),
        ],
        keywords=f"{s['name']}, {s['code']}, hantavirus, orthohantavirus, {s['endemic']}, {s['syndrome']}",
        news_keywords=f"{s['code']}, {s['name']}, hantavirus",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/glossary", response_class=HTMLResponse)
async def page_glossary() -> Response:
    spec = PageSpec(
        path="/glossary",
        title="Hantavirus Glossary — Terminology, Acronyms, OSINT Tradecraft · HORIZON",
        description=(
            "Authoritative glossary of hantavirus terminology (ANDV, SNV, HPS, HFRS, "
            "thrombocytopenia, ECMO), surveillance vocabulary (WHO DON, CDC HAN, "
            "ECDC, ProMED), and intelligence tradecraft (NATO Admiralty Scale, "
            "ICD 206, Berkeley Protocol)."
        ),
        h1="Glossary",
        body_html=seo_content.render_glossary_body(),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Glossary", url=f"{BASE_URL}/glossary"),
        ],
        jsonld_nodes=[
            {
                "@type": "DefinedTermSet",
                "@id": f"{BASE_URL}/glossary#termset",
                "name": "HORIZON Hantavirus Glossary",
                "hasDefinedTerm": [
                    {
                        "@type": "DefinedTerm",
                        "name": term,
                        "description": defn.replace("<em>", "").replace("</em>", "").replace("<strong>", "").replace("</strong>", ""),
                        "inDefinedTermSet": f"{BASE_URL}/glossary#termset",
                    }
                    for term, defn in seo_content.GLOSSARY_TERMS
                ],
            }
        ],
        keywords="hantavirus glossary, hantavirus terminology, ANDV definition, HPS definition, HFRS definition, NATO Admiralty Scale",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/methodology", response_class=HTMLResponse)
async def page_methodology() -> Response:
    spec = PageSpec(
        path="/methodology",
        title="HORIZON Methodology — NATO Admiralty Scale, ICD 206, Berkeley Protocol",
        description=(
            "How HORIZON qualifies every record: NATO Admiralty Scale reliability/credibility, "
            "ICD 206 Source Reference Citation format, dual confidence model (pipeline vs analyst), "
            "Berkeley Protocol chain-of-custody hashing, per-country authoritative caps."
        ),
        h1="HORIZON Methodology",
        body_html=seo_content.METHODOLOGY_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Methodology", url=f"{BASE_URL}/methodology"),
        ],
        jsonld_nodes=[],
        keywords="HORIZON methodology, NATO Admiralty Scale, ICD 206, Berkeley Protocol, OSINT methodology, source qualification, dual confidence",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/faq", response_class=HTMLResponse)
async def page_faq() -> Response:
    spec = PageSpec(
        path="/faq",
        title="Hantavirus FAQ — Symptoms, Transmission, Treatment, MV Hondius · HORIZON",
        description=(
            "Frequently asked questions about hantavirus disease, the 2026 MV Hondius "
            "outbreak, and the HORIZON surveillance platform. Answers grounded in WHO/CDC/ECDC sources."
        ),
        h1="Frequently Asked Questions",
        body_html=seo_content.render_faq_body(),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="FAQ", url=f"{BASE_URL}/faq"),
        ],
        jsonld_nodes=[
            jsonld.faq_page_from_entries(f"{BASE_URL}/faq", seo_content.FAQ_ENTRIES),
        ],
        keywords="hantavirus FAQ, hantavirus questions, MV Hondius FAQ, HORIZON FAQ, hantavirus answers",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/data", response_class=HTMLResponse)
async def page_data() -> Response:
    spec = PageSpec(
        path="/data",
        title="HORIZON Hantavirus Dataset — Download, Cite, API Documentation · Open Data CC BY 4.0",
        description=(
            "Download the HORIZON hantavirus open dataset: bulk NDJSON, JSON API, RSS/Atom/JSON Feed. "
            "Machine-readable metadata in DCAT-AP, CSL-JSON, CITATION.cff, and Schema.org JSON-LD. "
            "Includes Oxford Kraemer Lab MV Hondius ANDV individual line list (CC0) and NCBI RefSeq "
            "Orthohantavirus reference genome set (HantaNet). CC BY 4.0."
        ),
        h1="HORIZON Hantavirus Open Dataset",
        body_html=seo_content.DATA_PAGE_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Data", url=f"{BASE_URL}/data"),
        ],
        jsonld_nodes=[
            {
                "@type": ["Dataset", "DataFeed"],
                "@id": "https://hantavirus.software/#dataset",
                "name": "HORIZON Hantavirus Surveillance Dataset",
                "description": (
                    "Open dataset of hantavirus outbreak case reports aggregated from 65+ authoritative sources. "
                    "Includes Oxford Kraemer Lab MV Hondius ANDV line list (CC0) and NCBI RefSeq Orthohantavirus "
                    "reference genome set (HantaNet). CC BY 4.0."
                ),
                "url": "https://hantavirus.software/data",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "creator": {"@id": "https://hantavirus.software/#org"},
                "checkFrequency": "PT15M",
                "distribution": [
                    {
                        "@type": "DataDownload",
                        "encodingFormat": "application/x-ndjson",
                        "contentUrl": "https://hantavirus.software/api/v1/cases/bulk/ndjson",
                        "name": "Bulk NDJSON streaming export",
                    },
                    {
                        "@type": "DataDownload",
                        "encodingFormat": "application/json",
                        "contentUrl": "https://hantavirus.software/api/v1/cases",
                        "name": "Case reports JSON API",
                    },
                ],
                "potentialAction": {
                    "@type": "DownloadAction",
                    "target": "https://hantavirus.software/api/v1/cases/bulk/ndjson",
                },
            }
        ],
        keywords=(
            "hantavirus dataset download, hantavirus open data, hantavirus API, "
            "hantavirus NDJSON, hantavirus JSON, hantavirus CSV, DCAT, CC BY 4.0, "
            "Oxford Kraemer Lab line list, HantaNet NCBI RefSeq, hantavirus citation"
        ),
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/sources", response_class=HTMLResponse)
async def page_sources() -> Response:
    async with acquire() as conn:
        rows = await conn.fetch(_Q_SOURCES)
    grouped: dict[int, list[dict]] = {}
    for r in rows:
        grouped.setdefault(r["tier"], []).append(dict(r))

    tier_labels = {
        1: "Tier 1 — Authoritative public-health bodies",
        2: "Tier 2 — National public-health authorities and academic journals",
        3: "Tier 3 — News aggregators and wire services",
        4: "Tier 4 — Topical media and open-source signals",
    }

    body_parts = [
        '<p class="lead">Every source ingested into HORIZON, with its current '
        'NATO Admiralty Scale rating, ingestion telemetry, and provenance type. '
        'Source list is automatically managed; this page is regenerated every 10 minutes.</p>',
    ]
    for tier in sorted(grouped):
        body_parts.append(f'<h2>{esc(tier_labels.get(tier, f"Tier {tier}"))}</h2>')
        body_parts.append('<table class="facts">')
        body_parts.append(
            '<tr><th>Code</th><th>Name</th><th>NATO</th><th>Last fetched</th></tr>'
        )
        for s in grouped[tier]:
            last = s.get("last_fetched")
            last_str = last.strftime("%Y-%m-%d %H:%M UTC") if last else "—"
            body_parts.append(
                f'<tr><th>{esc(s["code"])}</th>'
                f'<td>{esc(s["name"])} '
                f'<span class="kv">({esc(s.get("provenance_type") or "")})</span></td>'
                f'<td><span class="tag">{esc(s["nato_reliability"])}{int(s["nato_credibility"])}</span></td>'
                f'<td class="kv">{esc(last_str)}</td></tr>'
            )
        body_parts.append('</table>')

    body_parts.append('<p><a href="/methodology">Read the methodology →</a></p>')
    body_parts.append('<p><a class="cta" href="/">Open the live outbreak map →</a></p>')

    spec = PageSpec(
        path="/sources",
        title="HORIZON Source Registry — WHO, CDC, ECDC, PAHO, ProMED + 50 more",
        description=(
            "Live source registry for HORIZON hantavirus surveillance. "
            "Every WHO, CDC, ECDC, PAHO, ProMED, national-authority, peer-reviewed-journal, "
            "and aggregator feed with NATO Admiralty Scale ratings and ingestion telemetry."
        ),
        h1="Source Registry",
        body_html="".join(body_parts),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Sources", url=f"{BASE_URL}/sources"),
        ],
        jsonld_nodes=[
            jsonld.collection_page(
                f"{BASE_URL}/sources",
                "HORIZON Source Registry",
                "Live source registry with NATO Admiralty Scale ratings.",
                [(r["name"], f"{BASE_URL}/sources#{r['code']}") for r in rows[:50]],
            ),
        ],
        keywords="hantavirus sources, WHO hantavirus, CDC hantavirus, ECDC hantavirus, PAHO hantavirus, ProMED hantavirus, surveillance sources",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


@router.get("/outbreaks", response_class=HTMLResponse)
async def page_outbreaks_index() -> Response:
    async with acquire() as conn:
        rows = await conn.fetch(_Q_INCIDENTS)

    cards = ['<div class="cards">']
    for r in rows:
        status_class = "alert" if r["status"] == "active" else ""
        cards.append(
            f'<article class="card">'
            f'<p><span class="tag {status_class}">{esc(r["status"].upper())}</span> '
            f'<span class="kv">{esc(r["serotype_code"] or "—")}</span></p>'
            f'<h3><a href="/outbreaks/{esc(r["code"])}">{esc(r["name"])}</a></h3>'
            f'<p>{esc((r["summary"] or "")[:220])}…</p>'
            f'<p class="kv">{int(r["sum_confirmed"] or 0)} confirmed · {int(r["sum_deaths"] or 0)} deaths · '
            f'{int(len(r["countries"] or [])) } countries</p>'
            f'<a class="more" href="/outbreaks/{esc(r["code"])}">View incident →</a>'
            f'</article>'
        )
    cards.append('</div>')

    spec = PageSpec(
        path="/outbreaks",
        title="Live Hantavirus Outbreaks — MV Hondius, Active Clusters · HORIZON",
        description=(
            "All active and monitored hantavirus outbreaks tracked by HORIZON. "
            "Each incident page carries authoritative case counts from WHO/ECDC, "
            "the full ontology graph, and live updates."
        ),
        h1="Hantavirus Outbreaks",
        body_html=(
            '<p class="lead">Active and monitoring incidents tracked by HORIZON. '
            'Each link opens the full ontology graph with authoritative WHO/ECDC case counts, '
            'corroborating articles, and the live event chronology.</p>'
            + "".join(cards)
            + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
        ),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Outbreaks", url=f"{BASE_URL}/outbreaks"),
        ],
        jsonld_nodes=[
            jsonld.collection_page(
                f"{BASE_URL}/outbreaks",
                "HORIZON Outbreaks Index",
                "All hantavirus incidents tracked by HORIZON.",
                [(r["name"], f"{BASE_URL}/outbreaks/{r['code']}") for r in rows],
            ),
        ],
        keywords="hantavirus outbreak, hantavirus cluster, MV Hondius, andes virus outbreak, hantavirus cases 2026",
        news_keywords="hantavirus outbreak, MV Hondius, ANDV",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=300)


@router.get("/outbreaks/{code}", response_class=HTMLResponse)
async def page_incident(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(_Q_INCIDENT_BY_CODE, code)
        if row is None:
            raise HTTPException(404, f"Unknown incident: {code!r}")
        country_rows = await conn.fetch(_Q_INCIDENT_COUNTRIES, UUID(row["id"]))
        history_rows = await conn.fetch(_Q_INCIDENT_HISTORY, UUID(row["id"]))
        article_rows = await conn.fetch(_Q_INCIDENT_ARTICLES, UUID(row["id"]))

    sum_confirmed = sum(int(c["confirmed_count"] or 0) for c in country_rows)
    sum_suspected = sum(int(c["suspected_count"] or 0) for c in country_rows)
    sum_deaths = sum(int(c["deaths"] or 0) for c in country_rows)
    sum_countries = sum(1 for c in country_rows if int(c["confirmed_count"] or 0) > 0 or int(c["deaths"] or 0) > 0)

    started_at_str = row["started_at"].strftime("%-d %B %Y") if row["started_at"] else "—"
    status_class = "alert" if row["status"] == "active" else ""

    countries_table = "".join(
        f'<tr><th>{esc(country_name(c["country_iso2"]))}</th>'
        f'<td>{int(c["confirmed_count"] or 0)} confirmed</td>'
        f'<td>{int(c["suspected_count"] or 0)} suspected</td>'
        f'<td>{int(c["deaths"] or 0)} deaths</td></tr>'
        for c in country_rows
    )

    history_rows_html = "".join(
        f'<tr><th class="kv">{esc(h["reported_at"].strftime("%Y-%m-%d"))}</th>'
        f'<td><span class="tag">{esc(h["nato_reliability"])}{int(h["nato_credibility"])}</span> '
        f'{esc(h["source_name"])}</td>'
        f'<td>{int(h["confirmed_cases"] or 0)} confirmed · {int(h["deaths"] or 0)} deaths</td></tr>'
        for h in history_rows
    )

    articles_html = "".join(
        f'<li><a href="/articles/{esc(a["id"])}">{esc(a["title"])}</a> '
        f'<span class="kv">— {esc(a["source_code"])} · '
        f'{(a["reported_date"] or a["ingested_at"].date()).strftime("%Y-%m-%d")}</span></li>'
        for a in article_rows
    )

    body_html = (
        f'<p><span class="tag {status_class}">{esc(row["status"].upper())}</span> '
        f'<span class="kv">{esc(row["serotype_code"] or "—")} · started {esc(started_at_str)}</span></p>'
        f'<p class="lead">{esc(row["summary"] or "")}</p>'
        '<div class="stats">'
        f'<div class="stat"><div class="n">{sum_confirmed}</div><div class="l">Confirmed</div></div>'
        f'<div class="stat"><div class="n">{sum_suspected}</div><div class="l">Suspected</div></div>'
        f'<div class="stat"><div class="n">{sum_deaths}</div><div class="l">Deaths</div></div>'
        f'<div class="stat"><div class="n">{sum_countries}</div><div class="l">Countries</div></div>'
        '</div>'
        + (
            '<h2>Per-country breakdown</h2>'
            '<table class="facts"><tr><th>Country</th><th>Confirmed</th><th>Suspected</th><th>Deaths</th></tr>'
            + countries_table + '</table>'
            if countries_table else ''
        )
        + (
            '<h2>Authoritative-source history</h2>'
            '<table class="facts">' + history_rows_html + '</table>'
            if history_rows_html else ''
        )
        + (f'<h2>Vessel context</h2>'
           f'<p><strong>{esc(row["primary_vessel_name"] or "")}</strong> · '
           f'IMO {esc(row["primary_vessel_imo"] or "—")} · '
           f'MMSI {esc(row["primary_vessel_mmsi"] or "—")}</p>'
           if row.get("primary_vessel_name") else '')
        + (
            '<h2>Recent articles</h2><ul>' + articles_html + '</ul>'
            if articles_html else ''
        )
        + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
    )

    started_dt = row["started_at"]
    ended_dt = row["ended_at"]
    countries_iso = [c["country_iso2"] for c in country_rows if c["country_iso2"]]
    spec = PageSpec(
        path=f"/outbreaks/{row['code']}",
        title=f'{row["name"]} — Live Hantavirus Outbreak · HORIZON',
        description=(
            f'{(row["summary"] or row["name"])[:220]}'
        ),
        h1=row["name"],
        body_html=body_html,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Outbreaks", url=f"{BASE_URL}/outbreaks"),
            Breadcrumb(name=row["name"], url=f"{BASE_URL}/outbreaks/{row['code']}"),
        ],
        jsonld_nodes=[
            jsonld.event_incident(
                incident_code=row["code"],
                name=row["name"],
                summary=row["summary"],
                started_at=(datetime.combine(started_dt, datetime.min.time(), tzinfo=timezone.utc) if started_dt else None),
                ended_at=(datetime.combine(ended_dt, datetime.min.time(), tzinfo=timezone.utc) if ended_dt else None),
                countries=countries_iso,
                status=row["status"],
                confirmed=sum_confirmed,
                deaths=sum_deaths,
            ),
        ],
        keywords=f'{row["name"]}, hantavirus outbreak, {row["serotype_code"]}, ' + ", ".join(country_name(c) for c in countries_iso[:5]),
        news_keywords=f'{row["name"]}, hantavirus, outbreak, {row["serotype_code"]}',
        article_published_time=(started_dt.strftime("%Y-%m-%d") if started_dt else None),
        article_modified_time=(row["updated_at"].strftime("%Y-%m-%dT%H:%M:%S+00:00") if row.get("updated_at") else None),
        article_section="Outbreaks",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


@router.get("/countries", response_class=HTMLResponse)
async def page_countries_index() -> Response:
    async with acquire() as conn:
        rows = await conn.fetch(_Q_COUNTRY_LIST)
    valid_rows = [r for r in rows if r["iso"]]

    cards = ['<div class="cards">']
    for r in valid_rows:
        iso = r["iso"].upper()
        cards.append(
            f'<article class="card"><h3>'
            f'<a href="/countries/{esc(iso.lower())}">{esc(country_name(iso))}</a></h3>'
            f'<p class="kv">{int(r["n"])} ingested reports · ISO {esc(iso)}</p></article>'
        )
    cards.append('</div>')

    spec = PageSpec(
        path="/countries",
        title="Hantavirus by Country — Argentina, USA, Germany, Finland · HORIZON",
        description=(
            "Hantavirus surveillance by country. Per-country case chronology, "
            "authoritative-source linkage, endemic-serotype context. "
            "Coverage: Americas, Europe, east Asia, plus emerging regions."
        ),
        h1="Hantavirus by Country",
        body_html=(
            '<p class="lead">HORIZON tracks hantavirus signal across every country with ingested '
            'reports. Country pages include case chronology, the serotype context, and links '
            'to the authoritative national public-health authority.</p>'
            + "".join(cards)
        ),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Countries", url=f"{BASE_URL}/countries"),
        ],
        jsonld_nodes=[
            jsonld.collection_page(
                f"{BASE_URL}/countries",
                "Hantavirus by country",
                "Country index for HORIZON hantavirus surveillance.",
                [(country_name(r["iso"].upper()), f"{BASE_URL}/countries/{r['iso'].lower()}") for r in valid_rows[:50]],
            ),
        ],
        keywords="hantavirus countries, hantavirus by country, hantavirus argentina, hantavirus usa, hantavirus germany, hantavirus finland",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/countries/{iso}", response_class=HTMLResponse)
async def page_country(iso: str) -> Response:
    iso_upper = iso.upper()
    if iso_upper not in COUNTRY_NAMES and not (len(iso_upper) == 2 and iso_upper.isalpha()):
        raise HTTPException(404, f"Unknown country: {iso!r}")

    cn = country_name(iso_upper)

    async with acquire() as conn:
        articles = await conn.fetch(_Q_COUNTRY_ARTICLES, iso_upper)

    articles_html = "".join(
        f'<li><a href="/articles/{esc(a["id"])}">{esc(a["title"])}</a> '
        f'<span class="kv">— {esc(a["source_code"])} · '
        f'{(a["reported_date"] or a["ingested_at"].date()).strftime("%Y-%m-%d")}</span></li>'
        for a in articles
    )

    body_html = (
        f'<p class="lead">Hantavirus surveillance and recent activity for '
        f'<strong>{esc(cn)}</strong>. {int(len(articles))} ingested reports in the '
        f'current HORIZON window.</p>'
        + ('<h2>Recent reports</h2><ul>' + articles_html + '</ul>'
           if articles_html else
           '<p class="muted">No recent reports have been ingested for this country in the active window. '
           'Active reports for this country, if any, will appear here within minutes of ingestion.</p>')
        + '<h2>Authoritative national source</h2><p>For clinical or policy queries refer to the '
          'country\'s national public-health authority and to '
          '<a href="https://www.who.int" rel="external">WHO</a>, '
          '<a href="https://www.cdc.gov/hantavirus/" rel="external">CDC</a>, '
          '<a href="https://www.ecdc.europa.eu/" rel="external">ECDC</a>, and '
          '<a href="https://www.paho.org" rel="external">PAHO</a>.</p>'
        + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
    )

    spec = PageSpec(
        path=f"/countries/{iso_upper.lower()}",
        title=f"Hantavirus in {cn} — Case Chronology and Surveillance · HORIZON",
        description=(
            f"Hantavirus surveillance for {cn}: ingested reports, "
            f"chronology, serotype context, and authoritative national-source linkage."
        ),
        h1=f"Hantavirus in {cn}",
        body_html=body_html,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Countries", url=f"{BASE_URL}/countries"),
            Breadcrumb(name=cn, url=f"{BASE_URL}/countries/{iso_upper.lower()}"),
        ],
        jsonld_nodes=[
            jsonld.country_place(iso_upper),
            jsonld.collection_page(
                f"{BASE_URL}/countries/{iso_upper.lower()}",
                f"Hantavirus reports for {cn}",
                f"Live HORIZON hantavirus surveillance reports for {cn}.",
                [(a["title"], f"{BASE_URL}/articles/{a['id']}") for a in articles[:20]],
            ),
        ],
        keywords=f"hantavirus {cn}, {cn} hantavirus outbreak, hantavirus {iso_upper}, {cn} hanta",
        news_keywords=f"hantavirus, {cn}",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


@router.get("/articles", response_class=HTMLResponse)
async def page_articles_index() -> Response:
    async with acquire() as conn:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 200)

    items = "".join(
        f'<li><a href="/articles/{esc(r["id"])}">{esc(r["title"] or "Untitled")}</a> '
        f'<span class="kv">— {esc(r["source_code"])} · '
        f'{(r["reported_date"] or r["ingested_at"].date()).strftime("%Y-%m-%d")}'
        f'{" · " + country_name(r["country_iso2"]) if r["country_iso2"] else ""}</span></li>'
        for r in rows
    )

    spec = PageSpec(
        path="/articles",
        title="Live Hantavirus News & Reports — WHO, CDC, ECDC Feed · HORIZON",
        description=(
            "Live feed of hantavirus reports ingested into HORIZON from WHO, CDC, "
            "ECDC, PAHO, ProMED, peer-reviewed journals, and open news. "
            "Sorted reverse-chronologically with NATO source qualification."
        ),
        h1="Live Article Feed",
        body_html=(
            '<p class="lead">Reverse-chronological feed of every ingested hantavirus-relevant '
            'report from the last 30 days. Subscribe via '
            '<a href="/rss.xml">RSS</a>, <a href="/atom.xml">Atom</a>, or '
            '<a href="/feed.json">JSON Feed</a>.</p>'
            f'<ul>{items}</ul>'
        ),
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Articles", url=f"{BASE_URL}/articles"),
        ],
        jsonld_nodes=[],
        keywords="hantavirus news, hantavirus reports, hantavirus articles, WHO hantavirus, CDC hantavirus, ProMED hantavirus",
        news_keywords="hantavirus news, outbreak, surveillance",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=300)


@router.get("/articles/{article_id}", response_class=HTMLResponse)
async def page_article(article_id: str) -> Response:
    try:
        aid = UUID(article_id)
    except ValueError:
        raise HTTPException(404, "Invalid article id")
    async with acquire() as conn:
        r = await conn.fetchrow(_Q_ARTICLES, aid)
    if r is None:
        raise HTTPException(404, "Article not found")

    reported = r["reported_date"]
    ingested = r["ingested_at"]
    published_dt = (
        datetime.combine(reported, datetime.min.time(), tzinfo=timezone.utc)
        if reported else ingested
    )
    canonical = f"{BASE_URL}/articles/{r['id']}"

    body_html = (
        f'<p class="kv"><span class="tag">{esc(r["nato_reliability"])}{int(r["nato_credibility"])}</span> '
        f'{esc(r["source_name"])} · {esc((reported or ingested.date()).strftime("%Y-%m-%d"))}'
        f'{" · " + country_name(r["country_iso2"]) if r["country_iso2"] else ""}'
        f'{" · " + r["serotype_code"] if r["serotype_code"] else ""}</p>'
        + (f'<p class="lead">{esc(r["summary"])}</p>' if r["summary"] else "")
        + (
            f'<p><a class="cta" href="{esc(r["raw_url"])}" rel="external noopener">'
            f'Read at source ({esc(r["source_name"])}) →</a></p>'
        )
        + '<h2>HORIZON metadata</h2>'
        + '<table class="facts">'
        + f'<tr><th>Source</th><td>{esc(r["source_name"])} <span class="kv">({esc(r["source_code"])})</span></td></tr>'
        + f'<tr><th>NATO rating</th><td>{esc(r["nato_reliability"])}{int(r["nato_credibility"])} '
          '— see <a href="/methodology">methodology</a></td></tr>'
        + (f'<tr><th>Country</th><td><a href="/countries/{esc(r["country_iso2"].lower())}">{esc(country_name(r["country_iso2"]))}</a></td></tr>' if r["country_iso2"] else "")
        + (f'<tr><th>Serotype</th><td>{esc(r["serotype_code"])}</td></tr>' if r["serotype_code"] else "")
        + f'<tr><th>Reported date</th><td>{esc(str(reported))}</td></tr>'
        + f'<tr><th>Ingested at</th><td class="kv">{esc(ingested.strftime("%Y-%m-%d %H:%M UTC"))}</td></tr>'
        + '</table>'
        + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
    )

    spec = PageSpec(
        path=f"/articles/{r['id']}",
        title=f'{r["title"]} · HORIZON',
        description=((r["summary"] or r["title"])[:230]),
        h1=r["title"] or "Untitled",
        body_html=body_html,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Articles", url=f"{BASE_URL}/articles"),
            Breadcrumb(name=(r["title"] or "Article")[:60], url=canonical),
        ],
        jsonld_nodes=[
            jsonld.news_article(
                article_id=r["id"],
                headline=r["title"] or "Untitled",
                summary=r["summary"],
                url=canonical,
                raw_url=r["raw_url"],
                published=published_dt,
                modified=ingested,
                country_iso2=r["country_iso2"],
                serotype_code=r["serotype_code"],
                source_name=r["source_name"],
                nato_reliability=r["nato_reliability"],
                nato_credibility=int(r["nato_credibility"]),
            ),
        ],
        keywords=f'hantavirus, {r["source_code"]}, {r["serotype_code"] or ""}, {country_name(r["country_iso2"]) if r["country_iso2"] else ""}',
        news_keywords=f'hantavirus, {r["serotype_code"] or ""}',
        article_published_time=iso_dt(published_dt) if isinstance(published_dt, datetime) else None,
        article_modified_time=iso_dt(ingested),
        article_section="News",
        article_authors=[r["source_name"], "79th Unit Limited"],
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


# ---------------------------------------------------------------------------
# IndexNow endpoint discovery — pointing at our key file
# ---------------------------------------------------------------------------


@router.get("/indexnow-keyfile", response_class=PlainTextResponse)
async def indexnow_keyfile() -> Response:
    """Return the IndexNow key so submission endpoints can verify ownership."""
    return PlainTextResponse(
        "59d765645bcc5c9d796c94bf59063fe5",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ============================================================================
# SPANISH SURFACE (/es/)
# ============================================================================
#
# Spanish-language SEO twins of the English topic clusters. Each page is a
# proper translation (not a calque), keyed off the same JSON-LD identities
# as its English equivalent via shared @id values. hreflang link tags in
# the HTML shell connect them bidirectionally.
#
# URL pattern: /es{english-path} but with Spanish-language URL segments
# (e.g. /es/hantavirus/sintomas, /es/brotes/mv-hondius-2026,
# /es/paises/ar).
# ============================================================================


def _home_crumb_es() -> Breadcrumb:
    return Breadcrumb(name="HORIZON", url=f"{BASE_URL}/es/")


@router.get("/es", response_class=HTMLResponse)
@router.get("/es/", response_class=HTMLResponse)
async def page_es_home() -> Response:
    """Spanish landing page — points at the live map and lists Spanish topic clusters."""
    body = f"""
<p class="lead">
HORIZON es una plataforma de vigilancia de brotes de hantavirus en vivo
con procedencia de fuente de nivel auditoría. Agregamos señales de la
Organización Mundial de la Salud (OMS), la Organización Panamericana de
la Salud (OPS), los Centros para el Control y la Prevención de
Enfermedades de EE. UU. (CDC), el Centro Europeo para la Prevención y el
Control de Enfermedades (ECDC), ProMED, autoridades nacionales,
literatura revisada por pares y noticias abiertas — cada registro lleva
calificación NATO de Almirantazgo y trazabilidad SHA-256.
</p>

{seo_content._CTA_LIVE_MAP.replace("Open the live outbreak map", "Abrir el mapa de brotes en vivo")}

<h2>Brote activo</h2>
<p><a href="/es/brotes/mv-hondius-2026"><strong>MV Hondius 2026</strong></a> — Andes virus, exposición sospechada en Ushuaia (Tierra del Fuego, Argentina). Bajo seguimiento por OMS, OPS, CDC, ECDC y el Ministerio de Salud argentino.</p>

<h2>Temas principales</h2>
<div class="cards">
<article class="card"><h3><a href="/es/hantavirus">Qué es el hantavirus</a></h3><p>Familia de virus de roedores con dos síndromes clínicos: SCPH y FHSR.</p></article>
<article class="card"><h3><a href="/es/hantavirus/sintomas">Síntomas</a></h3><p>Pródromo gripal, progresión a SCPH o FHSR, criterios para buscar atención.</p></article>
<article class="card"><h3><a href="/es/hantavirus/transmision">Transmisión</a></h3><p>Aerosoles de excretas de roedores; ANDV con transmisión persona-persona.</p></article>
<article class="card"><h3><a href="/es/hantavirus/prevencion">Prevención</a></h3><p>Control de roedores, protocolos de limpieza segura, equipo de protección.</p></article>
<article class="card"><h3><a href="/es/hantavirus/tratamiento">Tratamiento</a></h3><p>Cuidado crítico de soporte, ECMO, ribavirina temprana en FHSR.</p></article>
<article class="card"><h3><a href="/es/hantavirus/virus-de-los-andes">Virus de los Andes</a></h3><p>El serotipo más letal de las Américas; único con transmisión P2P.</p></article>
</div>

<h2>Datos abiertos</h2>
<p>Todos los datos están disponibles bajo CC BY 4.0 vía la <a href="/api/openapi.json">API JSON</a> o suscripción <a href="/rss.xml">RSS</a>/<a href="/atom.xml">Atom</a>/<a href="/feed.json">JSON Feed</a>.</p>

{seo_content._CTA_LIVE_MAP.replace("Open the live outbreak map", "Abrir el mapa de brotes en vivo")}
"""
    spec = PageSpec(
        path="/es/",
        title="HORIZON — Rastreador de Brotes de Hantavirus en Vivo",
        description=(
            "Vigilancia en vivo de brotes de hantavirus con procedencia de fuente "
            "de nivel auditoría. OMS, OPS, CDC, ECDC, ProMED y literatura revisada "
            "por pares. Mapa, cronología y ontología del brote MV Hondius 2026."
        ),
        h1="Rastreador de Brotes de Hantavirus en Vivo",
        body_html=body,
        breadcrumbs=[_home_crumb_es()],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="hantavirus, virus de los Andes, ANDV, Sin Nombre, hantavirus síntomas, MV Hondius, vigilancia, OMS, OPS, CDC, ECDC",
        news_keywords="hantavirus, ANDV, virus de los Andes, MV Hondius, brote",
        og_type="website",
        locale="es-ES",
        hreflang_path="/",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/es/hantavirus", response_class=HTMLResponse)
async def page_es_hantavirus() -> Response:
    spec = PageSpec(
        path="/es/hantavirus",
        title="Hantavirus — Síntomas, Serotipos, Transmisión, Brotes (2026) · HORIZON",
        description=(
            "Referencia completa sobre la enfermedad por hantavirus: 12 serotipos "
            "de orthohantavirus, síndromes SCPH y FHSR, transmisión, prevención, "
            "tratamiento, y vigilancia en vivo desde OMS, OPS, CDC y ECDC."
        ),
        h1="Hantavirus — Vigilancia y Referencia en Vivo",
        body_html=i18n.ES_HANTAVIRUS_HUB_BODY,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/es/hantavirus",
                "Hantavirus — Vigilancia y Referencia",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus, orthohantavirus, virus de los Andes, Sin Nombre, Puumala, Hantaan, Seoul, SCPH, FHSR, brote",
        news_keywords="hantavirus, virus de los Andes, MV Hondius, brote",
        locale="es-ES",
        hreflang_path="/hantavirus",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/es/hantavirus/sintomas", response_class=HTMLResponse)
async def page_es_symptoms() -> Response:
    spec = PageSpec(
        path="/es/hantavirus/sintomas",
        title="Síntomas del Hantavirus — SCPH vs FHSR, Pródromo, Tríada · HORIZON",
        description=(
            "Progresión clínica detallada del hantavirus: incubación 1–8 semanas, "
            "pródromo gripal, luego SCPH (colapso pulmonar, letalidad 30–50% para "
            "Andes) o FHSR (falla renal). Diagnóstico diferencial y criterios."
        ),
        h1="Síntomas del Hantavirus — Curso Clínico de SCPH y FHSR",
        body_html=i18n.ES_SYMPTOMS_BODY,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
            Breadcrumb(name="Síntomas", url=f"{BASE_URL}/es/hantavirus/sintomas"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/es/hantavirus/sintomas",
                "Síntomas del Hantavirus",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus síntomas, SCPH síntomas, FHSR síntomas, hantavirus pródromo, síndrome pulmonar, síndrome renal, trombocitopenia",
        locale="es-ES",
        hreflang_path="/hantavirus/symptoms",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/es/hantavirus/transmision", response_class=HTMLResponse)
async def page_es_transmission() -> Response:
    spec = PageSpec(
        path="/es/hantavirus/transmision",
        title="Transmisión del Hantavirus — Aerosoles de Roedores, ANDV Persona-Persona · HORIZON",
        description=(
            "Cómo se propaga el hantavirus: inhalación de excretas aerosolizadas "
            "es la ruta principal. El virus de los Andes es el único orthohantavirus "
            "con transmisión persona-persona documentada. Mapa de especies reservorio."
        ),
        h1="Transmisión del Hantavirus",
        body_html=i18n.ES_TRANSMISSION_BODY,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
            Breadcrumb(name="Transmisión", url=f"{BASE_URL}/es/hantavirus/transmision"),
        ],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="hantavirus transmisión, cómo se contagia el hantavirus, virus de los Andes persona-persona, aerosol roedor",
        locale="es-ES",
        hreflang_path="/hantavirus/transmission",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/es/hantavirus/prevencion", response_class=HTMLResponse)
async def page_es_prevention() -> Response:
    spec = PageSpec(
        path="/es/hantavirus/prevencion",
        title="Prevención del Hantavirus — Control de Roedores, Limpieza, N95 · HORIZON",
        description=(
            "Prevención del hantavirus basada en evidencia: exclusión de roedores, "
            "protocolo seguro de limpieza con lejía 1:10 y respirador N95/FFP3, "
            "precauciones de viaje a zonas endémicas. Estado vacunal 2026."
        ),
        h1="Prevención del Hantavirus",
        body_html=i18n.ES_PREVENTION_BODY,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
            Breadcrumb(name="Prevención", url=f"{BASE_URL}/es/hantavirus/prevencion"),
        ],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="prevención hantavirus, control de roedores, limpieza segura, N95 hantavirus, vacuna hantavirus, Hantavax",
        locale="es-ES",
        hreflang_path="/hantavirus/prevention",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/es/hantavirus/tratamiento", response_class=HTMLResponse)
async def page_es_treatment() -> Response:
    spec = PageSpec(
        path="/es/hantavirus/tratamiento",
        title="Tratamiento del Hantavirus — UCI, ECMO, Ribavirina · HORIZON",
        description=(
            "Tratamiento del hantavirus 2026: no hay antiviral licenciado, soporte "
            "crítico, ECMO en SCPH, ribavirina en FHSR temprana, ensayos de "
            "anticuerpos monoclonales. Secuelas a largo plazo."
        ),
        h1="Tratamiento del Hantavirus",
        body_html=i18n.ES_TREATMENT_BODY,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
            Breadcrumb(name="Tratamiento", url=f"{BASE_URL}/es/hantavirus/tratamiento"),
        ],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="tratamiento hantavirus, SCPH tratamiento, FHSR tratamiento, ribavirina hantavirus, ECMO hantavirus",
        locale="es-ES",
        hreflang_path="/hantavirus/treatment",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


# Spanish per-serotype pages. URL slugs use Spanish-language fragments where
# that's the natural rendering (virus-de-los-andes, sin-nombre, hantaan, etc).
_ES_SEROTYPE_URL_MAP = {
    "virus-de-los-andes": "andes-virus",
    "sin-nombre":         "sin-nombre-virus",
    "puumala":            "puumala-virus",
    "hantaan":            "hantaan-virus",
    "seoul":              "seoul-virus",
    "dobrava-belgrado":   "dobrava-belgrade-virus",
    "bayou":              "bayou-virus",
    "laguna-negra":       "laguna-negra-virus",
    "choclo":             "choclo-virus",
    "tula":               "tula-virus",
    "saaremaa":           "saaremaa-virus",
    "black-creek-canal":  "black-creek-canal-virus",
}


@router.get("/es/hantavirus/{es_slug}", response_class=HTMLResponse)
async def page_es_serotype(es_slug: str) -> Response:
    # Reserve known sub-pages
    if es_slug in {"sintomas", "transmision", "prevencion", "tratamiento"}:
        raise HTTPException(404)
    en_slug = _ES_SEROTYPE_URL_MAP.get(es_slug)
    if en_slug is None:
        raise HTTPException(404, f"Serotipo desconocido: {es_slug!r}")
    s_en = serotype_by_slug(en_slug)
    if s_en is None:
        raise HTTPException(404)
    s_es = i18n.ES_SEROTYPE_PROSE.get(en_slug)

    body = i18n.render_es_serotype_body(s_en, s_es)
    name = s_es["name"] if s_es else s_en["name"]

    spec = PageSpec(
        path=f"/es/hantavirus/{es_slug}",
        title=f"{name} — Reservorio, Endémica, Letalidad, Brotes · HORIZON",
        description=(
            f"{name}: {(s_es or s_en).get('syndrome', s_en['syndrome'])}, "
            f"reservorio {(s_es or s_en).get('reservoir', s_en['reservoir'])}, "
            f"endémico de {(s_es or s_en).get('endemic', s_en['endemic'])}. "
            f"Letalidad {(s_es or s_en).get('cfr', s_en['cfr'])}."
        ),
        h1=name,
        body_html=body,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Hantavirus", url=f"{BASE_URL}/es/hantavirus"),
            Breadcrumb(name=name, url=f"{BASE_URL}/es/hantavirus/{es_slug}"),
        ],
        jsonld_nodes=[
            jsonld.serotype_node(s_en),
            jsonld.medical_web_page(
                f"{BASE_URL}/es/hantavirus/{es_slug}",
                name,
                f"{BASE_URL}/hantavirus/{en_slug}#condition",
            ),
        ],
        keywords=f"{name}, {s_en['code']}, hantavirus, orthohantavirus",
        locale="es-ES",
        hreflang_path=f"/hantavirus/{en_slug}",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/es/preguntas-frecuentes", response_class=HTMLResponse)
async def page_es_faq() -> Response:
    spec = PageSpec(
        path="/es/preguntas-frecuentes",
        title="Preguntas Frecuentes sobre Hantavirus · HORIZON",
        description=(
            "Preguntas frecuentes sobre la enfermedad por hantavirus, el brote "
            "del MV Hondius 2026 y la plataforma HORIZON. Respuestas con base "
            "en fuentes OMS, OPS, CDC y ECDC."
        ),
        h1="Preguntas Frecuentes",
        body_html=i18n.render_es_faq_body(),
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="FAQ", url=f"{BASE_URL}/es/preguntas-frecuentes"),
        ],
        jsonld_nodes=[
            jsonld.faq_page_from_entries(f"{BASE_URL}/es/preguntas-frecuentes", i18n.ES_FAQ_ENTRIES),
        ],
        keywords="hantavirus FAQ, preguntas frecuentes hantavirus, MV Hondius preguntas",
        locale="es-ES",
        hreflang_path="/faq",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/es/brotes/{code}", response_class=HTMLResponse)
async def page_es_incident(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(_Q_INCIDENT_BY_CODE, code)
        if row is None:
            raise HTTPException(404)
        country_rows = await conn.fetch(_Q_INCIDENT_COUNTRIES, UUID(row["id"]))

    sum_confirmed = sum(int(c["confirmed_count"] or 0) for c in country_rows)
    sum_suspected = sum(int(c["suspected_count"] or 0) for c in country_rows)
    sum_deaths = sum(int(c["deaths"] or 0) for c in country_rows)

    countries_table = "".join(
        f'<tr><th>{esc(country_name(c["country_iso2"]))}</th>'
        f'<td>{int(c["confirmed_count"] or 0)} confirmados</td>'
        f'<td>{int(c["suspected_count"] or 0)} sospechosos</td>'
        f'<td>{int(c["deaths"] or 0)} fallecidos</td></tr>'
        for c in country_rows
    )

    status_es = {"active": "ACTIVO", "monitoring": "MONITOREO", "resolved": "RESUELTO"}.get(row["status"], row["status"].upper())
    started_at_str = row["started_at"].strftime("%-d de %B de %Y") if row["started_at"] else "—"

    body_html = (
        f'<p><span class="tag {"alert" if row["status"] == "active" else ""}">{esc(status_es)}</span> '
        f'<span class="kv">{esc(row["serotype_code"] or "—")} · iniciado {esc(started_at_str)}</span></p>'
        f'<p class="lead">{esc(row["summary"] or "")}</p>'
        '<div class="stats">'
        f'<div class="stat"><div class="n">{sum_confirmed}</div><div class="l">Confirmados</div></div>'
        f'<div class="stat"><div class="n">{sum_suspected}</div><div class="l">Sospechosos</div></div>'
        f'<div class="stat"><div class="n">{sum_deaths}</div><div class="l">Fallecidos</div></div>'
        '</div>'
        + ('<h2>Desglose por país</h2><table class="facts"><tr><th>País</th><th>Confirmados</th><th>Sospechosos</th><th>Fallecidos</th></tr>' + countries_table + '</table>' if countries_table else '')
        + '<p><a class="cta" href="/">Abrir el mapa de brotes en vivo →</a></p>'
    )

    spec = PageSpec(
        path=f"/es/brotes/{code}",
        title=f'{row["name"]} — Brote de Hantavirus · HORIZON',
        description=(row["summary"] or row["name"])[:220],
        h1=row["name"],
        body_html=body_html,
        breadcrumbs=[
            _home_crumb_es(),
            Breadcrumb(name="Brotes", url=f"{BASE_URL}/es/brotes"),
            Breadcrumb(name=row["name"], url=f"{BASE_URL}/es/brotes/{code}"),
        ],
        jsonld_nodes=[
            jsonld.event_incident(
                incident_code=row["code"],
                name=row["name"],
                summary=row["summary"],
                started_at=(datetime.combine(row["started_at"], datetime.min.time(), tzinfo=timezone.utc) if row["started_at"] else None),
                ended_at=None,
                countries=[c["country_iso2"] for c in country_rows if c["country_iso2"]],
                status=row["status"],
                confirmed=sum_confirmed,
                deaths=sum_deaths,
            ),
        ],
        keywords=f'{row["name"]}, brote hantavirus, {row["serotype_code"]}',
        news_keywords=f'{row["name"]}, hantavirus, brote',
        locale="es-ES",
        hreflang_path=f"/outbreaks/{code}",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


# ============================================================================
# E-E-A-T TRUST PAGES (/about, /contact, /editorial-standards, /corrections)
# ============================================================================


@router.get("/about", response_class=HTMLResponse)
async def page_about() -> Response:
    body = """
<p class="lead">
HORIZON is a live hantavirus outbreak surveillance platform operated by
<strong>79th Unit Limited</strong>, a UK intelligence consultancy
(Companies House number 17133814). We specialise in open-source
intelligence, public-safety surveillance, and audit-grade source
provenance.
</p>

<h2>What we do</h2>
<p>
We aggregate hantavirus outbreak signal from authoritative public-health
bodies (WHO, CDC, ECDC, PAHO), national authorities, peer-reviewed
literature, and open news. We qualify every record with the NATO
Admiralty Scale, attach an ICD 206 source citation, and hash every
fetched document under the Berkeley Protocol chain-of-custody.
</p>

<h2>What we are not</h2>
<p>
We are <strong>not</strong> a clinical service. We do not provide
medical advice. If you are unwell, contact a clinician or your local
public-health authority. We are <strong>not</strong> a substitute for
WHO Disease Outbreak News, ECDC weekly threats reports, or CDC HAN
advisories — read those alongside.
</p>

<h2>Our standards</h2>
<p>
See our <a href="/methodology">methodology</a>, <a href="/editorial-standards">editorial
standards</a>, and <a href="/corrections">corrections policy</a>. All data
is open under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license external">CC BY 4.0</a>.
</p>

<h2>Contact</h2>
<p>
Email <a href="mailto:security@79thunit.co.uk">security@79thunit.co.uk</a>
for security disclosures (PGP key in <a href="/.well-known/security.txt">security.txt</a>),
or <a href="mailto:hello@79thunit.co.uk">hello@79thunit.co.uk</a> for
general enquiries.
</p>

<h2>Open API</h2>
<p>
Every dataset we surface is available as machine-readable JSON via our
<a href="/api/openapi.json">OpenAPI schema</a>. Mirror it, scrape it,
index it, train models on it — the only requirement is attribution.
</p>

<p><a class="cta" href="/">Open the live outbreak map →</a></p>
"""
    spec = PageSpec(
        path="/about",
        title="About HORIZON — Operated by 79th Unit Limited · UK CRN 17133814",
        description="HORIZON is operated by 79th Unit Limited, a UK intelligence consultancy specialising in OSINT, public-safety surveillance, and audit-grade source provenance.",
        h1="About HORIZON",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="About", url=f"{BASE_URL}/about")],
        jsonld_nodes=[{
            "@type": "AboutPage",
            "@id": f"{BASE_URL}/about#aboutpage",
            "url": f"{BASE_URL}/about",
            "name": "About HORIZON",
            "mainEntity": {"@id": f"{BASE_URL}/#org"},
        }],
        keywords="HORIZON about, 79th Unit Limited, hantavirus surveillance company, OSINT UK, public health intelligence",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/editorial-standards", response_class=HTMLResponse)
async def page_editorial_standards() -> Response:
    body = """
<p class="lead">
HORIZON publishes one type of content: structured outbreak intelligence
with auditable source provenance. Every claim is traceable. Every
correction is logged. This page documents the rules we hold ourselves to.
</p>

<h2>1. Source verification</h2>
<p>
Every record is tied to a named, published source. We do not accept
anonymous tips. We do not republish unsourced social media posts as fact.
Every fetched document is hashed (SHA-256) at ingestion under the
<a href="https://humanrights.berkeley.edu/programs-projects/tech-human-rights-program/berkeley-protocol" rel="external">Berkeley Protocol</a>;
the hash is stored alongside the fetch timestamp, URL, and User-Agent.
</p>

<h2>2. NATO Admiralty Scale rating</h2>
<p>
Every source is rated on reliability (A–F) and credibility (1–6) per NATO
AJP-2.1. Auto-application of an extracted fact to the incident ontology
requires an A1/A2/B1/B2 source or three corroborating independent sources
within 48 hours. See the full procedure on the
<a href="/methodology">methodology page</a>.
</p>

<h2>3. Dual confidence model</h2>
<p>
Pipeline confidence (machine, statistical) and analyst confidence (human,
vetted) are stored as separate columns and never conflated. Front-end
displays distinguish them visually. Export endpoints require analyst
confidence on every record.
</p>

<h2>4. Corrections</h2>
<p>
When we discover an error, we (a) correct the record, (b) log the
correction in our <a href="/corrections">corrections log</a>, and (c) preserve
the prior version's hash in the database for audit. We never silently
overwrite history.
</p>

<h2>5. No clinical advice</h2>
<p>
We are not a clinical service. We do not diagnose. We do not recommend
treatment. Every medical topic page carries an explicit disclaimer
directing readers to WHO, CDC, ECDC, or their local clinician.
</p>

<h2>6. Plagiarism + copyright</h2>
<p>
All prose on HORIZON is original. We cite WHO/CDC/ECDC/PAHO sources by
name and link to them. We do not copy excerpts longer than a few words
without attribution. Our open-data licence is CC BY 4.0; we ask the same
attribution standard of anyone using our data.
</p>

<h2>7. AI training disclosure</h2>
<p>
HORIZON content is generated by humans. We use machine learning for
extraction and deduplication (specifically the qualification pipeline
described in our methodology). We do not generate prose with large
language models. Where ML touches the dataset, the
<code>pipeline_confidence</code> field is amber — not green.
</p>

<h2>8. Editorial independence</h2>
<p>
HORIZON receives no advertising revenue. We accept no sponsored content.
We do not promote products, treatments, or commercial services.
</p>

<p><a href="/methodology">→ Read the full methodology</a></p>
"""
    spec = PageSpec(
        path="/editorial-standards",
        title="Editorial Standards — HORIZON",
        description="The editorial, verification, correction, and AI-disclosure standards that govern every HORIZON record.",
        h1="Editorial Standards",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Editorial standards", url=f"{BASE_URL}/editorial-standards")],
        jsonld_nodes=[{
            "@type": "WebPage",
            "@id": f"{BASE_URL}/editorial-standards#webpage",
            "url": f"{BASE_URL}/editorial-standards",
            "name": "Editorial Standards",
            "publisher": {"@id": f"{BASE_URL}/#org"},
        }],
        keywords="HORIZON editorial standards, fact-checking policy, corrections policy, AI disclosure, source verification",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/corrections", response_class=HTMLResponse)
async def page_corrections() -> Response:
    body = """
<p class="lead">
When HORIZON publishes incorrect data we log the correction here. The
record is updated, the prior version's hash is preserved, and a new
audit entry is created. We never silently overwrite history.
</p>

<h2>2026-05-13 — Per-country death attribution capped</h2>
<p>
Issue: The v1.5 extractor attributed cluster-total death counts to
individual countries via article-origin metadata. Specifically, US news
articles reporting the MV Hondius cluster total of 3 deaths were
incorrectly attributed as 3 US-national deaths.
</p>
<p>
Fix: Extractor upgraded to v1.6 with the article-metadata fallback removed.
Added a global authoritative cap that rejects per-country proposals
where the proposed count exceeds the WHO Disease Outbreak News total.
DB reset for affected countries (US: 11/0/3 → 1/0/0, ES: 1/0/0 → 0/0/0).
</p>
<p class="kv">Cite: migrations 026, 027, 028 in the HORIZON DB schema.</p>

<h2>2026-05-13 — Live AIS source corrected</h2>
<p>
Issue: MV Hondius position on the live map was stale because the only
working AIS source (myshiptracking.com public page) was serving cached
data more than 7 hours old. AISStream had no satellite coverage for the
vessel's mid-ocean position; Kpler subscription unresolved.
</p>
<p>
Fix: CruiseMapper connector added as a fresh live AIS source; verified
to return current vessel position within minutes of the AIS receiver.
Dead-reckoning algorithm upgraded to COG/SOG projection (pure for first
6h, blended for 6–12h, route-interpolation fallback).
</p>

<p><a href="/editorial-standards">← Editorial standards</a></p>
"""
    spec = PageSpec(
        path="/corrections",
        title="Corrections Log — HORIZON",
        description="Public log of every correction issued to HORIZON data, with date, root cause, and remediation.",
        h1="Corrections Log",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Corrections", url=f"{BASE_URL}/corrections")],
        jsonld_nodes=[],
        keywords="HORIZON corrections, errata, transparency log",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/terms-of-service", response_class=HTMLResponse)
@router.get("/terms", response_class=HTMLResponse)
async def page_terms() -> Response:
    body = """
<p class="lead">
HORIZON (hantavirus.software) is operated by <strong>79th Unit Limited</strong>,
a private limited company registered in the United Kingdom (Companies
House number 17133814). By accessing the site, the API, or any feed,
you agree to these terms. Last updated: 13 May 2026.
</p>

<h2>1. Service description</h2>
<p>
HORIZON is a live hantavirus outbreak surveillance and OSINT platform.
We aggregate publicly available outbreak signal from the World Health
Organization, US CDC, ECDC, PAHO, ProMED, national public-health
authorities, peer-reviewed literature, and open news. We do not
provide clinical advice, diagnostic services, or treatment
recommendations.
</p>

<h2>2. Open data licence</h2>
<p>
All data, prose, structured data, sitemaps, feeds, and JSON endpoints
on this site are published under
<a rel="license noopener" href="https://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International (CC BY 4.0)</a>.
You may copy, redistribute, transform, and build upon this material for
any purpose, including commercially, provided you give attribution
to <em>79th Unit Limited</em> and link back to
<a href="https://hantavirus.software/">hantavirus.software</a>.
The CC BY 4.0 attribution baked into our embeddable widgets satisfies
the licence requirement for widget embeds.
</p>

<h2>3. Acceptable use</h2>
<p>
You may mirror, scrape, index, train models on, and otherwise process
HORIZON content under CC BY 4.0. You may <strong>not</strong>:
</p>
<ul>
<li>Misrepresent HORIZON or 79th Unit Limited as the source of derivative work without attribution.</li>
<li>Use the public API in ways that materially degrade service for other users (the rate limit is 60 req/min per IP; respect it).</li>
<li>Use HORIZON to harass, defame, or surveil identifiable individuals. Our content is about public-health epidemiology, not individual people.</li>
<li>Bypass technical controls, attempt unauthorised access, or probe for security vulnerabilities outside our published
   <a href="/.well-known/security.txt">security.txt</a> coordinated-disclosure policy.</li>
</ul>

<h2>4. Not medical advice</h2>
<p>
HORIZON is a surveillance and OSINT platform, not a clinical service.
Nothing on this site constitutes medical advice, diagnosis, or
treatment recommendation. If you are unwell, contact a qualified
clinician or your local public-health authority. We are not a
substitute for the WHO Disease Outbreak News, ECDC weekly threats
report, CDC HAN advisories, or any other authoritative public-health
bulletin. Read those alongside.
</p>

<h2>5. Accuracy disclaimer</h2>
<p>
We follow strict <a href="/editorial-standards">editorial standards</a>:
every record is tied to a named, published source; corrections are
logged in our public <a href="/corrections">corrections log</a>; and
the underlying methodology is documented at
<a href="/methodology">/methodology</a>. Notwithstanding, we make no
warranty as to the accuracy, completeness, currency, or fitness for
any particular purpose of the content, and we accept no liability for
any loss arising from reliance on it.
</p>

<h2>6. Liability</h2>
<p>
Nothing in these terms excludes or limits liability for death or
personal injury caused by negligence, fraud, or any other liability that
cannot lawfully be excluded under UK law. Subject to that, our total
aggregate liability to you for any cause of action arising under or in
connection with these terms is limited to GBP 100. We are not liable for
any indirect, consequential, special, or punitive losses.
</p>

<h2>7. Third-party links</h2>
<p>
HORIZON links to external sources (WHO, CDC, ECDC, news outlets, etc.).
Those sites are operated by independent third parties; we are not
responsible for their content, policies, or availability.
</p>

<h2>8. Termination</h2>
<p>
We may suspend or restrict access from any IP address, network, or
account that materially breaches these terms or our acceptable use
policy. The site itself remains a public resource under CC BY 4.0 and we
will not arbitrarily restrict public access.
</p>

<h2>9. Changes</h2>
<p>
We may update these terms from time to time. Material changes will be
announced on the <a href="/corrections">corrections log</a> with the
effective date. Continued use of the site after a change constitutes
acceptance of the updated terms.
</p>

<h2>10. Governing law</h2>
<p>
These terms and any dispute arising under them are governed by the laws
of England and Wales. The courts of England and Wales have exclusive
jurisdiction.
</p>

<h2>11. Contact</h2>
<p>
General: <a href="mailto:hello@79thunit.co.uk">hello@79thunit.co.uk</a><br>
Security: <a href="mailto:security@79thunit.co.uk">security@79thunit.co.uk</a><br>
Corrections: <a href="mailto:corrections@79thunit.co.uk">corrections@79thunit.co.uk</a><br>
Postal: 79th Unit Limited, United Kingdom. Companies House registration: 17133814.
</p>

<p class="muted">Effective date: 13 May 2026. <a href="/privacy">→ Privacy Policy</a></p>
"""
    spec = PageSpec(
        path="/terms-of-service",
        title="Terms of Service — HORIZON",
        description="Terms of service for HORIZON hantavirus surveillance platform. Open data under CC BY 4.0. Operated by 79th Unit Limited (UK CRN 17133814).",
        h1="Terms of Service",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Terms of Service", url=f"{BASE_URL}/terms-of-service")],
        jsonld_nodes=[{
            "@type": "WebPage",
            "@id": f"{BASE_URL}/terms-of-service#webpage",
            "url": f"{BASE_URL}/terms-of-service",
            "name": "Terms of Service",
            "publisher": {"@id": f"{BASE_URL}/#org"},
            "datePublished": "2026-05-13",
            "dateModified": "2026-05-13",
            "inLanguage": "en-GB",
        }],
        keywords="HORIZON terms of service, hantavirus.software terms, CC BY 4.0, 79th Unit terms",
        article_modified_time="2026-05-13",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/privacy", response_class=HTMLResponse)
@router.get("/privacy-policy", response_class=HTMLResponse)
async def page_privacy() -> Response:
    body = """
<p class="lead">
This policy explains what data HORIZON (hantavirus.software) collects,
how we use it, and your rights under the UK General Data Protection
Regulation. We are operated by <strong>79th Unit Limited</strong>
(Companies House 17133814, United Kingdom). Last updated: 13 May 2026.
</p>

<h2>1. What we collect</h2>
<p>
HORIZON is a read-only public-data platform. We collect the minimum
data needed to operate the service securely:
</p>
<ul>
<li><strong>Server access logs</strong> — IP address, User-Agent, HTTP request line, response code, response size, timestamp, referrer. Retained for 30 days for security monitoring and capacity planning, then automatically purged.</li>
<li><strong>API rate-limit state</strong> — IP address kept in-memory for the duration of the 1-minute rate-limit window (60 requests per IP per minute).</li>
<li><strong>Security incident records</strong> — if we detect abuse, the relevant access-log lines may be retained beyond 30 days for investigation under our <a href="/.well-known/security.txt">security disclosure policy</a>.</li>
</ul>

<h2>2. What we do NOT collect</h2>
<ul>
<li>We do <strong>not</strong> use Google Analytics, Plausible, Matomo, or any analytics service that shares data with third parties.</li>
<li>We do <strong>not</strong> use advertising trackers, retargeting pixels, or social-media tracking cookies.</li>
<li>We do <strong>not</strong> require an account, login, or email address to read HORIZON content or use the public API.</li>
<li>We do <strong>not</strong> collect any sensitive personal data (race, ethnicity, political opinion, religion, union membership, genetic data, biometric data, health data, sex life, sexual orientation).</li>
</ul>

<h2>3. Cookies</h2>
<p>
HORIZON does not set first-party cookies. The Carto map tiles
(<code>basemaps.cartocdn.com</code>) and Google Fonts
(<code>fonts.googleapis.com</code>, <code>fonts.gstatic.com</code>) may
set their own cookies under their respective privacy policies — we have
no control over those. Per UK GDPR / PECR, we do not require a cookie
banner because we set no first-party cookies and the third-party
cookies above are strictly necessary for map rendering and webfont
delivery.
</p>

<h2>4. Third-party services</h2>
<table class="facts">
<tr><th>Service</th><th>Purpose</th><th>Privacy policy</th></tr>
<tr><th>Carto</th><td>Background map tiles for the interactive outbreak map</td><td><a href="https://carto.com/privacy/" rel="external">carto.com/privacy</a></td></tr>
<tr><th>Google Fonts</th><td>Web font delivery (Inter, JetBrains Mono)</td><td><a href="https://policies.google.com/privacy" rel="external">policies.google.com/privacy</a></td></tr>
<tr><th>Google News (Subscribe with Google)</th><td>Publisher Center registration enabling Google News indexing</td><td><a href="https://policies.google.com/privacy" rel="external">policies.google.com/privacy</a></td></tr>
<tr><th>OVHcloud</th><td>Server hosting in Roubaix, France (EU jurisdiction, not US CLOUD Act)</td><td><a href="https://www.ovhcloud.com/en/personal-data-protection/" rel="external">ovhcloud.com/en/personal-data-protection</a></td></tr>
</table>
<p>
Map tiles and Google Fonts are loaded by your browser directly from
those third parties when you view the live map. Your IP address is
visible to them in that request. We do not control their data
processing.
</p>

<h2>5. Lawful basis (UK GDPR Article 6)</h2>
<p>
We process server access logs under <strong>legitimate interests</strong>
(Article 6(1)(f) UK GDPR): operating, securing, and improving a public
public-health surveillance service. The data we collect is limited to
what is strictly necessary to detect abuse and operate the service.
</p>

<h2>6. International transfers</h2>
<p>
Server infrastructure is hosted by <strong>OVHcloud</strong> in Roubaix,
France (EU). Backup infrastructure is in Strasbourg, France (EU) and
Falkenstein, Germany (EU). No personal data is transferred outside the
EU/UK by HORIZON's own systems. Third-party services (Carto, Google)
may transfer data to their own jurisdictions per their published
privacy policies.
</p>

<h2>7. Your rights under UK GDPR</h2>
<p>
You have the right to:
</p>
<ul>
<li>Request access to any personal data we hold about you (Article 15).</li>
<li>Request rectification of inaccurate personal data (Article 16).</li>
<li>Request erasure of your personal data (Article 17), subject to our legitimate-interest grounds.</li>
<li>Object to processing under legitimate interests (Article 21).</li>
<li>Lodge a complaint with the UK Information Commissioner's Office (<a href="https://ico.org.uk/" rel="external">ico.org.uk</a>).</li>
</ul>
<p>
To exercise any of these rights, email
<a href="mailto:privacy@79thunit.co.uk">privacy@79thunit.co.uk</a>.
We respond within one month per UK GDPR.
</p>

<h2>8. Children</h2>
<p>
HORIZON content is not directed at children under 13. We do not
knowingly process data from children. If you become aware that a child
has provided personal data, email
<a href="mailto:privacy@79thunit.co.uk">privacy@79thunit.co.uk</a> and
we will delete it.
</p>

<h2>9. Data Protection Officer</h2>
<p>
Email: <a href="mailto:privacy@79thunit.co.uk">privacy@79thunit.co.uk</a><br>
Postal: 79th Unit Limited, United Kingdom. Companies House: 17133814.
</p>

<h2>10. Changes</h2>
<p>
Material changes to this policy will be announced in the
<a href="/corrections">corrections log</a> with the effective date.
</p>

<p class="muted">Effective date: 13 May 2026. <a href="/terms-of-service">→ Terms of Service</a></p>
"""
    spec = PageSpec(
        path="/privacy",
        title="Privacy Policy — HORIZON",
        description="Privacy policy for HORIZON hantavirus surveillance. No analytics, no trackers, EU hosting, UK GDPR compliant. Operated by 79th Unit Limited.",
        h1="Privacy Policy",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Privacy Policy", url=f"{BASE_URL}/privacy")],
        jsonld_nodes=[{
            "@type": "WebPage",
            "@id": f"{BASE_URL}/privacy#webpage",
            "url": f"{BASE_URL}/privacy",
            "name": "Privacy Policy",
            "publisher": {"@id": f"{BASE_URL}/#org"},
            "datePublished": "2026-05-13",
            "dateModified": "2026-05-13",
            "inLanguage": "en-GB",
        }],
        keywords="HORIZON privacy policy, hantavirus.software privacy, UK GDPR, 79th Unit privacy",
        article_modified_time="2026-05-13",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/contact", response_class=HTMLResponse)
async def page_contact() -> Response:
    body = """
<p class="lead">
HORIZON is operated by <a href="https://79thunit.co.uk">79th Unit Limited</a>,
Companies House number 17133814 (United Kingdom).
</p>

<h2>Security disclosures</h2>
<p>
Email <a href="mailto:security@79thunit.co.uk">security@79thunit.co.uk</a>.
Coordinated disclosure policy, PGP key, and response SLA in our
<a href="/.well-known/security.txt">security.txt</a>.
</p>

<h2>Data corrections</h2>
<p>
If you spot an incorrect record, email
<a href="mailto:corrections@79thunit.co.uk">corrections@79thunit.co.uk</a>
with the article URL or record ID and a citation supporting the
correction. We respond within 24h and log every change in the public
<a href="/corrections">corrections log</a>.
</p>

<h2>Press</h2>
<p>
Email <a href="mailto:press@79thunit.co.uk">press@79thunit.co.uk</a>.
Background, screenshots, dataset access, and quotable spokesperson
availability on request.
</p>

<h2>General</h2>
<p>
Email <a href="mailto:hello@79thunit.co.uk">hello@79thunit.co.uk</a>.
</p>

<h2>Postal</h2>
<address>
79th Unit Limited<br>
United Kingdom<br>
Companies House registration: 17133814
</address>
"""
    spec = PageSpec(
        path="/contact",
        title="Contact HORIZON — Security, Corrections, Press, General",
        description="Contact details for HORIZON: security disclosures, data corrections, press enquiries, general questions.",
        h1="Contact",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Contact", url=f"{BASE_URL}/contact")],
        jsonld_nodes=[{
            "@type": "ContactPage",
            "@id": f"{BASE_URL}/contact#contactpage",
            "url": f"{BASE_URL}/contact",
            "mainEntity": {"@id": f"{BASE_URL}/#org"},
        }],
        keywords="HORIZON contact, 79th Unit contact, hantavirus surveillance press, data corrections",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


# ============================================================================
# PER-SOURCE LANDING PAGES (/sources/{code})
# ============================================================================


@router.get("/sources/{code}", response_class=HTMLResponse)
async def page_source(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.code, s.name, s.tier, s.nato_reliability, s.nato_credibility,
                   s.provenance_type, s.enabled,
                   (SELECT MAX(fetched_at) FROM source_quality_log WHERE source_id = s.id) AS last_fetched,
                   (SELECT COUNT(*)::int FROM case_reports WHERE source_id = s.id) AS total_articles,
                   (SELECT COUNT(*)::int FROM case_reports WHERE source_id = s.id AND ingested_at >= NOW() - INTERVAL '7 days') AS articles_7d
            FROM sources s
            WHERE s.code = $1
            """,
            code,
        )
        if row is None:
            raise HTTPException(404, f"Unknown source: {code!r}")
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        articles = await conn.fetch(
            """
            SELECT cr.id::text AS id, cr.title, cr.reported_date, cr.ingested_at,
                   cr.country_iso2, cr.raw_url, sero.code AS serotype_code
            FROM case_reports cr
            LEFT JOIN serotypes sero ON sero.id = cr.serotype_id
            WHERE cr.source_id = (SELECT id FROM sources WHERE code = $1)
              AND cr.ingested_at >= $2
            ORDER BY cr.ingested_at DESC LIMIT 30
            """,
            code, cutoff,
        )

    articles_html = "".join(
        f'<li><a href="/articles/{esc(a["id"])}">{esc(a["title"] or "Untitled")}</a> '
        f'<span class="kv">{(a["reported_date"] or a["ingested_at"].date()).strftime("%Y-%m-%d")}'
        f'{" · " + country_name(a["country_iso2"]) if a["country_iso2"] else ""}'
        f'{" · " + a["serotype_code"] if a["serotype_code"] else ""}</span></li>'
        for a in articles
    )

    body = (
        '<p class="lead">'
        f'{esc(row["name"])} is one of {("Tier "+str(row["tier"]))} feeds HORIZON ingests for hantavirus surveillance. '
        f'NATO Admiralty Scale rating: <strong>{esc(row["nato_reliability"])}{int(row["nato_credibility"])}</strong> '
        f'({esc(row["provenance_type"] or "—")}).'
        '</p>'
        + '<table class="facts">'
        + f'<tr><th>Source code</th><td><code>{esc(row["code"])}</code></td></tr>'
        + f'<tr><th>Tier</th><td>{int(row["tier"])} — {("authoritative" if row["tier"] == 1 else "national or peer-reviewed" if row["tier"] == 2 else "aggregator or wire" if row["tier"] == 3 else "topical media")}</td></tr>'
        + f'<tr><th>NATO rating</th><td>{esc(row["nato_reliability"])}{int(row["nato_credibility"])} '
          '— see <a href="/methodology">methodology</a></td></tr>'
        + f'<tr><th>Provenance type</th><td>{esc(row["provenance_type"] or "—")}</td></tr>'
        + f'<tr><th>Articles ingested (all time)</th><td>{int(row["total_articles"] or 0):,}</td></tr>'
        + f'<tr><th>Articles last 7 days</th><td>{int(row["articles_7d"] or 0):,}</td></tr>'
        + f'<tr><th>Last fetched</th><td class="kv">{(row["last_fetched"].strftime("%Y-%m-%d %H:%M UTC") if row["last_fetched"] else "—")}</td></tr>'
        + '</table>'
        + (f'<h2>Recent ingested reports</h2><ul>{articles_html}</ul>' if articles_html else '<p class="muted">No ingested reports in the active 30-day window for this source.</p>')
        + '<p><a href="/sources">← All sources</a> · <a href="/methodology">Methodology →</a></p>'
    )

    spec = PageSpec(
        path=f"/sources/{code}",
        title=f'{row["name"]} ({row["code"]}) — Hantavirus Source · HORIZON',
        description=(
            f'{row["name"]} is a Tier-{row["tier"]} source for HORIZON hantavirus '
            f'surveillance, rated NATO Admiralty Scale {row["nato_reliability"]}'
            f'{int(row["nato_credibility"])}. {int(row["total_articles"] or 0):,} ingested reports.'
        ),
        h1=f'{row["name"]}',
        body_html=body,
        breadcrumbs=[
            Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"),
            Breadcrumb(name="Sources", url=f"{BASE_URL}/sources"),
            Breadcrumb(name=row["name"], url=f"{BASE_URL}/sources/{code}"),
        ],
        jsonld_nodes=[{
            "@type": "Organization",
            "@id": f"{BASE_URL}/sources/{code}#source-org",
            "name": row["name"],
            "url": row.get("raw_url") or f"{BASE_URL}/sources/{code}",
            "additionalProperty": [
                {"@type": "PropertyValue", "name": "NATO reliability", "value": row["nato_reliability"]},
                {"@type": "PropertyValue", "name": "NATO credibility", "value": int(row["nato_credibility"])},
                {"@type": "PropertyValue", "name": "Tier", "value": int(row["tier"])},
                {"@type": "PropertyValue", "name": "Provenance type", "value": row["provenance_type"] or "—"},
            ],
        }],
        keywords=f'{row["name"]}, hantavirus source, {row["code"]}, NATO Admiralty Scale, OSINT source',
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


# ============================================================================
# COMPARISON PAGES (/compare/{slug})
# ============================================================================


_COMPARISONS: dict[str, dict] = {
    "andes-vs-sin-nombre": {
        "title": "Andes virus vs Sin Nombre virus — HPS Severity, CFR, Geography",
        "h1": "Andes Virus vs Sin Nombre Virus",
        "left": "Andes virus (ANDV)",
        "right": "Sin Nombre virus (SNV)",
        "left_slug": "andes-virus",
        "right_slug": "sin-nombre-virus",
        "rows": [
            ("Region", "Southern South America (Argentina, Chile)", "US Four Corners (AZ, CO, NM, UT), Canada, Mexico"),
            ("Reservoir", "Oligoryzomys longicaudatus (long-tailed pygmy rice rat)", "Peromyscus maniculatus (deer mouse)"),
            ("Syndrome", "Hantavirus Pulmonary Syndrome (HPS)", "Hantavirus Pulmonary Syndrome (HPS)"),
            ("Case-fatality rate", "30–50%", "~38%"),
            ("Person-to-person transmission", "DOCUMENTED — only orthohantavirus with P2P", "Not documented"),
            ("First identified", "1995 (Argentina)", "1993 (Four Corners outbreak)"),
            ("Vaccine availability", "None licensed", "None licensed"),
            ("Antiviral", "Ribavirin off-label in LatAm; mAbs in trials", "Ribavirin trials negative"),
        ],
        "discussion": (
            "Both viruses cause Hantavirus Pulmonary Syndrome with extremely high "
            "case-fatality and rapid progression from a flu-like prodrome to "
            "cardiopulmonary collapse. The defining clinical difference is "
            "person-to-person transmission: Andes virus has been documented to "
            "spread between close household contacts (most famously the "
            "El Bolsón cluster of 1996), while Sin Nombre virus has never been "
            "shown to transmit between humans. The reservoir-host species "
            "differ, but in both cases human infection is via inhalation of "
            "aerosolised excreta in enclosed rural structures."
        ),
    },
    "hantavirus-vs-influenza": {
        "title": "Hantavirus vs Influenza — Symptoms, Severity, Transmission",
        "h1": "Hantavirus vs Influenza (Flu)",
        "left": "Hantavirus (HPS, ANDV/SNV)",
        "right": "Seasonal influenza (A/B)",
        "left_slug": "andes-virus",
        "right_slug": None,
        "rows": [
            ("Initial symptoms", "Fever, severe myalgia (thighs/back), headache, GI upset", "Fever, myalgia, headache, sore throat, cough"),
            ("Incubation", "1–8 weeks (very long)", "1–4 days"),
            ("Lethal phase", "Cardiopulmonary collapse 4–10 days after symptom onset", "Pneumonia, occasional bacterial co-infection"),
            ("Case-fatality", "30–50% (ANDV), ~38% (SNV)", "0.1% (typical season)"),
            ("Transmission", "Rodent aerosol; ANDV person-to-person", "Respiratory droplet, person-to-person"),
            ("Treatment", "Supportive ICU care, ECMO; no licensed antiviral", "Oseltamivir, baloxavir, supportive"),
            ("Vaccine", "Hantavax only (Hantaan, South Korea)", "Annual updated vaccines"),
            ("Lab clue", "Thrombocytopenia + left shift + immunoblasts", "Lymphopenia, normal platelets"),
        ],
        "discussion": (
            "Hantavirus and influenza both start with non-specific flu-like "
            "symptoms. The clinical divergence is dramatic: by day 5–10 after "
            "symptom onset, hantavirus patients in the HPS-causing serotypes "
            "are in profound cardiopulmonary failure with thrombocytopenia and "
            "haemoconcentration; influenza patients are typically improving. "
            "The exposure history is critical: rural rodent contact, recent "
            "travel to endemic areas, or cleaning of rodent-infested "
            "structures should raise suspicion for hantavirus."
        ),
    },
    "hantavirus-vs-covid": {
        "title": "Hantavirus vs COVID-19 — Clinical Differences, Transmission",
        "h1": "Hantavirus vs COVID-19",
        "left": "Hantavirus (HPS)",
        "right": "SARS-CoV-2 (COVID-19)",
        "left_slug": "andes-virus",
        "right_slug": None,
        "rows": [
            ("Family", "Hantaviridae", "Coronaviridae"),
            ("Initial symptoms", "Fever, severe myalgia, headache, GI", "Fever, cough, fatigue, anosmia, GI"),
            ("Incubation", "1–8 weeks", "2–14 days"),
            ("Predominant organ damage", "Lungs (non-cardiogenic oedema) + heart", "Lungs + multi-organ"),
            ("Case-fatality (severe disease)", "30–50% (ANDV)", "~1–4% (varies by variant + age)"),
            ("Transmission", "Rodent aerosol; ANDV person-to-person", "Airborne person-to-person"),
            ("Treatment", "Supportive ICU, ECMO; ribavirin (FHSR only)", "Antivirals (paxlovid, remdesivir), steroids"),
            ("Vaccine", "Hantavax (HTNV only)", "mRNA, viral vector, protein subunit"),
        ],
        "discussion": (
            "Both diseases cause severe respiratory illness. Key differences: "
            "hantavirus has a much longer incubation (weeks vs days), "
            "thrombocytopenia and haemoconcentration are hallmarks of HPS "
            "(unusual in COVID-19), and exposure history points to rural "
            "rodent contact rather than community transmission. ANDV is the "
            "only orthohantavirus that transmits person-to-person, which is "
            "rare and requires close household contact."
        ),
    },
    "hps-vs-hfrs": {
        "title": "HPS vs HFRS — The Two Hantavirus Clinical Syndromes",
        "h1": "Hantavirus Pulmonary Syndrome (HPS) vs Haemorrhagic Fever with Renal Syndrome (HFRS)",
        "left": "HPS",
        "right": "HFRS",
        "left_slug": "sin-nombre-virus",
        "right_slug": "hantaan-virus",
        "rows": [
            ("Region", "Americas", "Eurasia"),
            ("Causative serotypes", "Sin Nombre, Andes, Bayou, Black Creek Canal, Laguna Negra, Choclo", "Hantaan, Seoul, Puumala, Dobrava-Belgrade, Saaremaa"),
            ("Predominant organ", "Lungs (non-cardiogenic oedema)", "Kidneys (acute kidney injury)"),
            ("Case-fatality", "30–50% (ANDV), ~38% (SNV)", "5–15% (HTNV/DOBV); <1% (PUUV)"),
            ("Classical course", "Prodrome → cardiopulmonary collapse (rapid)", "Five stages: febrile, hypotensive, oliguric, diuretic, convalescent"),
            ("Lab hallmark", "Thrombocytopenia + immunoblasts + haemoconcentration", "Thrombocytopenia + AKI + bleeding"),
            ("ICU duration", "Often <1 week (rapid course)", "1–3 weeks (renal recovery)"),
            ("Long-term sequelae", "Pulmonary function usually recovers in 6–12 months", "~5–10% persistent renal impairment"),
        ],
        "discussion": (
            "Hantavirus disease has historically been split into two clinical "
            "buckets defined by which organ system fails first. HPS is the New "
            "World presentation and is much more lethal; HFRS is the Old World "
            "presentation and is more renal-dominated. Both share an initial "
            "prodrome and the underlying pathophysiology of vascular leak, but "
            "diverge at the critical-care management level: HPS needs lung "
            "support (often ECMO), HFRS needs renal support (dialysis)."
        ),
    },
}


@router.get("/compare", response_class=HTMLResponse)
async def page_compare_index() -> Response:
    cards = ['<div class="cards">']
    # Pinned: live tracker comparison (not in _COMPARISONS because it uses a custom multi-column layout)
    cards.append(
        '<article class="card"><h3>'
        '<a href="/compare/hantavirus-live-trackers">Best Hantavirus Live Tracker 2026</a>'
        '</h3>'
        '<p>HORIZON <span class="kv">vs</span> hantavirus.live, hanta-live.com, hantaviruslive.com</p>'
        '<a class="more" href="/compare/hantavirus-live-trackers">Compare →</a></article>'
    )
    for slug, c in _COMPARISONS.items():
        cards.append(
            f'<article class="card"><h3><a href="/compare/{esc(slug)}">{esc(c["h1"])}</a></h3>'
            f'<p>{esc(c["left"])} <span class="kv">vs</span> {esc(c["right"])}</p>'
            f'<a class="more" href="/compare/{esc(slug)}">Compare →</a></article>'
        )
    cards.append('</div>')

    spec = PageSpec(
        path="/compare",
        title="Hantavirus Comparisons — Andes vs Sin Nombre, HPS vs HFRS, Live Trackers · HORIZON",
        description="Side-by-side comparisons of hantavirus serotypes, syndromes, and live tracker platforms. HORIZON vs hantavirus.live, hanta-live.com, hantaviruslive.com.",
        h1="Hantavirus Comparisons",
        body_html='<p class="lead">Side-by-side comparison pages — useful for clinicians, journalists, and travellers triaging a symptom presentation against multiple differential diagnoses.</p>' + "".join(cards),
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Compare", url=f"{BASE_URL}/compare")],
        jsonld_nodes=[],
        keywords="hantavirus comparison, andes virus vs sin nombre, hantavirus vs flu, hantavirus vs covid, HPS vs HFRS",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/compare/hantavirus-live-trackers", response_class=HTMLResponse)
async def page_compare_trackers() -> Response:
    """Dedicated comparison page: HORIZON vs hantavirus.live vs hanta-live vs hantaviruslive."""
    spec = PageSpec(
        path="/compare/hantavirus-live-trackers",
        title="Best Hantavirus Live Tracker 2026 — HORIZON vs hantavirus.live vs hanta-live.com vs hantaviruslive.com",
        description=(
            "Factual feature comparison of every public hantavirus live tracker in 2026. "
            "HORIZON (65+ sources, free API, Oxford Kraemer Lab line list, CC BY 4.0) vs "
            "hantavirus.live, hanta-live.com, and hantaviruslive.com. "
            "Why media-volume counts are not confirmed case counts."
        ),
        h1="Hantavirus Live Tracker Comparison: HORIZON vs Competitors (2026)",
        body_html=seo_content.TRACKER_COMPARE_BODY,
        breadcrumbs=[
            _home_crumb(),
            Breadcrumb(name="Compare", url=f"{BASE_URL}/compare"),
            Breadcrumb(name="Live tracker comparison", url=f"{BASE_URL}/compare/hantavirus-live-trackers"),
        ],
        jsonld_nodes=[
            {
                "@type": "Article",
                "@id": f"{BASE_URL}/compare/hantavirus-live-trackers#article",
                "headline": "Best Hantavirus Live Tracker 2026 — HORIZON vs Competitors",
                "description": (
                    "Factual comparison of HORIZON against hantavirus.live, hanta-live.com, and "
                    "hantaviruslive.com across sources, data type, API availability, open data "
                    "licence, genomic layer, and research suitability."
                ),
                "publisher": {"@id": f"{BASE_URL}/#org"},
                "datePublished": "2026-05-14",
                "dateModified": "2026-05-14",
                "inLanguage": "en-GB",
                "about": {"@type": "WebSite", "name": "HORIZON Hantavirus Surveillance", "url": BASE_URL},
            }
        ],
        keywords=(
            "best hantavirus live tracker 2026, hantavirus live tracker comparison, "
            "hantavirus.live vs horizon, hanta-live.com review, hantaviruslive.com review, "
            "hantavirus live map, hantavirus surveillance platform, hantavirus confirmed cases"
        ),
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/compare/{slug}", response_class=HTMLResponse)
async def page_compare(slug: str) -> Response:
    c = _COMPARISONS.get(slug)
    if c is None:
        raise HTTPException(404, f"Unknown comparison: {slug!r}")

    rows = "".join(
        f'<tr><th>{esc(label)}</th><td>{esc(left)}</td><td>{esc(right)}</td></tr>'
        for label, left, right in c["rows"]
    )

    body = (
        f'<p class="lead">{esc(c["discussion"])}</p>'
        '<table class="facts">'
        f'<tr><th></th><th>{esc(c["left"])}</th><th>{esc(c["right"])}</th></tr>'
        f'{rows}'
        '</table>'
        + (f'<p><a href="/hantavirus/{esc(c["left_slug"])}">→ Full {esc(c["left"])} page</a></p>' if c.get("left_slug") else "")
        + (f'<p><a href="/hantavirus/{esc(c["right_slug"])}">→ Full {esc(c["right"])} page</a></p>' if c.get("right_slug") else "")
        + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
    )

    spec = PageSpec(
        path=f"/compare/{slug}",
        title=f'{c["title"]} · HORIZON',
        description=c["discussion"][:230],
        h1=c["h1"],
        body_html=body,
        breadcrumbs=[
            Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"),
            Breadcrumb(name="Compare", url=f"{BASE_URL}/compare"),
            Breadcrumb(name=c["h1"], url=f"{BASE_URL}/compare/{slug}"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            {
                "@type": "Article",
                "@id": f"{BASE_URL}/compare/{slug}#article",
                "headline": c["title"],
                "description": c["discussion"][:220],
                "publisher": {"@id": f"{BASE_URL}/#org"},
                "datePublished": "2026-05-13",
                "inLanguage": "en-GB",
            }
        ],
        keywords=c["title"].lower(),
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


# ============================================================================
# CHRONOLOGY (/chronology) — LiveBlogPosting of the active outbreak
# ============================================================================


@router.get("/chronology", response_class=HTMLResponse)
async def page_chronology() -> Response:
    async with acquire() as conn:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 200)

    items_html: list[str] = []
    liveblog_updates: list[dict] = []
    last_date: str | None = None
    for r in rows:
        date = (r["reported_date"] or r["ingested_at"].date()).isoformat()
        if date != last_date:
            items_html.append(f'<h2 id="{date}">{date}</h2><ul>')
            if last_date is not None:
                items_html.insert(-1, "</ul>")
            last_date = date
        url = f"/articles/{r['id']}"
        items_html.append(
            f'<li><a href="{url}">{esc(r["title"] or "Untitled")}</a> '
            f'<span class="kv">— {esc(r["source_code"])}'
            f'{" · " + country_name(r["country_iso2"]) if r["country_iso2"] else ""}</span></li>'
        )
        ts = (
            datetime.combine(r["reported_date"], datetime.min.time(), tzinfo=timezone.utc)
            if r["reported_date"] else r["ingested_at"]
        )
        liveblog_updates.append({
            "id": r["id"],
            "headline": r["title"] or "Untitled",
            "date": iso_dt(ts) if isinstance(ts, datetime) else str(ts),
            "url": f"{BASE_URL}{url}",
        })
    if last_date is not None:
        items_html.append("</ul>")

    body = (
        '<p class="lead">Reverse-chronological live blog of every hantavirus '
        'signal HORIZON has ingested in the last 90 days. Subscribe via '
        '<a href="/rss.xml">RSS</a>, <a href="/atom.xml">Atom</a>, '
        '<a href="/feed.json">JSON Feed</a>, or our WebSub hub at '
        '<a href="/websub">/websub</a> for instant push notification.</p>'
        + "".join(items_html)
        + '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
    )

    spec = PageSpec(
        path="/chronology",
        title="Live Hantavirus Chronology — 90-Day Timeline · HORIZON",
        description="Reverse-chronological live blog of every hantavirus signal HORIZON has ingested, with NATO source qualification and SHA-256 chain-of-custody.",
        h1="Live Hantavirus Chronology",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Chronology", url=f"{BASE_URL}/chronology")],
        jsonld_nodes=[
            jsonld.live_blog_posting(f"{BASE_URL}/chronology", "Hantavirus surveillance live blog", liveblog_updates[:50]),
        ],
        keywords="hantavirus chronology, hantavirus timeline, hantavirus live blog, hantavirus news feed",
        news_keywords="hantavirus, chronology, live blog, outbreak timeline",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


# ============================================================================
# JSON-LD EMBED ENDPOINT (/api/v1/jsonld/{kind}/{id})
# ============================================================================
#
# Third parties can embed our structured data by referencing this URL. The
# response is a single, focused JSON-LD object (not a full graph). Useful
# for sharing the MV Hondius incident on news sites, journalist tools,
# academic papers, or AI training pipelines.


@router.get("/api/v1/jsonld/incident/{code}", response_class=Response)
async def jsonld_incident(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(_Q_INCIDENT_BY_CODE, code)
        if row is None:
            raise HTTPException(404)
        country_rows = await conn.fetch(_Q_INCIDENT_COUNTRIES, UUID(row["id"]))
    sum_c = sum(int(c["confirmed_count"] or 0) for c in country_rows)
    sum_d = sum(int(c["deaths"] or 0) for c in country_rows)
    started = row["started_at"]
    node = jsonld.event_incident(
        incident_code=row["code"],
        name=row["name"],
        summary=row["summary"],
        started_at=(datetime.combine(started, datetime.min.time(), tzinfo=timezone.utc) if started else None),
        ended_at=None,
        countries=[c["country_iso2"] for c in country_rows if c["country_iso2"]],
        status=row["status"],
        confirmed=sum_c,
        deaths=sum_d,
    )
    payload = {"@context": "https://schema.org", **node}
    import json as _json
    return FastResponse(
        content=_json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/ld+json",
        headers={
            "Cache-Control": "public, max-age=300",
            "Access-Control-Allow-Origin": "*",
            "X-Robots-Tag": "all",
        },
    )


# ============================================================================
# EMBEDDABLE WIDGETS (/widgets, /widgets/{type})
# ============================================================================
#
# Stand-alone HTML pages designed to be embedded on third-party sites via
# <iframe>. Each widget is small (under 30 KB), self-contained, and links
# back to HORIZON via attribution. The whole point: free backlinks at scale.
# Iframe-friendly (no X-Frame-Options DENY on these endpoints).


_WIDGET_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:transparent;color:#111114}
body{padding:14px}
.w{background:#fff;border:1px solid #22221e;border-radius:6px;padding:18px;max-width:540px}
.w h2{font-size:14px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px;color:#5a5a60;font-weight:600}
.w .num{font-size:42px;font-weight:800;letter-spacing:-0.024em;line-height:1;color:#111114}
.w .lbl{font-size:11.5px;text-transform:uppercase;letter-spacing:.1em;color:#5a5a60;margin-top:3px}
.w .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:12px;margin:8px 0 12px}
.w .attr{font-size:11.5px;color:#5a5a60;margin-top:10px;border-top:1px solid #e8e6df;padding-top:8px}
.w .attr a{color:#c2542a;text-decoration:none;font-weight:600}
.w .attr a:hover{text-decoration:underline}
.w ul{list-style:none;padding:0}
.w li{padding:6px 0;border-bottom:1px solid #f0eee8;font-size:13.5px}
.w li:last-child{border-bottom:none}
.w li a{color:#111114;text-decoration:none}
.w li a:hover{color:#c2542a}
.w .ts{display:block;color:#5a5a60;font-size:11px;margin-top:2px}
"""


def _widget_wrap(title: str, body_html: str) -> str:
    """Wrap widget body in a clean HTML document, iframe-friendly."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{esc(title)} · HORIZON</title>
<meta name="robots" content="noindex, nofollow" />
<style>{_WIDGET_CSS}</style>
</head>
<body>
<div class="w">
<h2>{esc(title)}</h2>
{body_html}
<div class="attr">Live data from <a href="https://hantavirus.software/" target="_blank" rel="noopener">HORIZON</a> · 79th Unit Limited · CC BY 4.0</div>
</div>
</body>
</html>
"""


@router.get("/widgets", response_class=HTMLResponse)
async def page_widgets() -> Response:
    body = """
<p class="lead">
Embeddable widgets for the live HORIZON data. Drop the iframe code into
any HTML page or CMS template. They render small (under 600px wide),
self-contained, branded, and update live. Use of these widgets is
permitted under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license external">CC BY 4.0</a>:
the attribution link in each widget satisfies the licence.
</p>

<h2>Counter widget</h2>
<p>Authoritative case + death totals for active hantavirus outbreaks.</p>
<pre><code>&lt;iframe src="https://hantavirus.software/widgets/counter"
        width="560" height="240" frameborder="0" loading="lazy"
        title="HORIZON hantavirus case counter"&gt;&lt;/iframe&gt;</code></pre>
<iframe src="/widgets/counter" width="560" height="240" frameborder="0" style="border:1px solid #22221e;border-radius:6px;margin-top:1em" title="HORIZON hantavirus case counter"></iframe>

<h2>Latest news widget</h2>
<p>Last five hantavirus reports ingested, with source and timestamp.</p>
<pre><code>&lt;iframe src="https://hantavirus.software/widgets/feed"
        width="560" height="420" frameborder="0" loading="lazy"
        title="HORIZON hantavirus news feed"&gt;&lt;/iframe&gt;</code></pre>
<iframe src="/widgets/feed" width="560" height="420" frameborder="0" style="border:1px solid #22221e;border-radius:6px;margin-top:1em" title="HORIZON hantavirus news feed"></iframe>

<h2>MV Hondius status widget</h2>
<p>Live status of the active MV Hondius cluster.</p>
<pre><code>&lt;iframe src="https://hantavirus.software/widgets/incident/mv-hondius-2026"
        width="560" height="280" frameborder="0" loading="lazy"
        title="HORIZON MV Hondius status"&gt;&lt;/iframe&gt;</code></pre>
<iframe src="/widgets/incident/mv-hondius-2026" width="560" height="280" frameborder="0" style="border:1px solid #22221e;border-radius:6px;margin-top:1em" title="HORIZON MV Hondius status"></iframe>

<h2>Attribution</h2>
<p>Each widget renders an attribution link back to <code>hantavirus.software</code>. That link is required by the CC BY 4.0 licence. Beyond that, no restrictions — embed widely.</p>
"""
    spec = PageSpec(
        path="/widgets",
        title="Embeddable Hantavirus Widgets — HORIZON",
        description="Drop-in iframe widgets showing live hantavirus case counts, latest news, and MV Hondius cluster status. CC BY 4.0.",
        h1="Embeddable Widgets",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Widgets", url=f"{BASE_URL}/widgets")],
        jsonld_nodes=[],
        keywords="hantavirus widget, embed hantavirus counter, iframe outbreak tracker, hantavirus dashboard widget",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/widgets/counter", response_class=HTMLResponse)
async def widget_counter() -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(
            """
            WITH latest AS (
                SELECT DISTINCT ON (incident_id) confirmed_cases, suspected_cases, deaths
                FROM incident_authoritative_counts iac
                JOIN incidents i ON i.id = iac.incident_id
                WHERE i.status IN ('active', 'monitoring')
                ORDER BY incident_id, nato_reliability, nato_credibility, reported_at DESC
            )
            SELECT
              COALESCE(SUM(confirmed_cases)::int, 0) AS conf,
              COALESCE(SUM(suspected_cases)::int, 0) AS susp,
              COALESCE(SUM(deaths)::int, 0)          AS deaths,
              (SELECT COUNT(*)::int FROM incidents WHERE status IN ('active','monitoring')) AS incidents
            FROM latest
            """
        )
    body = f"""
<div class="grid">
  <div><div class="num">{int(row["conf"] or 0)}</div><div class="lbl">Confirmed</div></div>
  <div><div class="num">{int(row["susp"] or 0)}</div><div class="lbl">Suspected</div></div>
  <div><div class="num">{int(row["deaths"] or 0)}</div><div class="lbl">Deaths</div></div>
  <div><div class="num">{int(row["incidents"] or 0)}</div><div class="lbl">Outbreaks</div></div>
</div>
"""
    return FastResponse(
        content=_widget_wrap("Live Hantavirus Counter", body),
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300, s-maxage=300",
            "X-Frame-Options": "ALLOWALL",
            "Content-Security-Policy": "frame-ancestors *;",
            "X-Robots-Tag": "noindex",
        },
    )


@router.get("/widgets/feed", response_class=HTMLResponse)
async def widget_feed() -> Response:
    async with acquire() as conn:
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        rows = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 5)
    items = "".join(
        f'<li><a href="https://hantavirus.software/articles/{esc(r["id"])}" target="_blank" rel="noopener">{esc(r["title"] or "Untitled")}</a>'
        f'<span class="ts">{esc(r["source_code"])} · {(r["reported_date"] or r["ingested_at"].date()).strftime("%Y-%m-%d")}'
        f'{" · " + country_name(r["country_iso2"]) if r["country_iso2"] else ""}</span></li>'
        for r in rows
    )
    body = f'<ul>{items}</ul>' if items else '<p style="color:#5a5a60">No recent reports.</p>'
    return FastResponse(
        content=_widget_wrap("Latest Hantavirus Reports", body),
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Frame-Options": "ALLOWALL",
            "Content-Security-Policy": "frame-ancestors *;",
            "X-Robots-Tag": "noindex",
        },
    )


@router.get("/widgets/incident/{code}", response_class=HTMLResponse)
async def widget_incident(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(_Q_INCIDENT_BY_CODE, code)
        if row is None:
            raise HTTPException(404)
        country_rows = await conn.fetch(_Q_INCIDENT_COUNTRIES, UUID(row["id"]))
    conf = sum(int(c["confirmed_count"] or 0) for c in country_rows)
    susp = sum(int(c["suspected_count"] or 0) for c in country_rows)
    deaths = sum(int(c["deaths"] or 0) for c in country_rows)
    countries = sum(1 for c in country_rows if int(c["confirmed_count"] or 0) > 0 or int(c["deaths"] or 0) > 0)
    body = f"""
<p style="font-size:13.5px;color:#5a5a60;margin-bottom:8px;text-transform:uppercase;letter-spacing:.06em;font-weight:600">
{esc(row["status"].upper())} · {esc(row["serotype_code"] or "—")}
</p>
<p style="font-size:18px;font-weight:700;margin-bottom:12px">{esc(row["name"])}</p>
<div class="grid">
  <div><div class="num">{conf}</div><div class="lbl">Confirmed</div></div>
  <div><div class="num">{susp}</div><div class="lbl">Suspected</div></div>
  <div><div class="num">{deaths}</div><div class="lbl">Deaths</div></div>
  <div><div class="num">{countries}</div><div class="lbl">Countries</div></div>
</div>
"""
    return FastResponse(
        content=_widget_wrap(f"{row['name']} — Live", body),
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Frame-Options": "ALLOWALL",
            "Content-Security-Policy": "frame-ancestors *;",
            "X-Robots-Tag": "noindex",
        },
    )


# ============================================================================
# WEBSUB HUB (/websub) — instant push notification for feed subscribers
# ============================================================================


@router.get("/websub", response_class=HTMLResponse)
async def page_websub() -> Response:
    body = """
<p class="lead">
HORIZON publishes its RSS/Atom feeds with WebSub hub discovery enabled.
Subscribe via your reader's WebSub-aware client, or ping the hub URL
below to receive push notifications the instant a new hantavirus
report is ingested.
</p>

<h2>Hub URL</h2>
<p><code>https://hantavirus.software/websub</code></p>

<h2>How to subscribe</h2>
<ol>
<li>Discover the hub from any HORIZON feed (RSS / Atom both include the <code>&lt;link rel="hub"&gt;</code> declaration).</li>
<li>Subscribe with topic URL <code>https://hantavirus.software/rss.xml</code> (or <code>/atom.xml</code>).</li>
<li>The hub will send a verification GET to your callback URL.</li>
<li>Reply with the <code>hub.challenge</code> echoed back. You're subscribed.</li>
<li>Every new ingestion fires a POST to your callback with the new feed entries.</li>
</ol>

<p class="muted">Note: HORIZON is currently configured to relay through the
<a href="https://websub.rocks">websub.rocks</a> reference hub. Direct hub-side
delivery is on the roadmap. Existing RSS/Atom polling remains the most
compatible subscription path.</p>

<p><a href="/rss.xml">/rss.xml</a> · <a href="/atom.xml">/atom.xml</a> · <a href="/feed.json">/feed.json</a></p>
"""
    spec = PageSpec(
        path="/websub",
        title="WebSub Hub — Instant Push for HORIZON Feed Subscribers",
        description="WebSub hub URL and subscription instructions for HORIZON RSS/Atom feeds. Receive push notifications the moment a new hantavirus report is ingested.",
        h1="WebSub Hub",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="WebSub", url=f"{BASE_URL}/websub")],
        jsonld_nodes=[],
        keywords="HORIZON WebSub, RSS push, Atom push, hantavirus feed subscriber, real-time hantavirus alerts",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


# ============================================================================
# BRAZILIAN PORTUGUESE SURFACE (/pt-br/)
# ============================================================================
#
# Mirrors the Spanish layout. Brazil is one of the most hantavirus-endemic
# countries (Juquitiba, Araraquara, Castelo dos Sonhos, Anajatuba serotypes
# circulate; SP, MS, RS, SC, PR are endemic states). pt-BR demand for
# "hantavirose sintomas", "síndrome cardiopulmonar por hantavírus" is
# huge and current pt-BR tracker coverage is essentially zero.
# ============================================================================


def _home_crumb_pt() -> Breadcrumb:
    return Breadcrumb(name="HORIZON", url=f"{BASE_URL}/pt-br/")


@router.get("/pt-br", response_class=HTMLResponse)
@router.get("/pt-br/", response_class=HTMLResponse)
async def page_pt_home() -> Response:
    body = f"""
<p class="lead">
HORIZON é uma plataforma de vigilância de surtos de hantavírus em tempo
real com procedência de fonte em nível de auditoria. Agregamos sinais
da Organização Mundial da Saúde (OMS), da Organização Pan-Americana da
Saúde (OPAS), dos Centros de Controle e Prevenção de Doenças dos EUA
(CDC), do Centro Europeu para Prevenção e Controle de Doenças (ECDC),
do ProMED, de autoridades nacionais, literatura revisada por pares e
notícias abertas.
</p>

{i18n_pt.PT_CTA_LIVE_MAP}

<h2>Surto ativo</h2>
<p><a href="/pt-br/surtos/mv-hondius-2026"><strong>MV Hondius 2026</strong></a> — vírus Andes, exposição suspeita em Ushuaia (Terra do Fogo, Argentina). Sob monitoramento de OMS, OPAS, CDC, ECDC e Ministério da Saúde argentino.</p>

<h2>Tópicos principais</h2>
<div class="cards">
<article class="card"><h3><a href="/pt-br/hantavirus">O que é o hantavírus</a></h3><p>Família de vírus de roedores com duas síndromes clínicas: SCPH e FHSR.</p></article>
<article class="card"><h3><a href="/pt-br/hantavirus/sintomas">Sintomas</a></h3><p>Pródromo gripal, evolução para SCPH ou FHSR, critérios para procurar atendimento.</p></article>
<article class="card"><h3><a href="/pt-br/hantavirus/transmissao">Transmissão</a></h3><p>Aerossóis de excretas de roedores; ANDV com transmissão pessoa-pessoa.</p></article>
<article class="card"><h3><a href="/pt-br/hantavirus/prevencao">Prevenção</a></h3><p>Controle de roedores, protocolos de limpeza segura, equipamento de proteção.</p></article>
<article class="card"><h3><a href="/pt-br/hantavirus/virus-andes">Vírus Andes</a></h3><p>O sorotipo mais letal das Américas; único com transmissão pessoa-pessoa.</p></article>
</div>

<h2>Dados abertos</h2>
<p>Todos os dados estão disponíveis sob CC BY 4.0 via a <a href="/api/openapi.json">API JSON</a> ou assinatura <a href="/rss.xml">RSS</a>/<a href="/atom.xml">Atom</a>.</p>

{i18n_pt.PT_CTA_LIVE_MAP}
"""
    spec = PageSpec(
        path="/pt-br/",
        title="HORIZON — Rastreador de Surtos de Hantavírus em Tempo Real",
        description=(
            "Vigilância em tempo real de surtos de hantavírus com procedência "
            "de fonte em nível de auditoria. OMS, OPAS, CDC, ECDC, ProMED. "
            "Mapa, cronologia e ontologia do surto MV Hondius 2026."
        ),
        h1="Rastreador de Surtos de Hantavírus em Tempo Real",
        body_html=body,
        breadcrumbs=[_home_crumb_pt()],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="hantavirus, hantavirose, vírus Andes, ANDV, Sin Nombre, MV Hondius, OMS, OPAS, CDC, ECDC, surto, Brasil",
        news_keywords="hantavirus, hantavirose, surto, ANDV, MV Hondius",
        og_type="website",
        locale="pt-BR",
        hreflang_path="/",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/pt-br/hantavirus", response_class=HTMLResponse)
async def page_pt_hantavirus() -> Response:
    spec = PageSpec(
        path="/pt-br/hantavirus",
        title="Hantavírus — Sintomas, Sorotipos, Transmissão, Surtos (2026) · HORIZON",
        description=(
            "Referência completa sobre a doença por hantavírus: 12 sorotipos "
            "de orthohantavírus, síndromes SCPH e FHSR, transmissão, prevenção, "
            "tratamento e vigilância em tempo real de OMS, OPAS, CDC e ECDC. "
            "Inclui sorotipos brasileiros: Juquitiba, Araraquara, Anajatuba."
        ),
        h1="Hantavírus — Vigilância e Referência em Tempo Real",
        body_html=i18n_pt.PT_HANTAVIRUS_HUB_BODY,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Hantavírus", url=f"{BASE_URL}/pt-br/hantavirus"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/pt-br/hantavirus",
                "Hantavírus — Vigilância e Referência",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus, hantavirose, vírus Andes, Sin Nombre, Juquitiba, Araraquara, SCPH, FHSR, surto, Brasil",
        news_keywords="hantavirus, hantavirose, surto",
        locale="pt-BR",
        hreflang_path="/hantavirus",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=900)


@router.get("/pt-br/hantavirus/sintomas", response_class=HTMLResponse)
async def page_pt_symptoms() -> Response:
    spec = PageSpec(
        path="/pt-br/hantavirus/sintomas",
        title="Sintomas do Hantavírus — SCPH vs FHSR, Pródromo, Tríade · HORIZON",
        description=(
            "Evolução clínica detalhada do hantavírus: incubação 1–8 semanas, "
            "pródromo gripal, depois SCPH (colapso pulmonar, letalidade 30–50%) "
            "ou FHSR (falência renal). Diagnóstico diferencial. Inclui sorotipo "
            "Araraquara brasileiro (letalidade 40-50%)."
        ),
        h1="Sintomas do Hantavírus — Curso Clínico de SCPH e FHSR",
        body_html=i18n_pt.PT_SYMPTOMS_BODY,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Hantavírus", url=f"{BASE_URL}/pt-br/hantavirus"),
            Breadcrumb(name="Sintomas", url=f"{BASE_URL}/pt-br/hantavirus/sintomas"),
        ],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
            jsonld.medical_web_page(
                f"{BASE_URL}/pt-br/hantavirus/sintomas",
                "Sintomas do Hantavírus",
                f"{BASE_URL}/hantavirus#condition",
            ),
        ],
        keywords="hantavirus sintomas, hantavirose sintomas, SCPH sintomas, FHSR sintomas, hantavirose pródromo, Araraquara",
        locale="pt-BR",
        hreflang_path="/hantavirus/symptoms",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/pt-br/hantavirus/transmissao", response_class=HTMLResponse)
async def page_pt_transmission() -> Response:
    spec = PageSpec(
        path="/pt-br/hantavirus/transmissao",
        title="Transmissão do Hantavírus — Aerossóis de Roedores, ANDV Pessoa-Pessoa · HORIZON",
        description=(
            "Como o hantavírus se propaga: inalação de excretas aerossolizadas. "
            "O vírus Andes é o único orthohantavírus com transmissão "
            "pessoa-pessoa documentada. Mapa de espécies reservatório."
        ),
        h1="Transmissão do Hantavírus",
        body_html=i18n_pt.PT_TRANSMISSION_BODY,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Hantavírus", url=f"{BASE_URL}/pt-br/hantavirus"),
            Breadcrumb(name="Transmissão", url=f"{BASE_URL}/pt-br/hantavirus/transmissao"),
        ],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="hantavirus transmissão, como se pega hantavirose, vírus Andes pessoa-pessoa, aerossol roedor",
        locale="pt-BR",
        hreflang_path="/hantavirus/transmission",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/pt-br/hantavirus/prevencao", response_class=HTMLResponse)
async def page_pt_prevention() -> Response:
    spec = PageSpec(
        path="/pt-br/hantavirus/prevencao",
        title="Prevenção do Hantavírus — Controle de Roedores, Limpeza, N95 · HORIZON",
        description=(
            "Prevenção do hantavírus baseada em evidência: exclusão de roedores, "
            "protocolo seguro de limpeza com água sanitária 1:10 e respirador "
            "N95/FFP3, precauções de viagem em áreas endêmicas no Brasil."
        ),
        h1="Prevenção do Hantavírus",
        body_html=i18n_pt.PT_PREVENTION_BODY,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Hantavírus", url=f"{BASE_URL}/pt-br/hantavirus"),
            Breadcrumb(name="Prevenção", url=f"{BASE_URL}/pt-br/hantavirus/prevencao"),
        ],
        jsonld_nodes=[jsonld.medical_condition_hantavirus()],
        keywords="prevenção hantavirus, controle de roedores, limpeza segura, N95 hantavirose, vacina hantavirus",
        locale="pt-BR",
        hreflang_path="/hantavirus/prevention",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


_PT_SEROTYPE_URL_MAP = {
    "virus-andes": "andes-virus",
    "sin-nombre":  "sin-nombre-virus",
    "puumala":     "puumala-virus",
    "hantaan":     "hantaan-virus",
    "seoul":       "seoul-virus",
}


@router.get("/pt-br/hantavirus/{pt_slug}", response_class=HTMLResponse)
async def page_pt_serotype(pt_slug: str) -> Response:
    if pt_slug in {"sintomas", "transmissao", "prevencao", "tratamento"}:
        raise HTTPException(404)
    en_slug = _PT_SEROTYPE_URL_MAP.get(pt_slug)
    if en_slug is None:
        raise HTTPException(404, f"Sorotipo desconhecido: {pt_slug!r}")
    s_en = serotype_by_slug(en_slug)
    if s_en is None:
        raise HTTPException(404)
    s_pt = i18n_pt.PT_SEROTYPE_PROSE.get(pt_slug)

    body = i18n_pt.render_pt_serotype_body(s_en, s_pt)
    name = s_pt["name"] if s_pt else s_en["name"]

    spec = PageSpec(
        path=f"/pt-br/hantavirus/{pt_slug}",
        title=f"{name} — Reservatório, Endemia, Letalidade · HORIZON",
        description=(
            f"{name}: {(s_pt or s_en).get('syndrome', s_en['syndrome'])}, "
            f"reservatório {(s_pt or s_en).get('reservoir', s_en['reservoir'])}, "
            f"endêmico em {(s_pt or s_en).get('endemic', s_en['endemic'])}. "
            f"Letalidade {(s_pt or s_en).get('cfr', s_en['cfr'])}."
        ),
        h1=name,
        body_html=body,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Hantavírus", url=f"{BASE_URL}/pt-br/hantavirus"),
            Breadcrumb(name=name, url=f"{BASE_URL}/pt-br/hantavirus/{pt_slug}"),
        ],
        jsonld_nodes=[
            jsonld.serotype_node(s_en),
            jsonld.medical_web_page(
                f"{BASE_URL}/pt-br/hantavirus/{pt_slug}",
                name,
                f"{BASE_URL}/hantavirus/{en_slug}#condition",
            ),
        ],
        keywords=f"{name}, {s_en['code']}, hantavirus, hantavirose, orthohantavirus",
        locale="pt-BR",
        hreflang_path=f"/hantavirus/{en_slug}",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=3600)


@router.get("/pt-br/perguntas-frequentes", response_class=HTMLResponse)
async def page_pt_faq() -> Response:
    spec = PageSpec(
        path="/pt-br/perguntas-frequentes",
        title="Perguntas Frequentes sobre Hantavírus · HORIZON",
        description=(
            "Perguntas frequentes sobre a doença por hantavírus, o surto do "
            "MV Hondius 2026, hantavirose no Brasil (Juquitiba, Araraquara) "
            "e a plataforma HORIZON."
        ),
        h1="Perguntas Frequentes",
        body_html=i18n_pt.render_pt_faq_body(),
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="FAQ", url=f"{BASE_URL}/pt-br/perguntas-frequentes"),
        ],
        jsonld_nodes=[
            jsonld.faq_page_from_entries(f"{BASE_URL}/pt-br/perguntas-frequentes", i18n_pt.PT_FAQ_ENTRIES),
        ],
        keywords="hantavirus FAQ Brasil, perguntas frequentes hantavirose, MV Hondius perguntas",
        locale="pt-BR",
        hreflang_path="/faq",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)


@router.get("/pt-br/surtos/{code}", response_class=HTMLResponse)
async def page_pt_incident(code: str) -> Response:
    async with acquire() as conn:
        row = await conn.fetchrow(_Q_INCIDENT_BY_CODE, code)
        if row is None:
            raise HTTPException(404)
        country_rows = await conn.fetch(_Q_INCIDENT_COUNTRIES, UUID(row["id"]))

    sum_c = sum(int(c["confirmed_count"] or 0) for c in country_rows)
    sum_s = sum(int(c["suspected_count"] or 0) for c in country_rows)
    sum_d = sum(int(c["deaths"] or 0) for c in country_rows)

    countries_table = "".join(
        f'<tr><th>{esc(country_name(c["country_iso2"]))}</th>'
        f'<td>{int(c["confirmed_count"] or 0)} confirmados</td>'
        f'<td>{int(c["suspected_count"] or 0)} suspeitos</td>'
        f'<td>{int(c["deaths"] or 0)} óbitos</td></tr>'
        for c in country_rows
    )

    status_pt = {"active": "ATIVO", "monitoring": "MONITORAMENTO", "resolved": "RESOLVIDO"}.get(row["status"], row["status"].upper())

    body_html = (
        f'<p><span class="tag {"alert" if row["status"] == "active" else ""}">{esc(status_pt)}</span> '
        f'<span class="kv">{esc(row["serotype_code"] or "—")}</span></p>'
        f'<p class="lead">{esc(row["summary"] or "")}</p>'
        '<div class="stats">'
        f'<div class="stat"><div class="n">{sum_c}</div><div class="l">Confirmados</div></div>'
        f'<div class="stat"><div class="n">{sum_s}</div><div class="l">Suspeitos</div></div>'
        f'<div class="stat"><div class="n">{sum_d}</div><div class="l">Óbitos</div></div>'
        '</div>'
        + ('<h2>Distribuição por país</h2><table class="facts"><tr><th>País</th><th>Confirmados</th><th>Suspeitos</th><th>Óbitos</th></tr>' + countries_table + '</table>' if countries_table else '')
        + '<p><a class="cta" href="/">Abrir o mapa de surtos em tempo real →</a></p>'
    )

    spec = PageSpec(
        path=f"/pt-br/surtos/{code}",
        title=f'{row["name"]} — Surto de Hantavírus · HORIZON',
        description=(row["summary"] or row["name"])[:220],
        h1=row["name"],
        body_html=body_html,
        breadcrumbs=[
            _home_crumb_pt(),
            Breadcrumb(name="Surtos", url=f"{BASE_URL}/pt-br/surtos"),
            Breadcrumb(name=row["name"], url=f"{BASE_URL}/pt-br/surtos/{code}"),
        ],
        jsonld_nodes=[
            jsonld.event_incident(
                incident_code=row["code"],
                name=row["name"],
                summary=row["summary"],
                started_at=(datetime.combine(row["started_at"], datetime.min.time(), tzinfo=timezone.utc) if row["started_at"] else None),
                ended_at=None,
                countries=[c["country_iso2"] for c in country_rows if c["country_iso2"]],
                status=row["status"],
                confirmed=sum_c,
                deaths=sum_d,
            ),
        ],
        keywords=f'{row["name"]}, surto hantavirus, hantavirose, {row["serotype_code"]}',
        news_keywords=f'{row["name"]}, hantavirose, surto',
        locale="pt-BR",
        hreflang_path=f"/outbreaks/{code}",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=600)


# ============================================================================
# CRAWLER PRE-RENDERED SNAPSHOT (/seo-snapshot)
# ============================================================================
#
# When a known crawler User-Agent hits `/`, nginx routes them here. This
# endpoint returns a fully-populated static HTML snapshot of the homepage
# with live stats baked in — so Googlebot, Bingbot, etc. see real content
# (counts, country list, latest articles) instead of the React SPA shell.
#
# Real users still get the SPA at `/` (better UX). Crawlers get the
# snapshot (better indexing). This is Google's officially-supported
# "Dynamic Rendering" pattern.
# ============================================================================


@router.get("/seo-snapshot", response_class=HTMLResponse)
async def page_seo_snapshot() -> Response:
    async with acquire() as conn:
        stats = await conn.fetchrow(
            """
            WITH latest AS (
                SELECT DISTINCT ON (incident_id) confirmed_cases, suspected_cases, deaths
                FROM incident_authoritative_counts iac
                JOIN incidents i ON i.id = iac.incident_id
                WHERE i.status IN ('active', 'monitoring')
                ORDER BY incident_id, nato_reliability, nato_credibility, reported_at DESC
            )
            SELECT
              COALESCE(SUM(confirmed_cases)::int, 0) AS conf,
              COALESCE(SUM(suspected_cases)::int, 0) AS susp,
              COALESCE(SUM(deaths)::int, 0) AS deaths,
              (SELECT COUNT(*)::int FROM incidents WHERE status IN ('active','monitoring')) AS incidents,
              (SELECT COUNT(*)::int FROM case_reports) AS reports,
              (SELECT COUNT(DISTINCT country_iso2)::int FROM case_reports WHERE country_iso2 IS NOT NULL) AS countries,
              (SELECT COUNT(*)::int FROM sources WHERE enabled) AS sources
            FROM latest
            """
        )
        incident_rows = await conn.fetch(_Q_INCIDENTS)
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        recent = await conn.fetch(_Q_RECENT_ARTICLES, cutoff, 10)

    incidents_html = "".join(
        f'<li><a href="/outbreaks/{esc(r["code"])}"><strong>{esc(r["name"])}</strong></a> '
        f'<span class="kv">— {esc(r["status"].upper())} · {int(r["sum_confirmed"] or 0)} confirmed · {int(r["sum_deaths"] or 0)} deaths</span></li>'
        for r in incident_rows
    )

    articles_html = "".join(
        f'<li><a href="/articles/{esc(r["id"])}">{esc(r["title"] or "Untitled")}</a> '
        f'<span class="kv">— {esc(r["source_code"])} · {(r["reported_date"] or r["ingested_at"].date()).strftime("%Y-%m-%d")}</span></li>'
        for r in recent
    )

    body = f"""
<p class="lead">
HORIZON is the most comprehensive live hantavirus outbreak surveillance
platform on the public internet. Real-time aggregation of WHO, CDC, ECDC,
PAHO, ProMED, peer-reviewed literature, and open news. Audit-grade source
provenance on every record: NATO Admiralty Scale rating, ICD 206 source
citation, dual-confidence model, Berkeley Protocol chain-of-custody hash.
</p>

<div class="stats">
<div class="stat"><div class="n">{int(stats["conf"] or 0)}</div><div class="l">Confirmed cases</div></div>
<div class="stat"><div class="n">{int(stats["susp"] or 0)}</div><div class="l">Suspected</div></div>
<div class="stat"><div class="n">{int(stats["deaths"] or 0)}</div><div class="l">Deaths</div></div>
<div class="stat"><div class="n">{int(stats["incidents"] or 0)}</div><div class="l">Active outbreaks</div></div>
<div class="stat"><div class="n">{int(stats["countries"] or 0)}</div><div class="l">Countries reporting</div></div>
<div class="stat"><div class="n">{int(stats["sources"] or 0)}</div><div class="l">Live sources</div></div>
<div class="stat"><div class="n">{int(stats["reports"] or 0)}</div><div class="l">Reports indexed</div></div>
</div>

<h2>Active outbreaks</h2>
<ul>{incidents_html}</ul>

<h2>Latest reports</h2>
<ul>{articles_html}</ul>

<h2>Available content</h2>
<ul>
<li><a href="/hantavirus">Hantavirus — comprehensive medical reference</a> (12 serotypes, 4 clinical topic pages)</li>
<li><a href="/outbreaks">Live outbreak index</a></li>
<li><a href="/countries">Country-by-country surveillance</a></li>
<li><a href="/articles">Live article feed</a> with NATO source qualification</li>
<li><a href="/chronology">90-day chronology</a> as a live blog</li>
<li><a href="/compare">Clinical comparison pages</a></li>
<li><a href="/sources">Source registry</a> (every WHO/CDC/ECDC/PAHO feed with NATO rating)</li>
<li><a href="/methodology">Methodology</a> — NATO Admiralty Scale, ICD 206, Berkeley Protocol</li>
<li><a href="/glossary">Glossary</a> — hantavirus + OSINT tradecraft terminology</li>
<li><a href="/faq">FAQ</a></li>
</ul>

<h2>Spanish + Portuguese</h2>
<ul>
<li><a href="/es/" hreflang="es">Español</a> — full hantavirus reference and incident pages for LatAm readers</li>
<li><a href="/pt-br/" hreflang="pt-BR">Português brasileiro</a> — Brazilian medical vocabulary, includes Juquitiba/Araraquara serotype context</li>
</ul>

<h2>Open data + feeds</h2>
<ul>
<li>API: <a href="/api/openapi.json">/api/openapi.json</a></li>
<li>RSS: <a href="/rss.xml">/rss.xml</a></li>
<li>Atom: <a href="/atom.xml">/atom.xml</a></li>
<li>JSON Feed: <a href="/feed.json">/feed.json</a></li>
<li>Sitemap: <a href="/sitemap.xml">/sitemap.xml</a> · News sitemap: <a href="/news-sitemap.xml">/news-sitemap.xml</a></li>
<li>Embeddable widgets: <a href="/widgets">/widgets</a></li>
</ul>

<p><a class="cta" href="/">Open the interactive map →</a></p>
"""
    spec = PageSpec(
        path="/seo-snapshot",
        title="HORIZON — Live Hantavirus Outbreak Tracker (snapshot for indexing)",
        description=(
            "Server-rendered crawler-friendly snapshot of the HORIZON homepage. "
            "Live hantavirus outbreak counts, active incidents, latest reports, "
            "all topic clusters, EN/ES/PT-BR coverage, audit-grade provenance."
        ),
        h1="HORIZON — Live Hantavirus Outbreak Tracker",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/")],
        jsonld_nodes=[
            jsonld.medical_condition_hantavirus(),
        ],
        keywords="hantavirus tracker, live hantavirus outbreak, hantavirus surveillance, hantavirus map, WHO, CDC, ECDC, PAHO",
        news_keywords="hantavirus, outbreak, surveillance, MV Hondius",
        og_type="website",
        hreflang_path="/",
    )
    # Short cache so live numbers refresh; crawlers don't need second-by-second freshness.
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=300)


# ============================================================================
# PER-PAGE DYNAMIC OG IMAGE (/api/v1/og/{slug}.png)
# ============================================================================


@router.get("/api/v1/og/{slug}.png", response_class=Response)
async def og_image_dynamic(slug: str) -> Response:
    """Generate a 1200x630 OG image per page slug. Pillow-rendered, cacheable.

    Slug examples: 'hantavirus', 'mv-hondius-2026', 'es-hantavirus',
    'andes-virus', 'symptoms'. The slug determines the title + subtitle.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError:
        raise HTTPException(503, "Pillow not installed; OG image rendering unavailable")

    import io
    import os

    titles: dict[str, tuple[str, str]] = {
        "default":           ("Live Hantavirus", "Outbreak Tracker"),
        "hantavirus":        ("Hantavirus", "Symptoms · Transmission · Treatment"),
        "symptoms":          ("Hantavirus Symptoms", "HPS vs HFRS clinical course"),
        "transmission":      ("Hantavirus Transmission", "Rodent aerosol · Andes P2P"),
        "prevention":        ("Hantavirus Prevention", "Rodent control · safe cleaning"),
        "treatment":         ("Hantavirus Treatment", "ICU · ECMO · ribavirin"),
        "andes-virus":       ("Andes Virus (ANDV)", "HPS 30–50% CFR · P2P documented"),
        "sin-nombre-virus":  ("Sin Nombre Virus (SNV)", "Four Corners 1993 · ~38% CFR"),
        "puumala-virus":     ("Puumala Virus (PUUV)", "Europe's commonest HFRS"),
        "hantaan-virus":     ("Hantaan Virus (HTNV)", "Severe HFRS · East Asia"),
        "seoul-virus":       ("Seoul Virus (SEOV)", "Mild HFRS · global Rattus"),
        "mv-hondius-2026":   ("MV Hondius Cluster", "Andes virus · 2026 polar expedition"),
        "outbreaks":         ("Hantavirus Outbreaks", "Live cluster tracker"),
        "countries":         ("Hantavirus by Country", "Per-country case chronology"),
        "chronology":        ("Hantavirus Chronology", "90-day live blog"),
        "sources":           ("HORIZON Source Registry", "NATO Admiralty Scale rated"),
        "methodology":       ("HORIZON Methodology", "ICD 206 · Berkeley Protocol"),
        "glossary":          ("Hantavirus Glossary", "Tradecraft + virology"),
        "faq":               ("Hantavirus FAQ", "Symptoms · transmission · MV Hondius"),
        "compare":                          ("Hantavirus Comparisons", "ANDV vs SNV · HPS vs HFRS"),
        "compare-hantavirus-live-trackers": ("Live Tracker Comparison", "HORIZON vs hantavirus.live vs hanta-live"),
        "es-hantavirus":                    ("Hantavirus", "Síntomas · Transmisión · Tratamiento"),
        "pt-hantavirus":     ("Hantavírus", "Sintomas · Transmissão · Tratamento"),
    }
    title_top, subtitle = titles.get(slug, titles["default"])

    W, H = 1200, 630
    BG = (241, 239, 233)
    INK = (17, 17, 20)
    MUTED = (90, 90, 96)
    ACCENT = (194, 84, 42)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    def _font(size: int, bold: bool = False) -> Any:
        candidates = []
        if bold:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            ]
        else:
            candidates += [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
            ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    pass
        return ImageFont.load_default()

    # Top accent strip
    d.rectangle((0, 0, W, 14), fill=ACCENT)
    # Bottom strip
    d.rectangle((0, H - 10, W, H), fill=INK)

    # Brand
    d.text((60, 56), "HORIZON", fill=INK, font=_font(34, True))
    d.text((232, 66), "· hantavirus.software", fill=MUTED, font=_font(18))

    # Title (auto-shrink if too long)
    title_size = 76
    while title_size > 38:
        f = _font(title_size, True)
        try:
            w = d.textlength(title_top, font=f)
        except AttributeError:
            w = len(title_top) * title_size * 0.55
        if w < W - 320:
            break
        title_size -= 6
    d.text((60, 180), title_top, fill=INK, font=_font(title_size, True))

    # Subtitle
    sub_size = 36
    while sub_size > 22:
        f = _font(sub_size)
        try:
            w = d.textlength(subtitle, font=f)
        except AttributeError:
            w = len(subtitle) * sub_size * 0.55
        if w < W - 320:
            break
        sub_size -= 4
    d.text((60, 290), subtitle, fill=ACCENT, font=_font(sub_size, True))

    # Provenance line
    d.text((60, 420), "Audit-grade source provenance", fill=INK, font=_font(22, True))
    d.text((60, 454), "WHO · CDC · ECDC · PAHO · ProMED · peer-reviewed", fill=MUTED, font=_font(22))

    # Foot
    d.text((60, 545), "Open data · CC BY 4.0 · 79th Unit Limited", fill=MUTED, font=_font(18))

    # Right-side outbreak marker (concentric rings)
    cx, cy = W - 220, H // 2 - 30
    for r, alpha in [(118, 60), (94, 110), (76, 220)]:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*ACCENT, alpha))
        img.paste(overlay, (0, 0), overlay)

    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return FastResponse(
        content=out.getvalue(),
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400, s-maxage=86400",
            "X-Robots-Tag": "all, max-image-preview:large",
        },
    )


# ============================================================================
# STRUCTURED-DATA VALIDATOR (/seo-validate)
# ============================================================================


@router.get("/seo-validate", response_class=HTMLResponse)
async def page_seo_validate() -> Response:
    body = """
<p class="lead">
Quick references for validating HORIZON's structured data, accessibility,
performance, and indexability against external tools. Bookmark this page.
</p>

<h2>Structured data (schema.org)</h2>
<ul>
<li><a href="https://search.google.com/test/rich-results?url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">Google Rich Results Test</a></li>
<li><a href="https://validator.schema.org/#url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">schema.org Validator</a></li>
<li><a href="https://yandex.com/dev/turbo/test/?url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">Yandex Turbo Test</a></li>
</ul>

<h2>Performance + Core Web Vitals</h2>
<ul>
<li><a href="https://pagespeed.web.dev/report?url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">PageSpeed Insights (Google)</a></li>
<li><a href="https://www.webpagetest.org/?url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">WebPageTest</a></li>
</ul>

<h2>Mobile + accessibility</h2>
<ul>
<li><a href="https://search.google.com/test/mobile-friendly?url=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">Google Mobile-Friendly Test</a></li>
<li><a href="https://wave.webaim.org/report#/https://hantavirus.software/" target="_blank" rel="noopener">WAVE accessibility report</a></li>
</ul>

<h2>Security headers + TLS</h2>
<ul>
<li><a href="https://observatory.mozilla.org/analyze/hantavirus.software" target="_blank" rel="noopener">Mozilla Observatory</a></li>
<li><a href="https://securityheaders.com/?q=hantavirus.software" target="_blank" rel="noopener">SecurityHeaders.com</a></li>
<li><a href="https://www.ssllabs.com/ssltest/analyze.html?d=hantavirus.software" target="_blank" rel="noopener">SSL Labs</a></li>
</ul>

<h2>Open Graph + social</h2>
<ul>
<li><a href="https://www.opengraph.xyz/url/https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">OpenGraph.xyz preview</a></li>
<li><a href="https://developers.facebook.com/tools/debug/?q=https%3A%2F%2Fhantavirus.software%2F" target="_blank" rel="noopener">Facebook OG Debugger</a></li>
<li><a href="https://cards-dev.twitter.com/validator" target="_blank" rel="noopener">Twitter Card Validator</a></li>
<li><a href="https://www.linkedin.com/post-inspector/" target="_blank" rel="noopener">LinkedIn Post Inspector</a></li>
</ul>

<h2>Sitemaps + feeds</h2>
<ul>
<li><a href="https://hantavirus.software/sitemap.xml" target="_blank" rel="noopener">/sitemap.xml</a> (sitemap-index)</li>
<li><a href="https://hantavirus.software/news-sitemap.xml" target="_blank" rel="noopener">/news-sitemap.xml</a> (Google News)</li>
<li><a href="https://hantavirus.software/rss.xml" target="_blank" rel="noopener">/rss.xml</a></li>
<li><a href="https://www.feedvalidator.org/check.cgi?url=https%3A%2F%2Fhantavirus.software%2Frss.xml" target="_blank" rel="noopener">RSS validator</a></li>
</ul>
"""
    spec = PageSpec(
        path="/seo-validate",
        title="SEO + Structured Data Validators · HORIZON",
        description="One-click links to external validators for HORIZON's structured data, performance, security, and social previews.",
        h1="SEO Validators",
        body_html=body,
        breadcrumbs=[Breadcrumb(name="HORIZON", url=f"{BASE_URL}/"), Breadcrumb(name="Validators", url=f"{BASE_URL}/seo-validate")],
        jsonld_nodes=[],
        keywords="HORIZON SEO validation, rich results test, structured data validator, lighthouse hantavirus",
        robots="noindex, follow",
    )
    return _cache_response(render_page(spec), "text/html; charset=utf-8", max_age=86400)
