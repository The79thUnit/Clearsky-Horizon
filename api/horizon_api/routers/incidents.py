"""GET /api/v1/incidents - real outbreak events (not articles).

An incident is one outbreak (e.g. the MV Hondius cluster). It owns:
  - authoritative case counts from named sources (WHO DON, CDC HAN, PAHO)
  - per-country breakdown
  - vessel + port + excursion context
  - corroborating articles ingested from any source

This is what the public actually wants to see. Articles are evidence; incidents
are the thing.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..db import acquire
from ..schemas import (
    EntityRecord,
    IncidentAuthoritativeCount,
    IncidentCountryRow,
    IncidentDetail,
    IncidentList,
    IncidentOntology,
    IncidentRecord,
    RelationshipRecord,
    VesselTrackPoint,
)

router = APIRouter(tags=["incidents"])


_QUERY_LIST_BODY = """
WITH latest_counts AS (
    SELECT DISTINCT ON (iac.incident_id)
        iac.incident_id,
        iac.confirmed_cases,
        iac.suspected_cases,
        iac.deaths,
        iac.recovered,
        iac.reported_at,
        s.code AS source_code
    FROM incident_authoritative_counts iac
    JOIN sources s ON s.id = iac.source_id
    ORDER BY
        iac.incident_id,
        iac.nato_reliability ASC,
        iac.nato_credibility ASC,
        iac.reported_at DESC
)
SELECT
    i.id, i.code, i.name,
    sero.code AS serotype_code,
    i.started_at, i.ended_at, i.status, i.summary,
    i.primary_location_country_iso2,
    i.primary_location_name,
    i.primary_vessel_imo,
    i.primary_vessel_name,
    i.primary_vessel_mmsi,
    i.primary_vessel_flag,
    COALESCE(lc.confirmed_cases, 0) AS confirmed_cases,
    COALESCE(lc.suspected_cases, 0) AS suspected_cases,
    COALESCE(lc.deaths, 0)          AS deaths,
    COALESCE(lc.recovered, 0)       AS recovered,
    lc.source_code                  AS authority_source_code,
    lc.reported_at                  AS authority_reported_at,
    (
        SELECT COUNT(DISTINCT source_id)::int
        FROM incident_authoritative_counts
        WHERE incident_id = i.id
    ) AS corroborating_sources
FROM incidents i
LEFT JOIN serotypes sero ON sero.id = i.serotype_id
LEFT JOIN latest_counts lc ON lc.incident_id = i.id
"""

_QUERY_LIST = (
    _QUERY_LIST_BODY
    + """
ORDER BY
    CASE i.status WHEN 'active' THEN 0 WHEN 'monitoring' THEN 1 ELSE 2 END,
    i.started_at DESC NULLS LAST
"""
)

_QUERY_GET_BY_ID = _QUERY_LIST_BODY + "WHERE i.id = $1\n"
_QUERY_GET_BY_CODE = _QUERY_LIST_BODY + "WHERE i.code = $1\n"


_QUERY_COUNTRIES = """
SELECT country_iso2, confirmed_count, suspected_count, deaths, first_reported_at
FROM incident_countries
WHERE incident_id = $1
ORDER BY confirmed_count DESC, suspected_count DESC, country_iso2
"""


_QUERY_HISTORY = """
SELECT
    iac.confirmed_cases, iac.suspected_cases, iac.deaths, iac.recovered,
    s.code AS source_code, s.name AS source_name,
    iac.reported_at,
    iac.nato_reliability, iac.nato_credibility,
    iac.src_citation, iac.notes
FROM incident_authoritative_counts iac
JOIN sources s ON s.id = iac.source_id
WHERE iac.incident_id = $1
ORDER BY iac.reported_at DESC, iac.nato_reliability ASC, iac.nato_credibility ASC
"""


@router.get(
    "/api/v1/incidents",
    response_model=IncidentList,
    summary="List active outbreak incidents with their authoritative case counts",
)
async def list_incidents() -> IncidentList:
    async with acquire() as conn:
        rows = await conn.fetch(_QUERY_LIST)
        items: list[IncidentRecord] = []
        for r in rows:
            country_rows = await conn.fetch(_QUERY_COUNTRIES, r["id"])
            countries = [IncidentCountryRow.model_validate(dict(c)) for c in country_rows]
            items.append(IncidentRecord.model_validate({**dict(r), "countries": countries}))
    return IncidentList(items=items, total=len(items))


@router.get(
    "/api/v1/incidents/{incident_id_or_code}",
    response_model=IncidentDetail,
    summary="Incident detail with authoritative-count history",
)
async def get_incident(incident_id_or_code: str) -> IncidentDetail:
    async with acquire() as conn:
        try:
            uuid_arg: UUID | None = UUID(incident_id_or_code)
        except ValueError:
            uuid_arg = None

        if uuid_arg is not None:
            r = await conn.fetchrow(_QUERY_GET_BY_ID, uuid_arg)
        else:
            r = await conn.fetchrow(_QUERY_GET_BY_CODE, incident_id_or_code)

        if r is None:
            raise HTTPException(
                status_code=404, detail=f"incident {incident_id_or_code!r} not found"
            )

        country_rows = await conn.fetch(_QUERY_COUNTRIES, r["id"])
        countries = [IncidentCountryRow.model_validate(dict(c)) for c in country_rows]

        history_rows = await conn.fetch(_QUERY_HISTORY, r["id"])
        history = [IncidentAuthoritativeCount.model_validate(dict(h)) for h in history_rows]

    return IncidentDetail.model_validate(
        {
            **dict(r),
            "countries": countries,
            "counts_history": history,
        }
    )


_QUERY_ENTITIES = """
SELECT id, entity_type, public_label, properties
FROM entities
WHERE incident_id = $1
ORDER BY entity_type, public_label
"""

_QUERY_RELATIONSHIPS = """
SELECT r.id, r.src_id, r.dst_id, r.rel_type, r.properties, r.confidence, r.src_citation
FROM relationships r
JOIN entities src ON src.id = r.src_id
JOIN entities dst ON dst.id = r.dst_id
WHERE src.incident_id = $1 OR dst.incident_id = $1
ORDER BY r.rel_type
"""

_QUERY_TRACK = """
SELECT vtp.ts, vtp.lat::float8 AS lat, vtp.lng::float8 AS lng,
       vtp.speed_knots::float8 AS speed_knots, vtp.heading::float8 AS heading,
       vtp.source
FROM vessel_track_points vtp
JOIN entities e ON e.id = vtp.vessel_entity_id
WHERE e.incident_id = $1 AND e.entity_type = 'vessel'
ORDER BY vtp.ts ASC
"""


@router.get(
    "/api/v1/incidents/{incident_code}/ontology",
    response_model=IncidentOntology,
    summary="Full ontology graph (entities + relationships) for one incident",
)
async def get_incident_ontology(incident_code: str) -> IncidentOntology:
    async with acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, code FROM incidents WHERE code = $1 OR id::text = $1",
            incident_code,
        )
        if row is None:
            raise HTTPException(
                status_code=404, detail=f"incident {incident_code!r} not found"
            )
        incident_id = row["id"]
        entity_rows = await conn.fetch(_QUERY_ENTITIES, incident_id)
        rel_rows = await conn.fetch(_QUERY_RELATIONSHIPS, incident_id)
        track_rows = await conn.fetch(_QUERY_TRACK, incident_id)

    entities = [EntityRecord.model_validate(dict(r)) for r in entity_rows]
    relationships = [RelationshipRecord.model_validate(dict(r)) for r in rel_rows]
    track = [VesselTrackPoint.model_validate(dict(r)) for r in track_rows]

    return IncidentOntology(
        incident_code=row["code"],
        entities=entities,
        relationships=relationships,
        vessel_track=track,
    )
