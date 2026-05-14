"""One-off backfill: recompute pipeline_confidence based on actual corroboration.

For every case_report with a content_topic_hash, count distinct other-source
corroborators within +/- 7 days of its ingestion, recompute pipeline_confidence
using the canonical qualification module, and UPDATE the qualification_scores
row in place.

Was needed because ingest.py historically passed corroboration_count=0 on every
new record. Fixed in ingest.py 14 May 2026; this script repairs existing rows.

Idempotent and safe to re-run: re-running on the same DB will compute the same
result. Can also be scheduled (e.g. hourly) so late-arriving corroborators
update existing records' confidence over time.

Run inside the worker container:
    docker compose -f docker-compose.prod.yml exec worker \\
        python -m horizon_worker.tasks.backfill_corroboration
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime

from ..core.nato import NATOScore
from ..core.qualification import QualificationInputs, calculate
from ..db import get_conn

logger = logging.getLogger(__name__)


def run_backfill() -> dict[str, int]:
    """Recompute pipeline_confidence + factors for every record with a topic hash.

    Returns a summary dict so callers can log/test against the result.
    """
    today = datetime.now(tz=UTC).date()

    examined = 0
    updated = 0
    unchanged = 0
    corroborated = 0

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    cr.id,
                    cr.content_topic_hash,
                    cr.reported_date,
                    cr.source_id,
                    cr.ingested_at,
                    qs.nato_reliability,
                    qs.nato_credibility,
                    qs.pipeline_confidence AS old_confidence
                FROM case_reports cr
                JOIN qualification_scores qs ON qs.case_report_id = cr.id
                WHERE cr.content_topic_hash IS NOT NULL
                ORDER BY cr.ingested_at DESC
                """
            )
            rows = cur.fetchall()

            logger.info("backfill: examining %d records with topic hashes", len(rows))

            for row in rows:
                examined += 1

                cur.execute(
                    """
                    SELECT COUNT(DISTINCT source_id)::int AS n
                    FROM case_reports
                    WHERE content_topic_hash = %s
                      AND source_id != %s
                      AND ingested_at BETWEEN %s::timestamptz - INTERVAL '7 days'
                                          AND %s::timestamptz + INTERVAL '7 days'
                    """,
                    (
                        row["content_topic_hash"],
                        row["source_id"],
                        row["ingested_at"],
                        row["ingested_at"],
                    ),
                )
                n_corroborators = cur.fetchone()["n"] or 0

                if n_corroborators > 0:
                    corroborated += 1

                age_days = 0
                if row["reported_date"]:
                    age_days = max(0, (today - row["reported_date"]).days)

                nato = NATOScore.parse(
                    f"{row['nato_reliability']}{row['nato_credibility']}"
                )
                qresult = calculate(
                    QualificationInputs(
                        nato=nato,
                        corroboration_count=n_corroborators,
                        age_days=age_days,
                    )
                )

                new_conf = qresult.pipeline_confidence
                old_conf = float(row["old_confidence"])

                if abs(new_conf - old_conf) < 0.005 and n_corroborators == 0:
                    unchanged += 1
                    continue

                cur.execute(
                    """
                    UPDATE qualification_scores
                    SET pipeline_confidence = %s,
                        pipeline_factors = %s::jsonb
                    WHERE case_report_id = %s
                    """,
                    (
                        qresult.pipeline_confidence,
                        json.dumps(qresult.factors),
                        row["id"],
                    ),
                )
                updated += 1

        conn.commit()

    summary = {
        "examined": examined,
        "corroborated": corroborated,
        "updated": updated,
        "unchanged": unchanged,
    }
    logger.info("backfill complete: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run_backfill()
    print(json.dumps(result, indent=2))
