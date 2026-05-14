"""Automated analyst-confidence pre-fill task (HORIZON-AUTO-SCORER/1.0).

Runs hourly via Celery beat. Finds case_reports whose qualification_scores
row has analyst_confidence IS NULL and applies a rule-based score derived
from the source's NATO reliability band.

This is explicitly a MACHINE-ASSISTED pre-fill:
  - analyst_id = 'HORIZON-AUTO-SCORER/1.0'
  - analyst_notes documents the NATO band used
  - analyst_confidence is set within a [floor, cap] band per NATO tier
  - Human analysts can override by writing a new analyst_confidence value

Reddit records (code='reddit') are NEVER auto-scored. They remain NULL
until a human analyst explicitly reviews and approves a Reddit-sourced record.
This prevents unqualified social-rumour content from reaching the public API.

Score bands:
    NATO A (completely reliable):   0.70 – 0.92 (pipeline + 0.05, capped)
    NATO B (usually reliable):      0.60 – 0.85 (pipeline + 0.03, capped)
    NATO C (fairly reliable):       0.45 – 0.75 (pipeline + 0.01, capped)
    NATO D (not usually reliable):  0.30 – 0.60 (pipeline unchanged, capped)
    NATO E (unreliable):            0.00 – 0.30 (pipeline x 0.70, capped)
    NATO F (cannot be judged):      0.00 – 0.15 (pipeline x 0.40, capped)

Public API filter (cases.py): records with analyst_confidence IS NULL are
hidden from the public JSON API (they are still accessible via the bulk
NDJSON export for research transparency). After this task runs, any new
non-Reddit ingest should be surfaced within one hourly cycle.
"""

from __future__ import annotations

import logging

import psycopg
import psycopg.rows

from ..config import settings

log = logging.getLogger("horizon.auto_qualify")

# SQL: count how many records still need scoring
_SQL_COUNT_PENDING = """
SELECT COUNT(*) AS n
FROM qualification_scores qs
JOIN case_reports cr ON cr.id = qs.case_report_id
JOIN sources s ON s.id = cr.source_id
WHERE qs.analyst_confidence IS NULL
  AND s.code != 'reddit'
"""

# SQL: batch score all pending non-Reddit records in one UPDATE
_SQL_BATCH_SCORE = """
UPDATE qualification_scores qs
SET
    analyst_confidence = (
        CASE s.nato_reliability
            WHEN 'A' THEN LEAST(0.92, GREATEST(0.70, qs.pipeline_confidence + 0.05))
            WHEN 'B' THEN LEAST(0.85, GREATEST(0.60, qs.pipeline_confidence + 0.03))
            WHEN 'C' THEN LEAST(0.75, GREATEST(0.45, qs.pipeline_confidence + 0.01))
            WHEN 'D' THEN LEAST(0.60, GREATEST(0.30, qs.pipeline_confidence))
            WHEN 'E' THEN LEAST(0.30, qs.pipeline_confidence * 0.70)
            ELSE           LEAST(0.15, qs.pipeline_confidence * 0.40)
        END
    )::NUMERIC(3,2),
    analyst_id    = 'HORIZON-AUTO-SCORER/1.0',
    analyst_at    = NOW(),
    analyst_notes = 'AUTO-SCORER/1.0. NATO-' || s.nato_reliability
                 || s.nato_credibility::text || ' (' || s.name || '). '
                 || 'Machine pre-fill. Human override replaces this.',
    updated_at    = NOW()
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
WHERE qs.case_report_id = cr.id
  AND qs.analyst_confidence IS NULL
  AND s.code != 'reddit'
"""

# SQL: fetch a breakdown by NATO band for logging
_SQL_BREAKDOWN = """
SELECT
    s.nato_reliability,
    COUNT(*)::int           AS records_scored,
    MIN(qs.analyst_confidence)::float   AS min_score,
    MAX(qs.analyst_confidence)::float   AS max_score,
    ROUND(AVG(qs.analyst_confidence)::numeric, 3)::float AS avg_score
FROM qualification_scores qs
JOIN case_reports cr ON cr.id = qs.case_report_id
JOIN sources s ON s.id = cr.source_id
WHERE qs.analyst_id = 'HORIZON-AUTO-SCORER/1.0'
  AND qs.analyst_at >= NOW() - INTERVAL '5 minutes'
GROUP BY s.nato_reliability
ORDER BY s.nato_reliability
"""


def run_auto_qualifier() -> dict:  # type: ignore[return]
    """Core logic: count pending records, score them, return a summary dict.

    Separated from the Celery task decorator so it can be called directly
    from migration scripts or management commands without a running worker.
    """
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_COUNT_PENDING)
            row = cur.fetchone()
            pending = int(row["n"]) if row else 0

        if pending == 0:
            log.info("auto_qualify: no unscored non-Reddit records, skipping")
            return {"scored": 0, "breakdown": []}

        log.info("auto_qualify: %d records pending scoring", pending)

        with conn.cursor() as cur:
            cur.execute(_SQL_BATCH_SCORE)
            scored = cur.rowcount

        with conn.cursor() as cur:
            cur.execute(_SQL_BREAKDOWN)
            breakdown = [dict(r) for r in cur.fetchall()]

        conn.commit()

    log.info(
        "auto_qualify: scored %d records — %s",
        scored,
        ", ".join(
            f"NATO-{b['nato_reliability']}: {b['records_scored']} (avg {b['avg_score']:.3f})"
            for b in breakdown
        ),
    )
    return {"scored": scored, "breakdown": breakdown}


try:
    from celery import shared_task

    @shared_task(  # type: ignore[misc]
        name="horizon_worker.tasks.auto_qualify.run_auto_qualifier_task"
    )
    def run_auto_qualifier_task() -> dict:
        """Celery entry point — beat-scheduled hourly. Delegates to run_auto_qualifier()."""
        return run_auto_qualifier()

except ImportError:
    # Allow direct import outside a Celery context (e.g. from migration scripts).
    pass
