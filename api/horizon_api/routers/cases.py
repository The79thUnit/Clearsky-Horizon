"""GET /api/v1/cases - paginated case report listing with qualification scores."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..db import acquire
from ..schemas import CaseList, CaseRecord

router = APIRouter()

_QUERY_LIST = """
SELECT
    cr.id,
    s.code                              AS source_code,
    s.name                              AS source_name,
    cr.src_citation,
    cr.title,
    cr.summary,
    cr.country_iso2,
    cr.region,
    st.code                             AS serotype_code,
    cr.serotype_text,
    cr.reported_date,
    cr.ingested_at,
    cr.raw_url,
    qs.nato_reliability,
    qs.nato_credibility,
    qs.pipeline_confidence::double precision  AS pipeline_confidence,
    qs.analyst_confidence::double precision   AS analyst_confidence
FROM case_reports cr
JOIN sources s             ON s.id = cr.source_id
JOIN qualification_scores qs ON qs.case_report_id = cr.id
LEFT JOIN serotypes st     ON st.id = cr.serotype_id
ORDER BY cr.ingested_at DESC
LIMIT $1 OFFSET $2
"""

_QUERY_COUNT = "SELECT COUNT(*)::int AS c FROM case_reports"


@router.get("", response_model=CaseList, summary="List case reports")
async def list_cases(
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> CaseList:
    async with acquire() as conn:
        total_row = await conn.fetchrow(_QUERY_COUNT)
        rows = await conn.fetch(_QUERY_LIST, limit, offset)
    items = [CaseRecord.model_validate(dict(r)) for r in rows]
    return CaseList(
        items=items,
        total=int(total_row["c"]) if total_row else 0,
        limit=limit,
        offset=offset,
    )
