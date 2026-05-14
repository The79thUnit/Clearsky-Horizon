"""GET /api/v1/cases - paginated case report listing with qualification scores.

Pagination modes:
  - Cursor (preferred): ?cursor=<opaque token> -- keyset pagination, stable
    under continuous ingest. Recommended for all new consumers.
  - Offset (deprecated): ?offset=N -- non-deterministic with live data,
    kept for backwards compatibility. Returns Deprecation: true header.

The cursor is an opaque base64-encoded JSON token containing
{ingested_at: ISO8601, id: UUID}. Consumers must treat it as opaque.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from ..db import acquire
from ..schemas import CaseList, CaseRecord

router = APIRouter()

_SELECT_COLS = """
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
    COALESCE(qs.pipeline_factors, '{}'::jsonb) AS pipeline_factors,
    qs.analyst_confidence::double precision   AS analyst_confidence,
    qs.analyst_id                             AS analyst_id
    -- case_classification, lab_method, ihr_notified, travel_history,
    -- gadm_gid, ecological_flags are migration-053 columns not yet applied
    -- on production. Schema fields carry defaults; columns added when
    -- migration 054 runs. Remove this comment block when migrated.
FROM case_reports cr
JOIN sources s             ON s.id = cr.source_id
JOIN qualification_scores qs ON qs.case_report_id = cr.id
LEFT JOIN serotypes st     ON st.id = cr.serotype_id
"""

# Reddit quality gate: Reddit records (NATO E/4, disabled 2026-05-14 per
# migration 059) are hidden from the public JSON API unless a human analyst
# has explicitly set analyst_confidence. They remain accessible via the
# bulk NDJSON export (/api/v1/cases/bulk/ndjson) for research transparency.
# The filter is: show the record if the source is NOT reddit, OR if
# analyst_confidence is explicitly set (human-reviewed and approved).
_REDDIT_GATE = (
    "  AND (s.code != 'reddit' OR qs.analyst_confidence IS NOT NULL)\n"
)

# Cursor-based (keyset) pagination -- stable under continuous ingest.
_QUERY_CURSOR = (
    "SELECT " + _SELECT_COLS
    + "WHERE (cr.ingested_at, cr.id) < ($2::timestamptz, $3::uuid)\n"
    + _REDDIT_GATE
    + "ORDER BY cr.ingested_at DESC, cr.id DESC\n"
    + "LIMIT $1\n"
)

# First page (no cursor) -- just order and limit.
_QUERY_FIRST = (
    "SELECT " + _SELECT_COLS
    + "WHERE TRUE\n"
    + _REDDIT_GATE
    + "ORDER BY cr.ingested_at DESC, cr.id DESC\n"
    + "LIMIT $1\n"
)

# Offset-based (legacy) -- non-deterministic with live data.
_QUERY_OFFSET = (
    "SELECT " + _SELECT_COLS
    + "WHERE TRUE\n"
    + _REDDIT_GATE
    + "ORDER BY cr.ingested_at DESC\n"
    + "LIMIT $1 OFFSET $2\n"
)

_QUERY_COUNT = (
    "SELECT COUNT(*)::int AS c\n"
    "FROM case_reports cr\n"
    "JOIN sources s ON s.id = cr.source_id\n"
    "LEFT JOIN qualification_scores qs ON qs.case_report_id = cr.id\n"
    "WHERE (s.code != 'reddit' OR qs.analyst_confidence IS NOT NULL)\n"
)

# NDJSON bulk export (all columns, no filtering).
_QUERY_BULK = (
    "SELECT " + _SELECT_COLS
    + "ORDER BY cr.ingested_at ASC"
)


def _make_cursor(ingested_at: datetime, row_id: UUID) -> str:
    """Encode (ingested_at, id) as an opaque cursor token."""
    payload = json.dumps(
        {"t": ingested_at.isoformat(), "i": str(row_id)},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _parse_cursor(token: str) -> tuple[str, str] | None:
    """Decode cursor token. Returns (ingested_at_iso, id_str) or None on error."""
    try:
        data = json.loads(base64.urlsafe_b64decode(token + "=="))
        return str(data["t"]), str(data["i"])
    except Exception:
        return None


@router.get("", response_model=CaseList, summary="List case reports")
async def list_cases(
    response: Response,
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    cursor: str | None = Query(
        None,
        description=(
            "Opaque cursor token from a previous response next_cursor field. "
            "When present, returns the next page after the cursor position. "
            "Preferred over offset for stable pagination under live ingest."
        ),
    ),
    offset: int | None = Query(
        None,
        ge=0,
        description=(
            "DEPRECATED. Pagination offset. Non-deterministic under live ingest. "
            "Use cursor instead. Will be removed in v2."
        ),
    ),
) -> CaseList:
    async with acquire() as conn:
        total_row = await conn.fetchrow(_QUERY_COUNT)
        total = int(total_row["c"]) if total_row else 0

        if cursor is not None:
            # Cursor-based pagination
            parsed = _parse_cursor(cursor)
            if parsed is None:
                # Invalid cursor -- fall back to first page
                rows = await conn.fetch(_QUERY_FIRST, limit)
            else:
                ts_str, id_str = parsed
                rows = await conn.fetch(_QUERY_CURSOR, limit, ts_str, id_str)
        elif offset is not None:
            # Offset pagination (deprecated)
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = (
                '</api/v1/cases>; rel="successor-version", '
                '<https://hantavirus.software/api/docs>; rel="deprecation"'
            )
            rows = await conn.fetch(_QUERY_OFFSET, limit, offset)
        else:
            # First page, no cursor
            rows = await conn.fetch(_QUERY_FIRST, limit)

    items = [CaseRecord.model_validate(dict(r)) for r in rows]

    next_cursor: str | None = None
    if items:
        last = items[-1]
        next_cursor = _make_cursor(last.ingested_at, last.id)

    return CaseList(
        items=items,
        total=total,
        limit=limit,
        offset=offset or 0,
        next_cursor=next_cursor,
    )


async def _ndjson_stream() -> bytes:
    """Stream all case_reports as NDJSON. Generator for StreamingResponse."""
    async with acquire() as conn:
        rows = await conn.fetch(_QUERY_BULK)
    for r in rows:
        record = CaseRecord.model_validate(dict(r))
        yield (record.model_dump_json() + "\n").encode()


@router.get(
    "/bulk/ndjson",
    summary="Bulk NDJSON export of all case reports",
    responses={
        200: {
            "description": "All case reports as newline-delimited JSON (one record per line)",
            "content": {"application/x-ndjson": {}},
        }
    },
)
async def bulk_ndjson() -> StreamingResponse:
    """Full dataset as NDJSON. Each line is a CaseRecord JSON object.

    Suitable for direct ingestion into R (jsonlite), Python (pandas/polars),
    and epidemiological analysis pipelines. Updated in real time.

    Attribution required under CC BY 4.0:
    HORIZON Hantavirus Surveillance Platform (hantavirus.software), 79th Unit Limited.
    """
    return StreamingResponse(
        _ndjson_stream(),
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": 'attachment; filename="horizon-cases.ndjson"',
            "X-Data-License": "CC-BY-4.0",
            "Cache-Control": "public, max-age=300, stale-while-revalidate=60",
        },
    )
