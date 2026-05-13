"""Mock HORIZON API for visual verification of the frontend.

Serves canned data on http://localhost:8000 so the React UI at :5173 can render
populated Cases + Sources tabs without needing Docker, Postgres, or Celery.

Run from repo root:
    python scripts/mock_api.py

Then refresh http://localhost:5173 in your browser.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

TICK_SECONDS = 10

PORT = 8000


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def utc_offset_iso(*, hours_ago: int = 0, minutes_ago: int = 0) -> str:
    return (datetime.now(tz=UTC) - timedelta(hours=hours_ago, minutes=minutes_ago)).isoformat(
        timespec="seconds"
    )


def date_offset_iso(days_ago: int) -> str:
    return (datetime.now(tz=UTC) - timedelta(days=days_ago)).date().isoformat()


def _source(
    code: str,
    name: str,
    tier: int,
    provenance: str,
    rel: str,
    cred: int,
    *,
    enabled: bool = True,
    fetched_min_ago: int = 12,
    latency_ms: int = 400,
    http: int = 200,
    ingested: int = 0,
) -> dict[str, Any]:
    """Build a realistic source row for the mock dashboard."""
    return {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": name,
        "tier": tier,
        "provenance_type": provenance,
        "nato_reliability": rel,
        "nato_credibility": cred,
        "enabled": enabled,
        "last_fetched_at": utc_offset_iso(minutes_ago=fetched_min_ago) if enabled else None,
        "last_http_status": http if enabled else None,
        "last_latency_ms": latency_ms if enabled else None,
        "total_items_ingested": ingested,
    }


# Sources: matches migration 003 + 004 (16 connectors, all enabled in Phase 2).
SOURCES: list[dict[str, Any]] = [
    # Tier 1: official health authorities
    _source(
        "who-don",
        "WHO Disease Outbreak News",
        1,
        "official-authority",
        "A",
        1,
        fetched_min_ago=42,
        latency_ms=812,
        ingested=2,
    ),
    _source(
        "cdc-han",
        "CDC Health Alert Network",
        1,
        "official-authority",
        "A",
        1,
        fetched_min_ago=18,
        latency_ms=345,
        ingested=1,
    ),
    _source(
        "cdc-mmwr",
        "CDC MMWR",
        1,
        "official-authority",
        "A",
        1,
        fetched_min_ago=95,
        latency_ms=512,
        ingested=3,
    ),
    _source(
        "ecdc-tessy",
        "ECDC Surveillance Atlas of Infectious Diseases",
        1,
        "official-authority",
        "A",
        1,
        fetched_min_ago=22,
        latency_ms=1240,
        ingested=2,
    ),
    _source(
        "paho-alerts",
        "PAHO Epidemiological Alerts",
        1,
        "official-authority",
        "A",
        1,
        fetched_min_ago=14,
        latency_ms=687,
        ingested=4,
    ),
    _source(
        "nmh-data",
        "New Mexico Department of Health HPS",
        1,
        "official-authority",
        "A",
        2,
        fetched_min_ago=140,
        latency_ms=298,
        ingested=1,
    ),
    # Tier 2: outbreak intel + aggregators
    _source(
        "promed-rss",
        "ProMED-mail",
        2,
        "aggregator",
        "B",
        2,
        fetched_min_ago=8,
        latency_ms=487,
        ingested=12,
    ),
    _source(
        "healthmap",
        "HealthMap (Boston Children Hospital)",
        2,
        "aggregator",
        "B",
        2,
        fetched_min_ago=16,
        latency_ms=621,
        ingested=7,
    ),
    # Tier 3: news + social
    _source(
        "google-news",
        "Google News (hantavirus query)",
        3,
        "aggregator",
        "C",
        3,
        fetched_min_ago=4,
        latency_ms=312,
        ingested=23,
    ),
    _source(
        "gdelt",
        "GDELT 2.0 Global Knowledge Graph",
        3,
        "aggregator",
        "C",
        2,
        fetched_min_ago=11,
        latency_ms=445,
        ingested=18,
    ),
    _source(
        "reddit",
        "Reddit (hantavirus search)",
        3,
        "social-rumour",
        "E",
        4,
        fetched_min_ago=24,
        latency_ms=287,
        ingested=6,
    ),
    # Tier 4: academic + research
    _source(
        "arxiv",
        "arXiv preprint server (q-bio)",
        4,
        "peer-reviewed",
        "B",
        2,
        fetched_min_ago=215,
        latency_ms=540,
        ingested=0,
    ),
    _source(
        "biorxiv",
        "bioRxiv preprint server",
        4,
        "peer-reviewed",
        "B",
        2,
        fetched_min_ago=180,
        latency_ms=478,
        ingested=1,
    ),
    _source(
        "medrxiv",
        "medRxiv preprint server",
        4,
        "peer-reviewed",
        "B",
        2,
        fetched_min_ago=180,
        latency_ms=496,
        ingested=2,
    ),
    _source(
        "europe-pmc",
        "Europe PMC REST API",
        4,
        "peer-reviewed",
        "A",
        1,
        fetched_min_ago=205,
        latency_ms=388,
        ingested=3,
    ),
    _source(
        "crossref",
        "Crossref Works API",
        4,
        "peer-reviewed",
        "B",
        1,
        fetched_min_ago=420,
        latency_ms=234,
        ingested=2,
    ),
]


# Legacy variable block retained below for backward compatibility with any
# stale imports. The real source list is built above by _source().
_DEPRECATED_SOURCES: list[dict[str, Any]] = [
    # Tier 1 (gated)
    {
        "id": str(uuid.uuid4()),
        "code": "who-don",
        "name": "WHO Disease Outbreak News",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "cdc-han",
        "name": "CDC Health Alert Network",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "cdc-mmwr",
        "name": "CDC MMWR (Morbidity and Mortality Weekly Report)",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "ecdc-tessy",
        "name": "ECDC Surveillance Atlas (TESSy)",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "paho-alerts",
        "name": "PAHO Epidemiological Alerts",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "nmh-data",
        "name": "New Mexico Department of Health HPS",
        "tier": 1,
        "provenance_type": "official-authority",
        "nato_reliability": "A",
        "nato_credibility": 2,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    # Tier 2: ProMED ENABLED, simulating recent successful fetches
    {
        "id": str(uuid.uuid4()),
        "code": "promed-rss",
        "name": "ProMED-mail RSS",
        "tier": 2,
        "provenance_type": "aggregator",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "enabled": True,
        "last_fetched_at": utc_offset_iso(minutes_ago=8),
        "last_http_status": 200,
        "last_latency_ms": 487,
        "total_items_ingested": 5,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "healthmap",
        "name": "HealthMap (Boston Children Hospital)",
        "tier": 2,
        "provenance_type": "aggregator",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    # Tier 3
    {
        "id": str(uuid.uuid4()),
        "code": "gdelt",
        "name": "GDELT 2.0 Global Knowledge Graph",
        "tier": 3,
        "provenance_type": "aggregator",
        "nato_reliability": "C",
        "nato_credibility": 3,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    # Tier 4
    {
        "id": str(uuid.uuid4()),
        "code": "pubmed",
        "name": "PubMed E-utilities",
        "tier": 4,
        "provenance_type": "peer-reviewed",
        "nato_reliability": "A",
        "nato_credibility": 1,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
    {
        "id": str(uuid.uuid4()),
        "code": "biorxiv",
        "name": "bioRxiv preprint server",
        "tier": 4,
        "provenance_type": "peer-reviewed",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "enabled": False,
        "last_fetched_at": None,
        "last_http_status": None,
        "last_latency_ms": None,
        "total_items_ingested": 0,
    },
]


# Cases: realistic mock based on real 2026 hantavirus surveillance reports
CASES: list[dict[str, Any]] = [
    {
        "id": str(uuid.uuid4()),
        "source_code": "promed-rss",
        "source_name": "ProMED-mail RSS",
        "src_citation": (
            '[PUBLIC] promed-rss (B2) "Hantavirus, multi-country (cruise ship): '
            'MV Hondius cluster update" ProMED-mail RSS, 2026-05-10'
        ),
        "title": "Hantavirus, multi-country (cruise ship): MV Hondius cluster update",
        "summary": (
            "Eight confirmed and suspected cases of Andes virus aboard MV Hondius "
            "expedition cruise ship docked at Tenerife. Three deaths reported. "
            "Repatriation flights scheduled for nationals to Spain, Netherlands, UK, "
            "Canada, US, France, Ireland, Turkey, and Australia. Suspected exposure "
            "during Ushuaia, Argentina pre-departure shore excursion."
        ),
        "country_iso2": "AR",
        "region": "Tierra del Fuego (suspected exposure)",
        "serotype_code": "ANDV",
        "serotype_text": "ANDV",
        "reported_date": "2026-05-10",
        "ingested_at": utc_offset_iso(hours_ago=1, minutes_ago=12),
        "raw_url": "https://promedmail.org/post/2026-mv-hondius-update",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "pipeline_confidence": 0.88,
        "analyst_confidence": 0.95,
    },
    {
        "id": str(uuid.uuid4()),
        "source_code": "promed-rss",
        "source_name": "ProMED-mail RSS",
        "src_citation": (
            '[PUBLIC] promed-rss (B2) "Hantavirus, Argentina (Chubut): Andes virus, '
            '3 cases" ProMED-mail RSS, 2026-05-09'
        ),
        "title": "Hantavirus, Argentina (Chubut): Andes virus, 3 cases",
        "summary": (
            "Three laboratory-confirmed Andes virus cases reported by Argentine "
            "Ministry of Health in Chubut province. Two cases were rural forestry "
            "workers; one family contact raises person-to-person transmission "
            "concern. Malbrán Institute confirmed serology. Climate change and "
            "rodent population shifts cited as contributing factors."
        ),
        "country_iso2": "AR",
        "region": "Chubut",
        "serotype_code": "ANDV",
        "serotype_text": "ANDV",
        "reported_date": "2026-05-09",
        "ingested_at": utc_offset_iso(hours_ago=8),
        "raw_url": "https://promedmail.org/post/2026-chubut-cluster",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "pipeline_confidence": 0.82,
        "analyst_confidence": None,
    },
    {
        "id": str(uuid.uuid4()),
        "source_code": "promed-rss",
        "source_name": "ProMED-mail RSS",
        "src_citation": (
            '[PUBLIC] promed-rss (B2) "Hantavirus, USA (New Mexico): Sin Nombre virus, '
            'one fatal case" ProMED-mail RSS, 2026-05-06'
        ),
        "title": "Hantavirus, USA (New Mexico): Sin Nombre virus, one fatal case",
        "summary": (
            "New Mexico Department of Health confirmed first 2026 HPS fatality. "
            "Adult male, Santa Fe county, exposure suspected during cabin cleaning. "
            "Brings total NM cases since 1975 to 143, with 56 fatalities. "
            "CDC Four Corners endemic-zone reminder issued."
        ),
        "country_iso2": "US",
        "region": "New Mexico, Santa Fe county",
        "serotype_code": "SNV",
        "serotype_text": "SNV",
        "reported_date": "2026-05-06",
        "ingested_at": utc_offset_iso(hours_ago=24 * 2),
        "raw_url": "https://promedmail.org/post/2026-nm-snv",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "pipeline_confidence": 0.81,
        "analyst_confidence": 0.92,
    },
    {
        "id": str(uuid.uuid4()),
        "source_code": "promed-rss",
        "source_name": "ProMED-mail RSS",
        "src_citation": (
            '[PUBLIC] promed-rss (B2) "Hantavirus, Chile (Aysén): Andes virus, '
            'cluster of 4 cases" ProMED-mail RSS, 2026-05-04'
        ),
        "title": "Hantavirus, Chile (Aysén): Andes virus, cluster of 4 cases",
        "summary": (
            "Chile Ministry of Health reports a cluster of 4 Andes hantavirus cases "
            "in Aysén region. One fatality. All cases involved rural workers in "
            "forestry-adjacent areas. Epidemiological alert from November 2025 "
            "remains active. 2026 YTD Chilean cases now 43, surpassing 2025 total "
            "of 44 with eight months still to run."
        ),
        "country_iso2": "CL",
        "region": "Aysén",
        "serotype_code": "ANDV",
        "serotype_text": "ANDV",
        "reported_date": "2026-05-04",
        "ingested_at": utc_offset_iso(hours_ago=24 * 4),
        "raw_url": "https://promedmail.org/post/2026-cl-aysen",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "pipeline_confidence": 0.81,
        "analyst_confidence": None,
    },
    {
        "id": str(uuid.uuid4()),
        "source_code": "promed-rss",
        "source_name": "ProMED-mail RSS",
        "src_citation": (
            '[PUBLIC] promed-rss (B2) "Hantavirus, Finland (Uusimaa): Puumala virus, '
            'seasonal surveillance update" ProMED-mail RSS, 2026-04-12'
        ),
        "title": "Hantavirus, Finland (Uusimaa): Puumala virus, seasonal surveillance update",
        "summary": (
            "Finnish Institute for Health and Welfare (THL) reports 87 Puumala "
            "virus cases YTD across Uusimaa and surrounding regions. Nephropathia "
            "epidemica syndrome dominant clinical presentation. Vole population "
            "cycle in peak phase consistent with elevated seasonal transmission."
        ),
        "country_iso2": "FI",
        "region": "Uusimaa",
        "serotype_code": "PUUV",
        "serotype_text": "PUUV",
        "reported_date": "2026-04-12",
        "ingested_at": utc_offset_iso(hours_ago=24 * 28),
        "raw_url": "https://promedmail.org/post/2026-fi-puumala",
        "nato_reliability": "B",
        "nato_credibility": 2,
        "pipeline_confidence": 0.79,
        "analyst_confidence": None,
    },
]


# Clusters: derived from CASES (AR ANDV cruise + Chubut, CL ANDV Aysén).
# US SNV NM is a single-case cluster from the seeded SNV reference; FI PUUV is single case.
CLUSTERS: list[dict[str, Any]] = [
    {
        "id": str(uuid.uuid4()),
        "name": "AR ANDV cluster 2026-04-26",
        "country_iso2": "AR",
        "region": None,
        "serotype_code": "ANDV",
        "started_at": "2026-04-26",
        "ended_at": "2026-05-10",
        "status": "active",
        "case_count": 5,
        "death_count": 3,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "CL ANDV cluster 2026-04-29",
        "country_iso2": "CL",
        "region": "Aysén",
        "serotype_code": "ANDV",
        "started_at": "2026-04-29",
        "ended_at": "2026-05-04",
        "status": "active",
        "case_count": 4,
        "death_count": 1,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "US SNV cluster 2026-05-06",
        "country_iso2": "US",
        "region": "New Mexico",
        "serotype_code": "SNV",
        "started_at": "2026-05-06",
        "ended_at": "2026-05-06",
        "status": "active",
        "case_count": 1,
        "death_count": 1,
    },
]


# Hand-curated trace data for the MV Hondius cruise-ship cluster.
# Phase 3 will move this to a real schema (vessel_tracks, repatriation_routes,
# contacts). For now it powers the map-overlay visualisation.
TRACE_MV_HONDIUS: dict[str, Any] = {
    "cluster_id": "primary",
    "vessel_name": "MV Hondius",
    "patient_zero": {
        "label": "Ushuaia, Argentina",
        "lat": -54.80,
        "lng": -68.30,
        "date": "2026-04-01",
        "narrative": (
            "Dutch index couple exposure during pre-departure wildlife "
            "excursion in Tierra del Fuego national park."
        ),
    },
    "current_position": {
        "label": "Granadilla, Tenerife (docked)",
        "lat": 28.10,
        "lng": -16.50,
        "date": "2026-05-10",
        "stop_type": "dock",
    },
    "vessel_track": [
        {
            "label": "Ushuaia, AR",
            "lat": -54.80,
            "lng": -68.30,
            "date": "2026-04-01",
            "stop_type": "departure",
        },
        {
            "label": "South Georgia Island",
            "lat": -54.43,
            "lng": -36.59,
            "date": "2026-04-04",
            "stop_type": "shore",
        },
        {
            "label": "Tristan da Cunha",
            "lat": -37.10,
            "lng": -12.28,
            "date": "2026-04-13",
            "stop_type": "shore",
        },
        {
            "label": "Gough Island",
            "lat": -40.32,
            "lng": -9.93,
            "date": "2026-04-17",
            "stop_type": "shore",
        },
        {
            "label": "St Helena",
            "lat": -15.96,
            "lng": -5.71,
            "date": "2026-04-21",
            "stop_type": "shore",
        },
        {
            "label": "Ascension Island",
            "lat": -7.93,
            "lng": -14.41,
            "date": "2026-04-27",
            "stop_type": "medevac",
        },
        {
            "label": "Cape Verde (offshore)",
            "lat": 16.00,
            "lng": -24.00,
            "date": "2026-05-04",
            "stop_type": "detain",
        },
        {
            "label": "Granadilla, Tenerife",
            "lat": 28.10,
            "lng": -16.50,
            "date": "2026-05-10",
            "stop_type": "dock",
        },
    ],
    "repatriation_routes": [
        {
            "to_country": "ES",
            "to_label": "Madrid, Spain",
            "to_lat": 40.42,
            "to_lng": -3.70,
            "passenger_count": 14,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-08",
        },
        {
            "to_country": "FR",
            "to_label": "Paris (Le Bourget)",
            "to_lat": 48.97,
            "to_lng": 2.44,
            "passenger_count": 5,
            "case_count": 1,
            "fatalities": 0,
            "date": "2026-05-09",
        },
        {
            "to_country": "GB",
            "to_label": "Manchester, UK",
            "to_lat": 53.35,
            "to_lng": -2.28,
            "passenger_count": 22,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-10",
        },
        {
            "to_country": "NL",
            "to_label": "Amsterdam, Netherlands",
            "to_lat": 52.31,
            "to_lng": 4.77,
            "passenger_count": 26,
            "case_count": 2,
            "fatalities": 0,
            "date": "2026-05-10",
        },
        {
            "to_country": "CA",
            "to_label": "British Columbia, Canada",
            "to_lat": 49.28,
            "to_lng": -123.12,
            "passenger_count": 4,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-11",
        },
        {
            "to_country": "US",
            "to_label": "Nebraska via Washington",
            "to_lat": 41.49,
            "to_lng": -99.90,
            "passenger_count": 18,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-11",
        },
        {
            "to_country": "IE",
            "to_label": "Ireland (IRL290)",
            "to_lat": 53.40,
            "to_lng": -8.20,
            "passenger_count": 2,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-11",
        },
        {
            "to_country": "TR",
            "to_label": "Turkey",
            "to_lat": 39.93,
            "to_lng": 32.86,
            "passenger_count": 3,
            "case_count": 0,
            "fatalities": 0,
            "date": "2026-05-11",
        },
        {
            "to_country": "AU",
            "to_label": "Australia (pending)",
            "to_lat": -25.27,
            "to_lng": 133.78,
            "passenger_count": 0,
            "case_count": 0,
            "fatalities": 0,
            "date": None,
        },
    ],
}


# Hand-curated event chronology. Mock-only; the real API derives a subset
# from case_reports + clusters. Phase 3 may add an `events` table for
# milestones / statements / medevacs.
EVENTS: list[dict[str, Any]] = [
    {
        "id": "ev-2026-05-10-hondius-tenerife",
        "occurred_at": "2026-05-10",
        "event_type": "milestone",
        "severity": "alert",
        "title": "MV Hondius docks at Tenerife. Repatriation flights begin.",
        "summary": (
            "Eight confirmed and suspected ANDV cases. Three deaths. "
            "Nationals returned to Spain, Netherlands, UK, Canada, US, "
            "France, Ireland, Turkey, Australia."
        ),
        "country_iso2": "ES",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": "https://promedmail.org/post/2026-mv-hondius-update",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-09-chubut",
        "occurred_at": "2026-05-09",
        "event_type": "case",
        "severity": "notice",
        "title": "Argentina (Chubut): three Andes virus cases confirmed",
        "summary": (
            "Rural forestry workers and one family contact. "
            "Malbrán Institute serology confirmed. Person-to-person "
            "transmission under investigation."
        ),
        "country_iso2": "AR",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": "https://promedmail.org/post/2026-chubut-cluster",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-08-spain",
        "occurred_at": "2026-05-08",
        "event_type": "medevac",
        "severity": "info",
        "title": "Spain repatriates 14 nationals from Tenerife to Madrid",
        "summary": (
            "Airbus A310 'Reino de España' transports passengers to "
            "Gómez Ulla Defense Hospital. 21-day quarantine."
        ),
        "country_iso2": "ES",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": None,
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-07-who-statement",
        "occurred_at": "2026-05-07",
        "event_type": "statement",
        "severity": "alert",
        "title": "WHO response statement on cruise-ship hantavirus cluster",
        "summary": (
            "Dr. Tedros assesses public risk as low. Dr. Van Kerkhove: "
            "'This is not the start of a COVID pandemic.'"
        ),
        "country_iso2": None,
        "serotype_code": "ANDV",
        "source_code": "who-don",
        "source_url": "https://www.who.int/news/item/07-05-2026",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-06-nm-fatality",
        "occurred_at": "2026-05-06",
        "event_type": "fatality",
        "severity": "critical",
        "title": "USA (New Mexico): fatal Sin Nombre virus case",
        "summary": (
            "Adult male, Santa Fe county. Suspected exposure during cabin "
            "cleaning. 143rd NM case since 1975; 56th fatality."
        ),
        "country_iso2": "US",
        "serotype_code": "SNV",
        "source_code": "promed-rss",
        "source_url": "https://promedmail.org/post/2026-nm-snv",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-04-aysen",
        "occurred_at": "2026-05-04",
        "event_type": "cluster_new",
        "severity": "alert",
        "title": "Chile (Aysén): cluster of four ANDV cases identified",
        "summary": (
            "One fatality. Rural and forestry-adjacent exposure. "
            "2026 YTD Chilean total now 43, surpassing all of 2025."
        ),
        "country_iso2": "CL",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": "https://promedmail.org/post/2026-cl-aysen",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-05-02-don599",
        "occurred_at": "2026-05-02",
        "event_type": "statement",
        "severity": "alert",
        "title": "WHO DON599: Hantavirus cluster linked to cruise-ship travel",
        "summary": (
            "Seven cases (two laboratory-confirmed, five suspected) reported. "
            "Three deaths. Multi-country contact tracing initiated."
        ),
        "country_iso2": None,
        "serotype_code": "ANDV",
        "source_code": "who-don",
        "source_url": "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON599",
        "cluster_id": None,
    },
    {
        "id": "ev-2026-04-27-ascension",
        "occurred_at": "2026-04-27",
        "event_type": "medevac",
        "severity": "notice",
        "title": "Ascension Island: two symptomatic passengers airlifted",
        "summary": (
            "RAF facility serves as medevac point. Both transferred to "
            "Netherlands aboard chartered Airbus A220."
        ),
        "country_iso2": "NL",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": None,
        "cluster_id": None,
    },
    {
        "id": "ev-2026-04-26-first-death",
        "occurred_at": "2026-04-26",
        "event_type": "fatality",
        "severity": "critical",
        "title": "First fatality aboard MV Hondius: Dutch female",
        "summary": (
            "Second death in the cruise-ship cluster. Spouse (Dutch male) "
            "died 11 April. Index case during Ushuaia shore excursion."
        ),
        "country_iso2": "AR",
        "serotype_code": "ANDV",
        "source_code": "promed-rss",
        "source_url": None,
        "cluster_id": None,
    },
    {
        "id": "ev-2026-04-12-puumala-fi",
        "occurred_at": "2026-04-12",
        "event_type": "milestone",
        "severity": "info",
        "title": "Finland (Uusimaa): 87 Puumala virus cases YTD",
        "summary": (
            "THL reports vole population cycle in peak phase. "
            "Nephropathia epidemica dominant presentation."
        ),
        "country_iso2": "FI",
        "serotype_code": "PUUV",
        "source_code": "promed-rss",
        "source_url": "https://promedmail.org/post/2026-fi-puumala",
        "cluster_id": None,
    },
]


def _compute_stats() -> dict[str, Any]:
    """Derive aggregate stats from CASES + SOURCES + CLUSTERS fixtures."""
    now = datetime.now(tz=UTC)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)
    cutoff_14d = now - timedelta(days=14)

    cases_24h = 0
    cases_7d = 0
    cases_14d = 0
    for case in CASES:
        ingested = datetime.fromisoformat(case["ingested_at"])
        if ingested >= cutoff_24h:
            cases_24h += 1
        if ingested >= cutoff_7d:
            cases_7d += 1
        if ingested >= cutoff_14d:
            cases_14d += 1

    by_serotype_counts: dict[str, int] = {}
    by_country_counts: dict[str, int] = {}
    for case in CASES:
        sero = case.get("serotype_code") or case.get("serotype_text") or "unknown"
        by_serotype_counts[sero] = by_serotype_counts.get(sero, 0) + 1
        country = case.get("country_iso2")
        if country:
            by_country_counts[country] = by_country_counts.get(country, 0) + 1

    def top10(d: dict[str, int]) -> list[dict[str, int | str]]:
        return [{"label": k, "count": v} for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:10]]

    return {
        "total_cases": len(CASES),
        "total_countries": len({c["country_iso2"] for c in CASES if c.get("country_iso2")}),
        "total_clusters_active": sum(1 for c in CLUSTERS if c.get("status") == "active"),
        "total_serotypes_seen": len({c["serotype_code"] for c in CASES if c.get("serotype_code")}),
        "total_sources_enabled": sum(1 for s in SOURCES if s.get("enabled")),
        "cases_last_24h": cases_24h,
        "cases_last_7d": cases_7d,
        "cases_last_14d": cases_14d,
        "by_serotype": top10(by_serotype_counts),
        "by_country": top10(by_country_counts),
    }


class MockAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "accept, content-type")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self) -> None:
        self.send_response(404)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802 - http.server convention
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "accept, content-type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - http.server convention
        path = self.path.split("?", 1)[0]
        if path == "/health":
            return self._send_json({"status": "ok", "version": "0.1.0-mock"})
        if path == "/api/v1/cases":
            return self._send_json(
                {
                    "items": CASES,
                    "total": len(CASES),
                    "limit": 50,
                    "offset": 0,
                }
            )
        if path == "/api/v1/sources":
            return self._send_json({"items": SOURCES})
        if path == "/api/v1/clusters":
            return self._send_json({"items": CLUSTERS, "total": len(CLUSTERS)})
        # Trace endpoints MUST be checked before the generic /clusters/{id} fallback,
        # otherwise that fallback treats "primary/trace" as a cluster ID.
        if path == "/api/v1/clusters/primary/trace" or (
            path.startswith("/api/v1/clusters/") and path.endswith("/trace")
        ):
            return self._send_json(TRACE_MV_HONDIUS)
        if path.startswith("/api/v1/clusters/"):
            cluster_id = path.removeprefix("/api/v1/clusters/").rstrip("/")
            cluster = next((c for c in CLUSTERS if c["id"] == cluster_id), None)
            if cluster is None:
                return self._send_404()
            # Mock member-case lookup: match by country + serotype.
            members = [
                c
                for c in CASES
                if c["country_iso2"] == cluster["country_iso2"]
                and c.get("serotype_code") == cluster["serotype_code"]
            ]
            return self._send_json({**cluster, "cases": members})
        if path == "/api/v1/meta/stats":
            return self._send_json(_compute_stats())
        if path == "/api/v1/meta/events":
            return self._send_json({"items": EVENTS, "total": len(EVENTS)})
        if path == "/api/v1/stream/events":
            return self._stream_events()
        return self._send_404()

    def _stream_events(self) -> None:
        """SSE stream: emits a tick every TICK_SECONDS until client disconnects."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                payload = json.dumps(
                    {
                        "type": "tick",
                        "ts": datetime.now(tz=UTC).isoformat(timespec="seconds"),
                    }
                )
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
                time.sleep(TICK_SECONDS)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        print(f"  [mock] {self.command} {self.path} -> {args[1] if len(args) > 1 else '?'}")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), MockAPIHandler)
    print(f"==> HORIZON mock API running on http://localhost:{PORT}")
    print("    Endpoints: /health, /api/v1/cases, /api/v1/sources")
    print(f"    Sample data: {len(CASES)} cases, {len(SOURCES)} sources (1 enabled)")
    print("    Refresh http://localhost:5173 in your browser to see populated UI.")
    print("    Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n==> mock API stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
