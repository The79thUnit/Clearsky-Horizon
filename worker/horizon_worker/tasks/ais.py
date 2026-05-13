"""
AIS Celery tasks for vessel tracking (Kpler / MarineTraffic backend).

Two tasks:

  poll_latest_positions — every 2 min via beat. Pulls /ais-latest for every
                          tracked MMSI, INSERTs each new position into
                          vessel_track_points, and UPSERTs vessel-level
                          dynamic fields (destination, eta, current sog/cog,
                          last_ais_at, current_nav_status) onto the
                          corresponding vessel entity's properties JSONB.

  backfill_history     — one-shot, manually invoked. Calls /ais-historical
                          for one MMSI over an explicit window. Used to
                          populate the historical route line when a vessel
                          is first added.

Both tasks log a one-line summary so `docker logs horizon-worker` shows
how many positions came in on each tick.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta, timezone

import psycopg
from celery import shared_task

from ..celery_app import app  # noqa: F401 — registers tasks with the worker
from ..config import settings
from ..connectors.kpler_ais import PositionFix, fetch_historical, fetch_latest

log = logging.getLogger("horizon.ais")

# Vessels we currently track. Match by MMSI against vessel entity rows
# where entities.properties->>'mmsi' equals the value below. Adding a new
# vessel = add an entity row + append its MMSI here.
TRACKED_MMSIS: list[str] = [
    "244327000",  # MV Hondius (NL) — IMO 9818709
]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _resolve_vessel_ids(conn: psycopg.Connection) -> dict[str, str]:
    """Map MMSI → vessel entity UUID for each tracked MMSI."""
    out: dict[str, str] = {}
    with conn.cursor() as cur:
        for mmsi in TRACKED_MMSIS:
            cur.execute(
                """
                SELECT id::text AS id
                FROM entities
                WHERE entity_type = 'vessel'
                  AND properties->>'mmsi' = %s
                LIMIT 1
                """,
                (mmsi,),
            )
            row = cur.fetchone()
            if row is not None:
                out[mmsi] = row["id"]
    return out


def _persist_fix(
    conn: psycopg.Connection,
    vessel_entity_id: str,
    fix: PositionFix,
) -> bool:
    """
    Insert one position fix into vessel_track_points and update the
    vessel entity's dynamic properties. Returns True if a new row was
    inserted (False if it was a duplicate ts and ON CONFLICT skipped).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vessel_track_points (
                vessel_entity_id, ts, lat, lng, speed_knots, heading, source, src_citation
            ) VALUES (%s, %s, %s, %s, %s, %s, 'marinetraffic',
                      '[PUBLIC] Kpler/MarineTraffic AIS live position report')
            ON CONFLICT DO NOTHING
            RETURNING ts
            """,
            (
                vessel_entity_id,
                fix.pos_dt,
                fix.lat,
                fix.lon,
                fix.sog,
                fix.heading,
            ),
        )
        inserted = cur.fetchone() is not None

        # Always refresh the vessel-level dynamic fields. Destination
        # changes mid-voyage; we want the freshest one. We do this even
        # for duplicate-ts inserts since the duplicate check is on
        # (vessel, ts) only.
        dynamic = {
            "current_lat": fix.lat,
            "current_lng": fix.lon,
            "current_sog_knots": fix.sog,
            "current_cog_deg": fix.cog,
            "current_heading_deg": fix.heading,
            "current_nav_status": fix.nav_status,
            "current_destination": fix.destination,
            "current_eta": fix.eta.isoformat() if fix.eta else None,
            "current_pos_src": fix.pos_src,
            "last_ais_at": fix.pos_dt.isoformat(),
        }
        cur.execute(
            """
            UPDATE entities
            SET properties = properties || %s::jsonb
            WHERE id = %s::uuid
            """,
            (json.dumps(dynamic), vessel_entity_id),
        )
        conn.commit()
    return inserted


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@shared_task(name="horizon_worker.tasks.ais.poll_latest_positions")  # type: ignore[misc]
def poll_latest_positions() -> dict[str, int]:
    """Beat-scheduled every 2 min. One round-trip per call."""
    try:
        fixes = fetch_latest(TRACKED_MMSIS)
    except Exception:
        log.exception("Kpler /ais-latest call failed")
        return {"fetched": 0, "inserted": 0, "errors": 1}

    if not fixes:
        log.info("Kpler /ais-latest returned 0 fixes for %s", TRACKED_MMSIS)
        return {"fetched": 0, "inserted": 0, "errors": 0}

    inserted = 0
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        mmsi_to_id = _resolve_vessel_ids(conn)
        for fix in fixes:
            entity_id = mmsi_to_id.get(fix.mmsi)
            if entity_id is None:
                log.warning("no vessel entity for MMSI %s — skipping", fix.mmsi)
                continue
            if _persist_fix(conn, entity_id, fix):
                inserted += 1
            log.info(
                "Kpler fix mmsi=%s lat=%.4f lng=%.4f sog=%s dest=%s eta=%s src=%s",
                fix.mmsi,
                fix.lat,
                fix.lon,
                fix.sog,
                fix.destination,
                fix.eta.isoformat() if fix.eta else None,
                fix.pos_src,
            )

    return {"fetched": len(fixes), "inserted": inserted, "errors": 0}


@shared_task(name="horizon_worker.tasks.ais.backfill_history")  # type: ignore[misc]
def backfill_history(mmsi: str, days_back: int = 30) -> dict[str, int]:
    """
    Pull historical positions for one vessel. Default is 30 days (the
    Kpler trial tier max). Invoke manually:

        docker exec horizon-worker celery -A horizon_worker.celery_app \\
            call horizon_worker.tasks.ais.backfill_history \\
            --args '["244327000", 30]'
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    log.info("Kpler backfill MMSI=%s window=%s..%s", mmsi, start, end)

    try:
        fixes = fetch_historical(mmsi, start, end)
    except Exception:
        log.exception("Kpler /ais-historical backfill failed")
        return {"fetched": 0, "inserted": 0, "errors": 1}

    if not fixes:
        return {"fetched": 0, "inserted": 0, "errors": 0}

    inserted = 0
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        mmsi_to_id = _resolve_vessel_ids(conn)
        entity_id = mmsi_to_id.get(mmsi)
        if entity_id is None:
            log.error("no vessel entity for MMSI %s — backfill aborted", mmsi)
            return {"fetched": len(fixes), "inserted": 0, "errors": 1}
        for fix in fixes:
            if _persist_fix(conn, entity_id, fix):
                inserted += 1

    log.info(
        "Kpler backfill MMSI=%s fetched=%d inserted=%d",
        mmsi,
        len(fixes),
        inserted,
    )
    return {"fetched": len(fixes), "inserted": inserted, "errors": 0}


# ---------------------------------------------------------------------------
# Dead-reckoning fallback
#
# When live AIS hasn't seen the vessel in a while (gappy aisstream coverage),
# we don't want the map to keep showing a position from days ago. Instead we
# interpolate between the projected-route waypoints (already in
# vessel_track_points) using the elapsed wall-clock time.
#
# This is honest: the row is written with source='manual' and a citation
# that says "dead-reckoning between waypoints X and Y". The UI shows it
# with a distinct label so users know it's an estimate, not a live fix.
# ---------------------------------------------------------------------------

DEAD_RECK_STALE_SECS = 2 * 3600    # trigger after 2h with no new live fix
DEAD_RECK_MMSI = "244327000"       # MV Hondius
# COG/SOG projection is most accurate for the first 6h; blend toward
# route interpolation from 6-12h to prevent unbounded open-sea drift.
_COG_PURE_SECS  = 6  * 3600
_COG_BLEND_SECS = 12 * 3600
_EARTH_R_M      = 6_371_000.0


def _project_cog_sog(
    lat: float, lng: float,
    sog_knots: float, cog_deg: float,
    elapsed_s: float,
) -> tuple[float, float]:
    """
    Project (lat, lng) forward by elapsed_s seconds at constant SOG/COG.
    Uses the flat-earth approximation — accurate to < 0.1% for distances
    up to ~100 nm, more than sufficient for a 12-hour dead-reckoning window.
    """
    sog_ms  = sog_knots * 1852.0 / 3600.0        # knots → m/s
    dist_m  = sog_ms * elapsed_s                  # metres travelled
    cog_rad = math.radians(cog_deg)
    lat_rad = math.radians(lat)
    dlat    = dist_m * math.cos(cog_rad) / _EARTH_R_M
    dlng    = dist_m * math.sin(cog_rad) / (_EARTH_R_M * math.cos(lat_rad))
    return lat + math.degrees(dlat), lng + math.degrees(dlng)


@shared_task(name="horizon_worker.tasks.ais.dead_reckon_position")  # type: ignore[misc]
def dead_reckon_position() -> dict[str, int | str]:
    """
    Insert a 'manual' track point when no live AIS has arrived in the last
    DEAD_RECK_STALE_SECS.

    Position method (best available, in order):
      1. COG/SOG projection — uses speed_knots + heading from the last live
         fix.  Most accurate; used pure for the first 6 h.
      2. Blended — linearly weights (1) toward route-interpolation from 6 h
         to 12 h so the projected position converges to the scheduled route
         and accumulated heading-drift is corrected.
      3. Route interpolation — straight-line between the GPS anchor and the
         next port_call waypoint, weighted by elapsed / segment time.
         Used when SOG/COG data is unavailable or elapsed > 12 h.

    Bracket:
      prev = last live GPS fix (aisstream / marinetraffic / myshiptracking).
             Falls back to last port_call if no live fix exists.
      nxt  = next port_call waypoint strictly in the future.

    Idempotent: ON CONFLICT DO NOTHING on (vessel_entity_id, ts).
    """
    now = datetime.now(timezone.utc)
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        mmsi_to_id = _resolve_vessel_ids(conn)
        entity_id = mmsi_to_id.get(DEAD_RECK_MMSI)
        if entity_id is None:
            log.warning("dead-reckon: no vessel entity for MMSI %s", DEAD_RECK_MMSI)
            return {"inserted": 0, "skipped_reason": "no_vessel"}

        # 1. Check freshness of live data.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT max(ts) AS latest_live
                FROM vessel_track_points
                WHERE vessel_entity_id = %s
                  AND source IN ('aisstream', 'marinetraffic', 'myshiptracking', 'cruisemapper')
                """,
                (entity_id,),
            )
            row = cur.fetchone()
        latest_live = row["latest_live"] if row else None
        if latest_live is not None:
            age = (now - latest_live).total_seconds()
            if age < DEAD_RECK_STALE_SECS:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM vessel_track_points
                        WHERE vessel_entity_id = %s
                          AND source = 'manual'
                          AND ts >= (
                            SELECT min(ts) FROM vessel_track_points
                            WHERE vessel_entity_id = %s
                              AND source IN ('aisstream','marinetraffic','myshiptracking','cruisemapper')
                          )
                        """,
                        (entity_id, entity_id),
                    )
                    purged = cur.rowcount
                    conn.commit()
                return {
                    "inserted": 0,
                    "skipped_reason": "fresh_live_fix",
                    "age_s": int(age),
                    "purged_stale_dead_reckon": purged,
                }

        # 2. Build the bracket: GPS anchor + next scheduled waypoint.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, lat::float8 AS lat, lng::float8 AS lng,
                       speed_knots::float8 AS sog, heading::float8 AS cog,
                       source
                FROM vessel_track_points
                WHERE vessel_entity_id = %s
                  AND source IN ('aisstream', 'marinetraffic', 'myshiptracking', 'cruisemapper')
                  AND ts <= %s
                ORDER BY ts DESC LIMIT 1
                """,
                (entity_id, now),
            )
            live_prev = cur.fetchone()

            if live_prev is None:
                cur.execute(
                    """
                    SELECT ts, lat::float8 AS lat, lng::float8 AS lng,
                           NULL::float8 AS sog, NULL::float8 AS cog,
                           'port_call' AS source
                    FROM vessel_track_points
                    WHERE vessel_entity_id = %s AND source = 'port_call' AND ts <= %s
                    ORDER BY ts DESC LIMIT 1
                    """,
                    (entity_id, now),
                )
                live_prev = cur.fetchone()

            cur.execute(
                """
                SELECT ts, lat::float8 AS lat, lng::float8 AS lng
                FROM vessel_track_points
                WHERE vessel_entity_id = %s AND source = 'port_call' AND ts > %s
                ORDER BY ts ASC LIMIT 1
                """,
                (entity_id, now),
            )
            port_nxt = cur.fetchone()

        prev = live_prev
        nxt  = port_nxt

        if prev is None:
            return {"inserted": 0, "skipped_reason": "voyage_not_started"}
        if nxt is None:
            return {"inserted": 0, "skipped_reason": "voyage_complete"}

        # 3. Calculate best-available estimated position.
        elapsed_s  = (now - prev["ts"]).total_seconds()
        seg_span_s = (nxt["ts"] - prev["ts"]).total_seconds()
        if seg_span_s <= 0:
            return {"inserted": 0, "skipped_reason": "zero_segment"}

        # Route-interpolation position (always computed as fallback/blend target).
        f = max(0.0, min(1.0, elapsed_s / seg_span_s))
        interp_lat = prev["lat"] + f * (nxt["lat"] - prev["lat"])
        interp_lng = prev["lng"] + f * (nxt["lng"] - prev["lng"])

        sog = prev.get("sog")
        cog = prev.get("cog")
        method: str

        if (
            sog is not None and cog is not None
            and float(sog) > 0.5
            and elapsed_s <= _COG_BLEND_SECS
        ):
            # COG/SOG projection from GPS anchor.
            cog_lat, cog_lng = _project_cog_sog(
                prev["lat"], prev["lng"], float(sog), float(cog), elapsed_s
            )
            # Blend weight: 0 = pure COG/SOG, 1 = pure route interp.
            blend = max(0.0, (elapsed_s - _COG_PURE_SECS) / (_COG_BLEND_SECS - _COG_PURE_SECS))
            blend = min(1.0, blend)
            lat = (1.0 - blend) * cog_lat + blend * interp_lat
            lng = (1.0 - blend) * cog_lng + blend * interp_lng
            method = f"cog_sog(blend={blend:.2f},sog={sog:.1f},cog={cog:.0f})"
        else:
            lat, lng = interp_lat, interp_lng
            method = "route_interp"

        citation = (
            f"Dead-reckoning [{method}] elapsed={elapsed_s / 3600:.1f}h "
            f"from ({prev['lat']:.4f},{prev['lng']:.4f})@{prev['ts'].isoformat()} "
            f"[{prev.get('source','?')}] "
            f"toward ({nxt['lat']:.4f},{nxt['lng']:.4f})@{nxt['ts'].isoformat()} "
            f"[port_call]; f={f:.3f}"
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vessel_track_points (
                    vessel_entity_id, ts, lat, lng, source, src_citation
                ) VALUES (%s, %s, %s, %s, 'manual', %s)
                ON CONFLICT DO NOTHING
                """,
                (entity_id, now, lat, lng, citation),
            )
            cur.execute(
                """
                UPDATE entities
                SET properties = properties || %s::jsonb
                WHERE id = %s::uuid
                """,
                (
                    json.dumps({
                        "current_lat": lat,
                        "current_lng": lng,
                        "last_ais_at": now.isoformat(),
                        "current_source": "dead_reckoning",
                        "current_pos_src": "EST",
                    }),
                    entity_id,
                ),
            )
            conn.commit()

        log.info(
            "dead-reckon MMSI=%s lat=%.4f lng=%.4f method=%s elapsed=%.1fh",
            DEAD_RECK_MMSI, lat, lng, method, elapsed_s / 3600,
        )
        return {
            "inserted": 1,
            "lat": round(lat, 4),
            "lng": round(lng, 4),
            "method": method,
            "elapsed_h": round(elapsed_s / 3600, 1),
        }


# ---------------------------------------------------------------------------
# MyShipTracking public-page scraper task
#
# Polls every 5 min for each tracked vessel. Writes a vessel_track_point
# row with source='myshiptracking' so the FE can label it correctly
# (🟢 LIVE - myshiptracking). Honest about provenance.
# ---------------------------------------------------------------------------

from ..connectors.myshiptracking import fetch_position as mst_fetch  # noqa: E402
from ..connectors.cruisemapper import fetch_position as cm_fetch  # noqa: E402

# Vessels we scrape. (mmsi, imo) tuples — both required for the URL.
MST_TRACKED: list[tuple[str, str]] = [
    ("244327000", "9818709"),  # MV Hondius
]

# Vessels tracked via CruiseMapper — MMSI only.
CM_TRACKED: list[str] = [
    "244327000",  # MV Hondius
]


@shared_task(name="horizon_worker.tasks.ais.poll_myshiptracking")  # type: ignore[misc]
def poll_myshiptracking() -> dict[str, int]:
    """
    Hit the public MyShipTracking page for each tracked vessel and
    persist the position. Idempotent — duplicate (vessel, ts) within
    the same minute is silently ignored by the unique constraint.
    """
    inserted = 0
    errors = 0
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        mmsi_to_id = _resolve_vessel_ids(conn)
        for mmsi, imo in MST_TRACKED:
            entity_id = mmsi_to_id.get(mmsi)
            if entity_id is None:
                log.warning("myshiptracking: no vessel entity for MMSI %s", mmsi)
                continue
            try:
                fix = mst_fetch(mmsi, imo)
            except Exception:
                log.exception("myshiptracking fetch failed for MMSI %s", mmsi)
                errors += 1
                continue
            if fix is None:
                continue
            try:
                with conn.cursor() as cur:
                    # Dedupe: if the last stored position from MyShipTracking
                    # is the same lat/lng (within ~10 m), skip the INSERT but
                    # still update the vessel entity's last_ais_at so the UI
                    # shows freshness.
                    cur.execute(
                        """
                        SELECT ts, lat::float8 AS lat, lng::float8 AS lng
                        FROM vessel_track_points
                        WHERE vessel_entity_id = %s
                          AND source = 'myshiptracking'
                        ORDER BY ts DESC LIMIT 1
                        """,
                        (entity_id,),
                    )
                    last_row = cur.fetchone()
                    SAME_POS_TOL = 0.0001  # ~10 m
                    is_duplicate = bool(
                        last_row
                        and abs(last_row["lat"] - fix.lat) < SAME_POS_TOL
                        and abs(last_row["lng"] - fix.lng) < SAME_POS_TOL
                    )
                    if is_duplicate and last_row is not None:
                        # If the position hasn't changed but the vessel was
                        # moving, the source is almost certainly serving stale
                        # cached data. Log prominently so it's actionable.
                        last_ts = last_row["ts"]
                        if last_ts.tzinfo is None:
                            from datetime import timezone as _tz
                            last_ts = last_ts.replace(tzinfo=_tz.utc)
                        stale_h = (fix.fetched_at - last_ts).total_seconds() / 3600
                        if stale_h > 1.0 and fix.sog > 1.0:
                            log.warning(
                                "myshiptracking MMSI=%s: position UNCHANGED for %.1fh "
                                "despite sog=%.1f kn — source is serving stale data. "
                                "Dead-reckoning will continue from the %.0f-h-old GPS anchor.",
                                mmsi, stale_h, fix.sog, stale_h,
                            )
                    if not is_duplicate:
                        cur.execute(
                            """
                            INSERT INTO vessel_track_points (
                                vessel_entity_id, ts, lat, lng,
                                speed_knots, heading, source, src_citation
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                'myshiptracking',
                                'Scraped from myshiptracking.com public vessel page'
                            )
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                entity_id,
                                fix.fetched_at,
                                fix.lat,
                                fix.lng,
                                fix.sog,
                                int(round(fix.cog)),
                            ),
                        )
                        if cur.rowcount > 0:
                            inserted += 1
                    # Update vessel entity dynamic state too.
                    cur.execute(
                        """
                        UPDATE entities
                        SET properties = properties || %s::jsonb
                        WHERE id = %s::uuid
                        """,
                        (
                            json.dumps(
                                {
                                    "current_lat": fix.lat,
                                    "current_lng": fix.lng,
                                    "current_sog_knots": fix.sog,
                                    "current_cog_deg": fix.cog,
                                    "current_heading_deg": int(round(fix.cog)),
                                    "current_pos_src": "myshiptracking",
                                    "current_source": "myshiptracking",
                                    "last_ais_at": fix.fetched_at.isoformat(),
                                }
                            ),
                            entity_id,
                        ),
                    )
                conn.commit()
                log.info(
                    "myshiptracking MMSI=%s lat=%.4f lng=%.4f sog=%.1f cog=%.1f",
                    mmsi, fix.lat, fix.lng, fix.sog, fix.cog,
                )
            except psycopg.Error:
                log.exception("myshiptracking DB write failed for MMSI %s", mmsi)
                errors += 1
    return {"inserted": inserted, "errors": errors}


# ---------------------------------------------------------------------------
# CruiseMapper public-page scraper task
#
# Polls every 5 min for each tracked vessel. Writes a vessel_track_point
# row with source='cruisemapper'. CruiseMapper aggregates terrestrial +
# satellite AIS and typically has fresher mid-ocean positions than
# MyShipTracking (empirically verified 2026-05-12: CM had 32.58°N when
# MST was stuck at a 7h-stale 29.34°N for a vessel doing 11.8 kn).
# ---------------------------------------------------------------------------


@shared_task(name="horizon_worker.tasks.ais.poll_cruisemapper")  # type: ignore[misc]
def poll_cruisemapper() -> dict[str, int]:
    """
    Hit the public CruiseMapper page for each tracked vessel and persist
    the position. Same dedup logic as poll_myshiptracking: skip the INSERT
    if the position hasn't moved more than ~10 m since the last stored fix,
    but always refresh the vessel entity's dynamic properties.
    """
    inserted = 0
    errors = 0
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        mmsi_to_id = _resolve_vessel_ids(conn)
        for mmsi in CM_TRACKED:
            entity_id = mmsi_to_id.get(mmsi)
            if entity_id is None:
                log.warning("cruisemapper: no vessel entity for MMSI %s", mmsi)
                continue
            try:
                fix = cm_fetch(mmsi)
            except Exception:
                log.exception("cruisemapper fetch failed for MMSI %s", mmsi)
                errors += 1
                continue
            if fix is None:
                continue
            try:
                with conn.cursor() as cur:
                    # Position-dedup: skip INSERT if same lat/lng (< ~10 m).
                    cur.execute(
                        """
                        SELECT ts, lat::float8 AS lat, lng::float8 AS lng
                        FROM vessel_track_points
                        WHERE vessel_entity_id = %s
                          AND source = 'cruisemapper'
                        ORDER BY ts DESC LIMIT 1
                        """,
                        (entity_id,),
                    )
                    last_row = cur.fetchone()
                    SAME_POS_TOL = 0.0001  # ~10 m
                    is_duplicate = bool(
                        last_row
                        and abs(last_row["lat"] - fix.lat) < SAME_POS_TOL
                        and abs(last_row["lng"] - fix.lon) < SAME_POS_TOL
                    )
                    if is_duplicate and last_row is not None:
                        last_ts = last_row["ts"]
                        if last_ts.tzinfo is None:
                            from datetime import timezone as _tz
                            last_ts = last_ts.replace(tzinfo=_tz.utc)
                        stale_h = (fix.fetched_at - last_ts).total_seconds() / 3600
                        if stale_h > 1.0 and fix.sog is not None and fix.sog > 1.0:
                            log.warning(
                                "cruisemapper MMSI=%s: position UNCHANGED for %.1fh "
                                "despite sog=%.1f kn — source may be serving stale data.",
                                mmsi, stale_h, fix.sog,
                            )
                    if not is_duplicate:
                        cur.execute(
                            """
                            INSERT INTO vessel_track_points (
                                vessel_entity_id, ts, lat, lng,
                                speed_knots, heading, source, src_citation
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                'cruisemapper',
                                'Scraped from cruisemapper.com public vessel page'
                            )
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                entity_id,
                                fix.fetched_at,
                                fix.lat,
                                fix.lon,
                                fix.sog,
                                int(round(fix.cog)) if fix.cog is not None else None,
                            ),
                        )
                        if cur.rowcount > 0:
                            inserted += 1

                    # Always refresh vessel entity dynamic state.
                    dynamic: dict = {
                        "current_lat": fix.lat,
                        "current_lng": fix.lon,
                        "current_pos_src": "cruisemapper",
                        "current_source": "cruisemapper",
                        "last_ais_at": fix.fetched_at.isoformat(),
                    }
                    if fix.sog is not None:
                        dynamic["current_sog_knots"] = fix.sog
                    if fix.cog is not None:
                        dynamic["current_cog_deg"] = fix.cog
                        dynamic["current_heading_deg"] = int(round(fix.cog))
                    cur.execute(
                        """
                        UPDATE entities
                        SET properties = properties || %s::jsonb
                        WHERE id = %s::uuid
                        """,
                        (json.dumps(dynamic), entity_id),
                    )
                conn.commit()
                log.info(
                    "cruisemapper MMSI=%s lat=%.4f lon=%.4f sog=%s cog=%s",
                    mmsi, fix.lat, fix.lon, fix.sog, fix.cog,
                )
            except psycopg.Error:
                log.exception("cruisemapper DB write failed for MMSI %s", mmsi)
                errors += 1
    return {"inserted": inserted, "errors": errors}
