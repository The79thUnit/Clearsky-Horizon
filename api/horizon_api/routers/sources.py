"""GET /api/v1/sources - source registry with latest quality stats."""

from __future__ import annotations

from fastapi import APIRouter

from ..db import acquire
from ..schemas import SourceList, SourceRecord

router = APIRouter()

_QUERY_SOURCES = """
SELECT
    s.id,
    s.code,
    s.name,
    s.tier,
    s.provenance_type,
    s.nato_reliability,
    s.nato_credibility,
    s.enabled,
    sql_latest.fetched_at                                AS last_fetched_at,
    sql_latest.http_status                               AS last_http_status,
    sql_latest.latency_ms                                AS last_latency_ms,
    COALESCE(sql_totals.total_ingested, 0)::int          AS total_items_ingested
FROM sources s
LEFT JOIN LATERAL (
    SELECT fetched_at, http_status, latency_ms
    FROM source_quality_log
    WHERE source_id = s.id
    ORDER BY fetched_at DESC
    LIMIT 1
) sql_latest ON TRUE
LEFT JOIN LATERAL (
    SELECT SUM(items_ingested) AS total_ingested
    FROM source_quality_log
    WHERE source_id = s.id
) sql_totals ON TRUE
ORDER BY s.tier, s.code
"""


@router.get("", response_model=SourceList, summary="List configured sources")
async def list_sources() -> SourceList:
    async with acquire() as conn:
        rows = await conn.fetch(_QUERY_SOURCES)
    return SourceList(items=[SourceRecord.model_validate(dict(r)) for r in rows])
