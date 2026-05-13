"""GET /api/v1/clusters - list of auto-detected outbreak clusters with case counts.

GET /api/v1/clusters/{id} - cluster detail with member case_reports.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ..db import acquire
from ..schemas import CaseRecord, ClusterDetail, ClusterList, ClusterRecord

router = APIRouter()

_QUERY_LIST = """
SELECT
    c.id,
    c.name,
    c.country_iso2,
    c.region,
    s.code               AS serotype_code,
    c.started_at,
    c.ended_at,
    c.status,
    c.case_count,
    c.death_count
FROM clusters c
LEFT JOIN serotypes s ON s.id = c.serotype_id
ORDER BY c.ended_at DESC NULLS LAST, c.started_at DESC
LIMIT $1
"""

_QUERY_COUNT = "SELECT COUNT(*)::int AS c FROM clusters"


_QUERY_DETAIL = """
SELECT
    c.id, c.name, c.country_iso2, c.region,
    s.code AS serotype_code,
    c.started_at, c.ended_at, c.status, c.case_count, c.death_count
FROM clusters c
LEFT JOIN serotypes s ON s.id = c.serotype_id
WHERE c.id = $1
"""

_QUERY_MEMBER_CASES = """
SELECT
    cr.id,
    src.code                                AS source_code,
    src.name                                AS source_name,
    cr.src_citation,
    cr.title,
    cr.summary,
    cr.country_iso2,
    cr.region,
    sero.code                               AS serotype_code,
    cr.serotype_text,
    cr.reported_date,
    cr.ingested_at,
    cr.raw_url,
    qs.nato_reliability,
    qs.nato_credibility,
    qs.pipeline_confidence::double precision  AS pipeline_confidence,
    qs.analyst_confidence::double precision   AS analyst_confidence
FROM case_to_cluster ctc
JOIN case_reports cr             ON cr.id = ctc.case_report_id
JOIN sources src                 ON src.id = cr.source_id
JOIN qualification_scores qs     ON qs.case_report_id = cr.id
LEFT JOIN serotypes sero         ON sero.id = cr.serotype_id
WHERE ctc.cluster_id = $1
ORDER BY cr.reported_date DESC NULLS LAST, cr.ingested_at DESC
"""


@router.get("", response_model=ClusterList, summary="List outbreak clusters")
async def list_clusters(
    limit: int = Query(100, ge=1, le=500, description="Max clusters to return"),
) -> ClusterList:
    async with acquire() as conn:
        total_row = await conn.fetchrow(_QUERY_COUNT)
        rows = await conn.fetch(_QUERY_LIST, limit)
    items = [ClusterRecord.model_validate(dict(r)) for r in rows]
    return ClusterList(
        items=items,
        total=int(total_row["c"]) if total_row else 0,
    )


@router.get(
    "/{cluster_id}",
    response_model=ClusterDetail,
    summary="Cluster detail with member cases",
)
async def get_cluster(cluster_id: UUID) -> ClusterDetail:
    async with acquire() as conn:
        row = await conn.fetchrow(_QUERY_DETAIL, cluster_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"cluster {cluster_id} not found")
        case_rows = await conn.fetch(_QUERY_MEMBER_CASES, cluster_id)

    data = dict(row)
    data["cases"] = [CaseRecord.model_validate(dict(r)) for r in case_rows]
    return ClusterDetail.model_validate(data)
