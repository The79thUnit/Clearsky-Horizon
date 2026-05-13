"""
Celery tasks for the structured-fact extraction pipeline.

Two tasks:

  run_hondius_extractor — every 15 min via beat. Scans recent case_reports
                          for MV Hondius mentions, writes proposals to
                          extraction_proposals (idempotent via fingerprint),
                          and immediately calls the auto-applier.

  apply_proposals       — separable so it can also be run on demand.
                          Walks unapplied proposals; for NATO A1/A2/B1/B2
                          sources, accepts the proposal and updates the
                          incident ontology (incident_countries, etc.).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import psycopg
from celery import shared_task

from ..celery_app import app  # noqa: F401 — registers tasks
from ..config import settings
from ..extractors.hondius_extractor import (
    EXTRACTOR_VERSION,
    INCIDENT_CODE,
    CaseReport,
    Proposal,
    extract_many,
)

log = logging.getLogger("horizon.extraction")

# High-trust NATO Admiralty Scale tiers — these get auto-applied.
AUTO_APPLY_NATO = {("A", "1"), ("A", "2"), ("B", "1"), ("B", "2")}

# How far back to look on each run (in hours). 24h gives enough buffer to
# pick up articles ingested between runs even if a beat tick is skipped.
LOOKBACK_HOURS = 24


def _fetch_recent_reports(
    conn: psycopg.Connection,
    lookback_hours: int = LOOKBACK_HOURS,
) -> list[CaseReport]:
    """Load recently-ingested case_reports for the extractor to scan.

    The SQL pre-filter is intentionally broad (any hantavirus mention OR
    hondius) so that _is_relevant() + _classify_tie() in Python can make
    the precision call.  The old narrow filter ('%hantavirus%cruise%')
    blocked articles phrased as "cruise ship hantavirus" (reversed order)
    or that used "vessel"/"ship" without the word "cruise".
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cr.id::text AS id,
                   cr.title,
                   COALESCE(cr.summary, '') AS summary,
                   cr.country_iso2,
                   s.code AS source_code,
                   cr.raw_url,
                   cr.reported_date,
                   cr.ingested_at,
                   qs.nato_reliability,
                   qs.nato_credibility
            FROM case_reports cr
            JOIN sources s          ON s.id = cr.source_id
            LEFT JOIN qualification_scores qs ON qs.case_report_id = cr.id
            WHERE cr.ingested_at >= %s
              AND (
                lower(cr.title)   LIKE '%%hondius%%'
                OR lower(cr.summary) LIKE '%%hondius%%'
                OR lower(cr.title)   LIKE '%%hantavirus%%'
                OR lower(cr.summary) LIKE '%%hantavirus%%'
              )
            ORDER BY cr.ingested_at DESC
            """,
            (cutoff,),
        )
        rows = cur.fetchall()
    return [
        CaseReport(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            country_iso2=(row["country_iso2"].strip() if row["country_iso2"] else None),
            source_code=row["source_code"],
            nato_reliability=(row["nato_reliability"] or None),
            nato_credibility=(row["nato_credibility"] or None),
            raw_url=row["raw_url"],
            reported_date=row["reported_date"],
            ingested_at=row["ingested_at"],
        )
        for row in rows
    ]


def _persist_proposal(conn: psycopg.Connection, p: Proposal) -> bool:
    """Insert one proposal. Returns True if newly inserted (not duplicate)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO extraction_proposals (
                case_id, incident_code, extractor_version,
                fact_type, country_iso2, value_numeric, value_text,
                value_lat, value_lng,
                source_code, source_url,
                nato_reliability, nato_credibility, extractor_confidence,
                cluster_tie_score, cluster_tie_reason,
                fingerprint, notes
            ) VALUES (
                %s::uuid, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s
            )
            ON CONFLICT (fingerprint) DO NOTHING
            RETURNING id
            """,
            (
                p.case_id, INCIDENT_CODE, EXTRACTOR_VERSION,
                p.fact_type, p.country_iso2, p.value_numeric, p.value_text,
                p.value_lat, p.value_lng,
                p.source_code, p.source_url,
                p.nato_reliability, p.nato_credibility, p.extractor_confidence,
                p.cluster_tie_score, p.cluster_tie_reason,
                p.fingerprint, p.notes,
            ),
        )
        return cur.fetchone() is not None


def _auto_apply(conn: psycopg.Connection) -> dict[str, int]:
    """
    Auto-apply unapplied proposals for the Hondius incident.

    Rules:
      - Only NATO A1/A2/B1/B2 sources auto-apply.
      - Count facts (confirmed_count/suspected_count/death_count):
          incident_countries.{column} = MAX(current, proposed).
      - Port-call facts: INSERT new port entity + vessel_track_point if
        no existing port is within ~10 km AND the date hasn't been seen.
      - Death-event facts: INSERT new death_event entity if no existing
        one within ~10 km AND same occurred_at date.
      - Flight-route facts: INSERT new flight_route entity if no existing
        one with the same origin-destination pair.
    """
    counts = {
        "confirmed": 0, "suspected": 0, "deaths": 0,
        "ports": 0, "death_events": 0, "flights": 0, "rejected": 0,
    }

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, fact_type, country_iso2, value_numeric, value_text,
                   value_lat, value_lng, source_code, source_url,
                   nato_reliability, nato_credibility, extractor_confidence,
                   cluster_tie_score, cluster_tie_reason
            FROM extraction_proposals
            WHERE incident_code = %s
              AND applied = false
              AND rejected = false
              AND cluster_tie_score >= 1.0     -- STRONG ties only
            """,
            (INCIDENT_CODE,),
        )
        unapplied = cur.fetchall()

    incident_id: str | None = None
    with conn.cursor() as cur:
        cur.execute("SELECT id::text AS id FROM incidents WHERE code = %s", (INCIDENT_CODE,))
        row = cur.fetchone()
        if row:
            incident_id = row["id"]
    if incident_id is None:
        log.warning("auto-apply: no incident row for code %s", INCIDENT_CODE)
        return counts

    # Fetch global authoritative caps from WHO/ECDC confirmed data.
    # A per-country proposal that exceeds the global cluster total is
    # a cluster-total misattribution (e.g. "9 confirmed" in a Spain
    # article means the cluster has 9 total, not that Spain has 9).
    # Using these caps prevents a single country absorbing the whole
    # cluster count. Default to a large sentinel (999) if not set.
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT MAX(confirmed_cases) AS conf,
                   MAX(suspected_cases) AS susp,
                   MAX(deaths)          AS deaths
            FROM incident_authoritative_counts
            WHERE incident_id = %s::uuid
            """,
            (incident_id,),
        )
        caps = cur.fetchone()
    global_cap_confirmed = int(caps["conf"]  or 999)
    global_cap_suspected = int(caps["susp"]  or 999)
    global_cap_deaths    = int(caps["deaths"] or 999)

    SPATIAL_TOL_DEG = 0.10  # ~10 km — dedupe threshold for port/death entities

    for p in unapplied:
        nato = (p.get("nato_reliability"), p.get("nato_credibility"))
        if nato not in AUTO_APPLY_NATO:
            continue  # leave for analyst review

        ft = p["fact_type"]
        applied_target: str | None = None

        # ---- Count-based facts (per-country) ----
        if ft in ("confirmed_count", "suspected_count", "death_count"):
            if p.get("country_iso2") is None or p.get("value_numeric") is None:
                continue
            column = {
                "confirmed_count": "confirmed_count",
                "suspected_count": "suspected_count",
                "death_count": "deaths",
            }[ft]
            # Global-cap guard: a per-country count that equals or exceeds
            # the cluster-wide authoritative total is almost certainly a
            # cluster-total misattribution (e.g., "Spain: 9 confirmed" where
            # 9 is the cluster total, not Spain-specific). Reject silently.
            cap = {
                "confirmed_count": global_cap_confirmed,
                "suspected_count": global_cap_suspected,
                "deaths":          global_cap_deaths,
            }[column]
            if int(p["value_numeric"]) >= cap:
                log.info(
                    "Path A rejected (global cap): %s.%s=%d >= cap=%d",
                    p.get("country_iso2"), column, p["value_numeric"], cap,
                )
                continue
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO incident_countries (incident_id, country_iso2,
                        confirmed_count, suspected_count, deaths)
                    VALUES (%s::uuid, %s, 0, 0, 0)
                    ON CONFLICT (incident_id, country_iso2) DO NOTHING
                    """,
                    (incident_id, p["country_iso2"]),
                )
                cur.execute(
                    f"""
                    UPDATE incident_countries
                    SET {column} = GREATEST({column}, %s),
                        last_updated_at = now()
                    WHERE incident_id = %s::uuid AND country_iso2 = %s
                    """,
                    (p["value_numeric"], incident_id, p["country_iso2"]),
                )
            applied_target = f"incident_countries.{p['country_iso2']}.{column}"
            if column == "confirmed_count":
                counts["confirmed"] += 1
            elif column == "suspected_count":
                counts["suspected"] += 1
            elif column == "deaths":
                counts["deaths"] += 1

        # ---- New port-call entity + relationship ----
        elif ft == "port_call":
            lat, lng, label = p.get("value_lat"), p.get("value_lng"), p.get("value_text")
            if lat is None or lng is None or not label:
                continue
            with conn.cursor() as cur:
                # Dedupe: any existing port within ~10km?
                cur.execute(
                    """
                    SELECT id::text AS id
                    FROM entities
                    WHERE incident_id = %s::uuid
                      AND entity_type = 'port'
                      AND ABS((properties->>'lat')::float8 - %s) < %s
                      AND ABS((properties->>'lng')::float8 - %s) < %s
                    LIMIT 1
                    """,
                    (incident_id, lat, SPATIAL_TOL_DEG, lng, SPATIAL_TOL_DEG),
                )
                existing = cur.fetchone()
                if existing:
                    applied_target = f"entities.port.{existing['id']} (dedupe)"
                else:
                    cur.execute(
                        """
                        INSERT INTO entities (id, incident_id, entity_type,
                            public_label, properties)
                        VALUES (gen_random_uuid(), %s::uuid, 'port', %s, %s::jsonb)
                        RETURNING id::text AS id
                        """,
                        (
                            incident_id,
                            label.title(),
                            json.dumps({
                                "lat": lat,
                                "lng": lng,
                                "country_iso2": p.get("country_iso2"),
                                "auto_extracted": True,
                                "extractor_confidence": p.get("extractor_confidence"),
                                "source_url": p.get("source_url"),
                                "source_code": p.get("source_code"),
                            }),
                        ),
                    )
                    new_id = cur.fetchone()["id"]
                    applied_target = f"entities.port.{new_id} (new)"
                    counts["ports"] += 1

        # ---- New death_event entity ----
        elif ft == "death_event":
            lat, lng, label = p.get("value_lat"), p.get("value_lng"), p.get("value_text")
            if lat is None or lng is None:
                continue
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id::text AS id
                    FROM entities
                    WHERE incident_id = %s::uuid
                      AND entity_type = 'death_event'
                      AND ABS((properties->>'lat')::float8 - %s) < %s
                      AND ABS((properties->>'lng')::float8 - %s) < %s
                    LIMIT 1
                    """,
                    (incident_id, lat, SPATIAL_TOL_DEG, lng, SPATIAL_TOL_DEG),
                )
                existing = cur.fetchone()
                if existing:
                    applied_target = f"entities.death_event.{existing['id']} (dedupe)"
                else:
                    cur.execute(
                        """
                        INSERT INTO entities (id, incident_id, entity_type,
                            public_label, properties)
                        VALUES (gen_random_uuid(), %s::uuid, 'death_event', %s, %s::jsonb)
                        RETURNING id::text AS id
                        """,
                        (
                            incident_id,
                            f"Death — {(label or 'auto-extracted').title()}",
                            json.dumps({
                                "lat": lat,
                                "lng": lng,
                                "location_type": "auto",
                                "auto_extracted": True,
                                "extractor_confidence": p.get("extractor_confidence"),
                                "source_url": p.get("source_url"),
                                "source_code": p.get("source_code"),
                            }),
                        ),
                    )
                    new_id = cur.fetchone()["id"]
                    applied_target = f"entities.death_event.{new_id} (new)"
                    counts["death_events"] += 1

        # ---- New flight_route entity ----
        elif ft == "flight_route":
            dest_lat, dest_lng, dest_label = p.get("value_lat"), p.get("value_lng"), p.get("value_text")
            if dest_lat is None or dest_lng is None or not dest_label:
                continue
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id::text AS id
                    FROM entities
                    WHERE incident_id = %s::uuid
                      AND entity_type = 'flight_route'
                      AND ABS((properties->>'dest_lat')::float8 - %s) < %s
                      AND ABS((properties->>'dest_lng')::float8 - %s) < %s
                    LIMIT 1
                    """,
                    (incident_id, dest_lat, SPATIAL_TOL_DEG, dest_lng, SPATIAL_TOL_DEG),
                )
                existing = cur.fetchone()
                if existing:
                    applied_target = f"entities.flight_route.{existing['id']} (dedupe)"
                else:
                    # Without an explicit origin we can't draw a great-circle.
                    # Use Tenerife as fallback origin since most repatriations
                    # were post-Tenerife evacuations per CNN/WHO.
                    cur.execute(
                        """
                        INSERT INTO entities (id, incident_id, entity_type,
                            public_label, properties)
                        VALUES (gen_random_uuid(), %s::uuid, 'flight_route', %s, %s::jsonb)
                        RETURNING id::text AS id
                        """,
                        (
                            incident_id,
                            f"Auto-extracted flight — Tenerife → {dest_label.title()}",
                            json.dumps({
                                "origin_label": "Tenerife (TFS / TFN)",
                                "origin_lat": 28.4682, "origin_lng": -16.2546,
                                "dest_label": dest_label.title(),
                                "dest_lat": dest_lat, "dest_lng": dest_lng,
                                "pax_count": p.get("value_numeric"),
                                "purpose": "repatriation",
                                "confidence": p.get("extractor_confidence"),
                                "source_url": p.get("source_url"),
                                "source_code": p.get("source_code"),
                                "auto_extracted": True,
                            }),
                        ),
                    )
                    new_id = cur.fetchone()["id"]
                    applied_target = f"entities.flight_route.{new_id} (new)"
                    counts["flights"] += 1
        else:
            continue

        if applied_target:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE extraction_proposals
                    SET applied = true, applied_at = now(), applied_target = %s
                    WHERE id = %s
                    """,
                    (applied_target, p["id"]),
                )

    # ------------------------------------------------------------------
    # SECOND PASS: corroboration applier
    #
    # Phoenix rule (12 May 2026 PM): when ≥3 distinct articles within
    # the last 48h independently report the same per-country count for
    # the Hondius cluster (STRONG tie), apply MAX(value) even if no
    # individual source is NATO A/B. This catches multi-outlet news-wire
    # reporting that's reliable by virtue of independent corroboration.
    # ------------------------------------------------------------------
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fact_type,
                   country_iso2,
                   MAX(value_numeric)             AS max_value,
                   COUNT(DISTINCT case_id)        AS n_articles,
                   COUNT(DISTINCT source_code)    AS n_connectors,
                   ARRAY_AGG(DISTINCT source_url) AS source_urls,
                   ARRAY_AGG(DISTINCT source_code) AS source_codes
            FROM extraction_proposals
            WHERE incident_code = %s
              AND applied = false
              AND rejected = false
              AND cluster_tie_score >= 1.0
              AND country_iso2 IS NOT NULL
              AND value_numeric IS NOT NULL
              AND fact_type IN ('confirmed_count', 'suspected_count', 'death_count')
              AND extracted_at >= now() - INTERVAL '48 hours'
              AND extractor_confidence >= 0.65   -- require explicit nearby-text attribution
            GROUP BY 1, 2
            HAVING COUNT(DISTINCT case_id) >= 3
            """,
            (INCIDENT_CODE,),
        )
        corroborated = cur.fetchall()

    for row in corroborated:
        column = {
            "confirmed_count": "confirmed_count",
            "suspected_count": "suspected_count",
            "death_count":     "deaths",
        }[row["fact_type"]]
        max_value = int(row["max_value"])
        country = row["country_iso2"]
        n_articles = int(row["n_articles"])

        # Global-cap guard for Path B (same rule as Path A).
        # MAX(value_numeric) for a group may reflect the cluster total being
        # reported in the same article that mentions the country. Reject the
        # whole group if its maximum exceeds the global authoritative cap.
        cap = {
            "confirmed_count": global_cap_confirmed,
            "suspected_count": global_cap_suspected,
            "deaths":          global_cap_deaths,
        }[column]
        if max_value >= cap:
            log.info(
                "Path B rejected (global cap): %s.%s MAX=%d >= cap=%d "
                "from %d articles — likely cluster-total misattribution",
                country, column, max_value, cap, n_articles,
            )
            continue
        # Audit trail: list the URLs that corroborated
        urls = row["source_urls"] or []
        target = (
            f"incident_countries.{country}.{column} "
            f"[corroborated by {n_articles} articles across "
            f"{int(row['n_connectors'])} connectors]"
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO incident_countries (incident_id, country_iso2,
                    confirmed_count, suspected_count, deaths)
                VALUES (%s::uuid, %s, 0, 0, 0)
                ON CONFLICT (incident_id, country_iso2) DO NOTHING
                """,
                (incident_id, country),
            )
            cur.execute(
                f"""
                UPDATE incident_countries
                SET {column} = GREATEST({column}, %s),
                    last_updated_at = now()
                WHERE incident_id = %s::uuid AND country_iso2 = %s
                """,
                (max_value, incident_id, country),
            )
            # Mark every corroborating proposal as applied — citation chain
            cur.execute(
                """
                UPDATE extraction_proposals
                SET applied = true, applied_at = now(),
                    applied_target = %s,
                    notes = COALESCE(notes, '') || E'\n[citation chain]\n' || %s
                WHERE incident_code = %s
                  AND fact_type = %s
                  AND country_iso2 = %s
                  AND cluster_tie_score >= 1.0
                  AND applied = false
                  AND extracted_at >= now() - INTERVAL '48 hours'
                """,
                (target, "\n".join(urls), INCIDENT_CODE, row["fact_type"], country),
            )

        if column == "confirmed_count":
            counts["confirmed"] += 1
        elif column == "suspected_count":
            counts["suspected"] += 1
        elif column == "deaths":
            counts["deaths"] += 1

    conn.commit()
    return counts


def _link_articles_to_incident(conn: psycopg.Connection) -> int:
    """
    Auto-link any Hondius-tied case_report to the mv-hondius-2026 incident.
    Linking criterion = the article passes _is_relevant AND _classify_tie
    returns a score >= 1.0 (STRONG tie). Updates case_reports.incident_id
    so the dossier / chronology / Reports view show every corroborating
    article alongside the manually-curated facts.
    """
    from ..extractors.hondius_extractor import _classify_tie, _is_relevant, _normalise

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM incidents WHERE code = %s",
            (INCIDENT_CODE,),
        )
        row = cur.fetchone()
        if row is None:
            return 0
        incident_id = row["id"]

        # Pull unlinked articles whose text might be Hondius-related.
        # Broad SQL filter (any hantavirus OR hondius) — _is_relevant +
        # _classify_tie handle precision. The old '%hantavirus%cruise%'
        # pattern required "hantavirus" to appear before "cruise" which
        # excluded ~half of real-world headlines.
        cur.execute(
            """
            SELECT id, title, COALESCE(summary, '') AS summary, country_iso2
            FROM case_reports
            WHERE incident_id IS NULL
              AND (
                lower(title)   LIKE '%hondius%'
                OR lower(summary) LIKE '%hondius%'
                OR lower(title)   LIKE '%hantavirus%'
                OR lower(summary) LIKE '%hantavirus%'
              )
            """,
        )
        candidates = cur.fetchall()

    linked = 0
    for c in candidates:
        # Reuse the same relevance + tie classifier the extractor uses
        # so the linking criterion matches the extraction criterion.
        # Minimum data needed for _is_relevant: title + summary.
        from ..extractors.hondius_extractor import CaseReport
        dummy = CaseReport(
            id=c["id"], title=c["title"], summary=c["summary"],
            country_iso2=c["country_iso2"], source_code="",
            nato_reliability=None, nato_credibility=None,
            raw_url="", reported_date=None, ingested_at=datetime.now(timezone.utc),
        )
        if not _is_relevant(dummy):
            continue
        text = _normalise(f"{c['title']}. {c['summary']}")
        tie, _ = _classify_tie(text)
        if tie < 1.0:
            continue   # Phoenix rule: STRONG tie only

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE case_reports SET incident_id = %s::uuid WHERE id = %s::uuid",
                (incident_id, c["id"]),
            )
            linked += 1
    conn.commit()
    return linked


@shared_task(name="horizon_worker.tasks.extraction.run_hondius_extractor")  # type: ignore[misc]
def run_hondius_extractor() -> dict[str, int]:
    """
    Beat-scheduled every 15 min. Scans recent articles, writes proposals,
    auto-applies high-trust ones to incident_countries, AND auto-links
    STRONG-tied articles to the incident so they appear in the dossier.
    """
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        # 1. Auto-link Hondius-tied articles to the incident
        linked = _link_articles_to_incident(conn)

        # 2. Extract structured facts from recent articles
        reports = _fetch_recent_reports(conn)
        proposals = extract_many(reports)

        new_proposals = 0
        for p in proposals:
            if _persist_proposal(conn, p):
                new_proposals += 1
        conn.commit()

        # 3. Auto-apply Path A (NATO A/B + country) and Path B (≥3 sources)
        applied = _auto_apply(conn)

    log.info(
        "Hondius extractor: linked %d new articles, scanned %d, %d proposals, applied %s",
        linked, len(reports), new_proposals, applied,
    )
    return {
        "articles_linked_to_incident": linked,
        "articles_scanned": len(reports),
        "new_proposals": new_proposals,
        **applied,
    }


@shared_task(name="horizon_worker.tasks.extraction.apply_proposals")  # type: ignore[misc]
def apply_proposals() -> dict[str, int]:
    """Standalone applier — useful for one-shot re-application."""
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        return _auto_apply(conn)


@shared_task(name="horizon_worker.tasks.extraction.backfill_hondius_extraction")  # type: ignore[misc]
def backfill_hondius_extraction(lookback_hours: int = 168) -> dict[str, int]:
    """
    One-shot catch-up task.  Invoke manually after a SQL-filter or extractor
    fix to reprocess historical articles that were previously missed.

    Default window is 168h (7 days).  Override via:
        celery -A horizon_worker.celery_app call \\
            horizon_worker.tasks.extraction.backfill_hondius_extraction \\
            --args '[336]'

    Does the same three steps as run_hondius_extractor but with a custom
    lookback so articles outside the normal 24h window are picked up.
    The _link_articles_to_incident step has no time limit — it always
    scans ALL unlinked articles — so that part is already handled by every
    normal tick after the SQL-filter fix lands.
    """
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        # 1. Link any still-unlinked Hondius articles (no time limit)
        linked = _link_articles_to_incident(conn)

        # 2. Extract facts over the extended window
        reports = _fetch_recent_reports(conn, lookback_hours=lookback_hours)
        proposals = extract_many(reports)

        new_proposals = 0
        for p in proposals:
            if _persist_proposal(conn, p):
                new_proposals += 1
        conn.commit()

        # 3. Auto-apply: Path A (NATO A/B) + Path B (≥3 corroborating sources)
        applied = _auto_apply(conn)

    log.info(
        "Backfill (lookback=%dh): linked %d articles, scanned %d, "
        "%d new proposals, applied %s",
        lookback_hours, linked, len(reports), new_proposals, applied,
    )
    return {
        "lookback_hours": lookback_hours,
        "articles_linked_to_incident": linked,
        "articles_scanned": len(reports),
        "new_proposals": new_proposals,
        **applied,
    }
