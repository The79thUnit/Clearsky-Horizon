"""Pydantic response schemas for the API."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    version: str


class CaseRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_code: str
    source_name: str
    src_citation: str
    title: str
    summary: str | None = None
    country_iso2: str | None = None
    region: str | None = None
    serotype_code: str | None = None
    serotype_text: str | None = None
    reported_date: date | None = None
    ingested_at: datetime
    raw_url: str
    nato_reliability: str
    nato_credibility: int
    pipeline_confidence: float
    pipeline_factors: dict = {}  # type: ignore[assignment]
    analyst_confidence: float | None = None
    analyst_id: str | None = None  # 'HORIZON-AUTO-SCORER/1.0' = machine pre-fill; human ID = reviewed
    # Epidemiological classification (Pass 2 -- migration 054)
    case_classification: str = "unknown"
    lab_method: str = "unknown"
    ihr_notified: bool = False
    travel_history: bool | None = None
    gadm_gid: str | None = None
    ecological_flags: dict = {}  # type: ignore[assignment]


class CaseList(BaseModel):
    items: list[CaseRecord]
    total: int
    limit: int
    offset: int
    # Cursor for the next page (cursor-based pagination, preferred over offset).
    # Pass as ?cursor=<value> to retrieve the next page.
    # None when the result set is exhausted.
    next_cursor: str | None = None


class SourceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    tier: int
    provenance_type: str
    nato_reliability: str
    nato_credibility: int
    enabled: bool
    last_fetched_at: datetime | None = None
    last_http_status: int | None = None
    last_latency_ms: int | None = None
    total_items_ingested: int = 0


class SourceList(BaseModel):
    items: list[SourceRecord]


class ClusterRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country_iso2: str | None = None
    region: str | None = None
    serotype_code: str | None = None
    started_at: date | None = None
    ended_at: date | None = None
    status: str
    case_count: int
    death_count: int


class ClusterList(BaseModel):
    items: list[ClusterRecord]
    total: int


class ClusterDetail(ClusterRecord):
    """Full cluster view: cluster fields + linked case_reports."""

    cases: list[CaseRecord] = []


class BreakdownEntry(BaseModel):
    """One row of a top-N breakdown (e.g. cases by serotype)."""

    label: str
    count: int


class StatsResponse(BaseModel):
    """Global counters for the home-screen hero strip.

    NOTE: `total_reports_ingested` is the count of source articles HORIZON has
    consumed. It is NOT a count of real people. The authoritative case number
    for the public is `total_confirmed_cases_authoritative`, summed from
    `incident_authoritative_counts` (most-recent highest-NATO entry per incident).
    """

    # Authoritative real-world counters (from `incident_authoritative_counts`)
    total_confirmed_cases_authoritative: int
    total_suspected_cases_authoritative: int
    total_deaths_authoritative: int
    total_active_incidents: int
    # Ingestion telemetry (what the pipeline has consumed; informational)
    total_reports_ingested: int
    total_countries_in_reports: int
    total_clusters_active: int
    total_serotypes_seen: int
    total_sources_enabled: int
    reports_last_24h: int
    reports_last_7d: int
    reports_last_14d: int
    by_serotype: list[BreakdownEntry]
    by_country: list[BreakdownEntry]


class EventRecord(BaseModel):
    """One entry in the chronological events feed."""

    id: str  # UUID or stable derived key
    occurred_at: date | datetime
    event_type: str  # 'case', 'fatality', 'cluster_new', 'cluster_update',
    # 'statement', 'medevac', 'milestone'
    severity: str  # 'info', 'notice', 'alert', 'critical'
    title: str
    summary: str | None = None
    country_iso2: str | None = None
    serotype_code: str | None = None
    source_code: str | None = None
    source_url: str | None = None
    cluster_id: str | None = None


class EventList(BaseModel):
    items: list[EventRecord]
    total: int


# ---------------------------------------------------------------------------
# Incident model (real outbreak events, distinct from case_reports/articles).
# ---------------------------------------------------------------------------


class IncidentCountryRow(BaseModel):
    country_iso2: str
    confirmed_count: int
    suspected_count: int
    deaths: int
    first_reported_at: date | None = None


class IncidentAuthoritativeCount(BaseModel):
    """One snapshot of an authoritative case count from a named source."""

    confirmed_cases: int
    suspected_cases: int
    deaths: int
    recovered: int
    source_code: str
    source_name: str
    reported_at: datetime
    nato_reliability: str
    nato_credibility: int
    src_citation: str
    notes: str | None = None


class IncidentRecord(BaseModel):
    """Top-level outbreak event entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    serotype_code: str | None = None
    started_at: date | None = None
    ended_at: date | None = None
    status: str
    summary: str | None = None
    primary_location_country_iso2: str | None = None
    primary_location_name: str | None = None
    primary_vessel_imo: str | None = None
    primary_vessel_name: str | None = None
    primary_vessel_mmsi: str | None = None
    primary_vessel_flag: str | None = None
    # Derived from latest authoritative count (highest-NATO, most-recent)
    confirmed_cases: int = 0
    suspected_cases: int = 0
    deaths: int = 0
    recovered: int = 0
    authority_source_code: str | None = None
    authority_reported_at: datetime | None = None
    # How many distinct sources have corroborated this incident
    corroborating_sources: int = 0
    countries: list[IncidentCountryRow] = []


class IncidentList(BaseModel):
    items: list[IncidentRecord]
    total: int


class IncidentDetail(IncidentRecord):
    counts_history: list[IncidentAuthoritativeCount] = []


class EntityRecord(BaseModel):
    """One node in the incident ontology graph."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    public_label: str | None = None
    properties: dict  # type: ignore[type-arg]


class RelationshipRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    src_id: UUID
    dst_id: UUID
    rel_type: str
    properties: dict  # type: ignore[type-arg]
    confidence: float
    src_citation: str


class VesselTrackPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    lat: float
    lng: float
    speed_knots: float | None = None
    heading: float | None = None
    source: str


class IncidentOntology(BaseModel):
    """The full ontology graph for an incident: nodes + edges + vessel track."""

    incident_code: str
    entities: list[EntityRecord]
    relationships: list[RelationshipRecord]
    vessel_track: list[VesselTrackPoint] = []
