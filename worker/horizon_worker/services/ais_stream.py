"""
AISStream.io websocket daemon.

Subscribes to PositionReport messages for the MMSIs we care about
(currently MV Hondius / 244327000) and persists each fix to
vessel_track_points with source = 'aisstream'.

Run as its own long-lived container:

    docker compose -f docker-compose.prod.yml up -d ais

Behaviour:
  * If AISSTREAM_API_KEY is not set in the environment, the daemon logs a
    warning every 5 min and otherwise idles. This keeps the container
    healthy (no crash-restart loop) until Phoenix drops the key in.
  * On websocket disconnect (network blip, AISStream restart, etc.) it
    waits 30s and reconnects. The aisstream session itself is cheap.
  * Each PositionReport is inserted via ON CONFLICT DO NOTHING — duplicate
    fixes at the same timestamp + vessel are silently ignored.
  * Logs every accepted fix to stdout so `docker logs horizon-ais` shows
    a live feed.

Provider docs: https://aisstream.io/documentation
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.sync.client import connect as ws_connect

from ..config import settings

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WSS_URL = "wss://stream.aisstream.io/v0/stream"

# Vessels we want AIS positions for. MMSI must be a 9-digit string.
TRACKED_MMSIS: list[str] = [
    "244327000",  # MV Hondius (NL) — IMO 9818709, verified live 12 May 2026
]

# How long to back off after a websocket failure before reconnecting.
RECONNECT_BACKOFF_SECONDS = 30

# When AISSTREAM_API_KEY is unset, idle this long between warning logs so
# the container doesn't spam stdout.
NO_KEY_IDLE_SECONDS = 300

log = logging.getLogger("horizon.ais")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


@contextmanager
def db_conn() -> Iterator[psycopg.Connection]:
    """Open a short-lived psycopg connection. Same DSN as the worker."""
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def load_mmsi_to_entity_id() -> dict[str, str]:
    """
    Look up the vessel entity UUIDs from the DB so AIS messages can be
    persisted with the correct vessel_entity_id FK.
    """
    out: dict[str, str] = {}
    with db_conn() as conn, conn.cursor() as cur:
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
            if row:
                out[mmsi] = row["id"]
                log.info("tracking MMSI %s → entity %s", mmsi, row["id"])
            else:
                log.warning("no vessel entity found in DB for MMSI %s — skipping", mmsi)
    return out


def insert_track_point(
    vessel_entity_id: str,
    ts: datetime,
    lat: float,
    lng: float,
    sog: float | None,
    cog: float | None,
) -> None:
    """Insert one position fix. Duplicate (vessel_id, ts) is silently ignored."""
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vessel_track_points (
                vessel_entity_id, ts, lat, lng, speed_knots, heading, source, src_citation
            ) VALUES (%s, %s, %s, %s, %s, %s, 'aisstream',
                      '[PUBLIC] AISStream.io live position report (websocket AIS feed)')
            ON CONFLICT DO NOTHING
            """,
            (vessel_entity_id, ts, lat, lng, sog, cog),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Websocket loop
# ---------------------------------------------------------------------------


def stream_once(api_key: str, mmsi_to_entity_id: dict[str, str]) -> None:
    """
    One full lifecycle of an aisstream websocket session.
    Returns when the connection drops; the outer loop handles backoff.
    """
    subscribe_msg = {
        "APIKey": api_key,
        # Global bounding box — the Hondius could be anywhere on the route.
        "BoundingBoxes": [[[-90.0, -180.0], [90.0, 180.0]]],
        "FiltersShipMMSI": list(mmsi_to_entity_id.keys()),
        # Class A (1/2/3) + Class B (18/19) — large vessels use Class A but
        # subscribe to both so coastal-approach Class B fallback is caught too.
        "FilterMessageTypes": [
            "PositionReport",
            "StandardClassBPositionReport",
            "ExtendedClassBPositionReport",
        ],
    }

    with ws_connect(WSS_URL, max_size=2**20) as ws:
        ws.send(json.dumps(subscribe_msg))
        log.info(
            "subscribed to aisstream for %d vessel(s): %s",
            len(mmsi_to_entity_id),
            ", ".join(mmsi_to_entity_id.keys()),
        )

        for raw in ws:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError as exc:
                log.warning("non-JSON frame from aisstream: %s", exc)
                continue

            msg_type = msg.get("MessageType") or ""
            # Accept Class A (PositionReport) and Class B (Standard/Extended).
            if msg_type not in (
                "PositionReport",
                "StandardClassBPositionReport",
                "ExtendedClassBPositionReport",
            ):
                continue

            metadata = msg.get("MetaData") or {}
            mmsi = str(metadata.get("MMSI") or "")
            entity_id = mmsi_to_entity_id.get(mmsi)
            if entity_id is None:
                continue  # not one we're tracking

            # Field names differ slightly across message types.
            inner = (msg.get("Message") or {})
            pr = (
                inner.get("PositionReport")
                or inner.get("StandardClassBPositionReport")
                or inner.get("ExtendedClassBPositionReport")
                or {}
            )
            lat = pr.get("Latitude")
            lng = pr.get("Longitude")
            if lat is None or lng is None:
                continue

            ts_iso = metadata.get("time_utc")
            if ts_iso:
                # AISStream gives e.g. "2026-05-12 11:04:36.123456789 +0000 UTC"
                # Strip nanoseconds and timezone descriptor to get an
                # ISO-parseable string.
                ts_iso_clean = ts_iso.split(" +")[0].split(".")[0]
                try:
                    ts = datetime.fromisoformat(ts_iso_clean).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            sog = pr.get("Sog")  # speed over ground (knots)
            cog = pr.get("Cog")  # course over ground (deg)

            try:
                insert_track_point(entity_id, ts, float(lat), float(lng), sog, cog)
                log.info(
                    "MMSI %s @ %s  lat=%.4f lng=%.4f  sog=%s cog=%s",
                    mmsi,
                    ts.isoformat(),
                    lat,
                    lng,
                    sog,
                    cog,
                )
            except psycopg.Error as exc:
                log.exception("DB insert failed: %s", exc)


def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    api_key = os.environ.get("AISSTREAM_API_KEY", "").strip()
    if not api_key:
        # Idle gracefully — don't crash-loop. Phoenix can add the key later
        # and restart the container.
        log.warning(
            "AISSTREAM_API_KEY is not set. "
            "Register at https://aisstream.io/ to get a free key, then "
            "add AISSTREAM_API_KEY=<key> to .env.production and "
            "`docker compose restart ais`. Idling."
        )
        while True:
            time.sleep(NO_KEY_IDLE_SECONDS)
            log.info("still idle — AISSTREAM_API_KEY unset")

    # Resolve tracked MMSIs → entity UUIDs once at startup. If a tracked
    # vessel isn't in the DB yet, it's skipped (re-resolved on each
    # reconnect, so adding it later auto-picks up).
    while True:
        try:
            mmsi_to_entity_id = load_mmsi_to_entity_id()
            if not mmsi_to_entity_id:
                log.warning(
                    "no tracked MMSIs match a DB entity. Sleeping %ds before retry.",
                    RECONNECT_BACKOFF_SECONDS,
                )
                time.sleep(RECONNECT_BACKOFF_SECONDS)
                continue

            stream_once(api_key, mmsi_to_entity_id)
            log.warning("aisstream connection closed cleanly; reconnecting")
        except (ConnectionClosed, WebSocketException) as exc:
            log.warning("aisstream websocket error: %s", exc)
        except psycopg.Error as exc:
            log.exception("DB error in stream loop: %s", exc)
        except Exception as exc:  # noqa: BLE001 — daemon should never die
            log.exception("unexpected error: %s", exc)
        time.sleep(RECONNECT_BACKOFF_SECONDS)


if __name__ == "__main__":
    main()
