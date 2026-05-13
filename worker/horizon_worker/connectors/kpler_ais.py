"""
Kpler Maritime AIS connector.

Pulls vessel positions from https://api.kpler.com/v2/maritime — Kpler
acquired MarineTraffic and exposes their global terrestrial + roaming +
satellite AIS network through this single API.

Auth: HTTP Basic with a base64-encoded `client_id:secret` key supplied via
      KPLER_API_KEY env var. Send as `Authorization: Basic <KPLER_API_KEY>`.
Rate limit: 300 req/min per endpoint (well above what we need).

Two endpoints used:

  /ais-latest        — one latest position per vessel matching an ECQL filter.
                       Used every 2 min by the Celery beat schedule.

  /ais-historical    — multiple positions per vessel over a time window
                       (max 366 days per request, up to 10 vessels). Used
                       for one-shot backfill of the MV Hondius polar voyage
                       from 1 April 2026 onwards.

Both endpoints return GeoJSON FeatureCollection. Each Feature carries:

  geometry.coordinates = [lon, lat]
  properties = {
    mmsi, imo, vesselName, vesselType, flag,
    sog (knots), cog (deg), heading, rot, navStatus,
    destination, eta,
    posDt (when AIS msg emitted, ISO 8601),
    posSrcText (TER | ROAM | SAT),
    ...
  }

We persist each position as a row in `vessel_track_points` with source =
'marinetraffic' (the schema CHECK constraint already accepts that value).
The vessel-level dynamic fields (destination, eta, current sog/cog, last
AIS at) are upserted onto the vessel entity's `properties` JSONB so the UI
can display them on the current-position popup.

The Kpler trial tier limits historical data to the most recent 30 days.
The MV Hondius voyage started 1 April 2026; depending on the plan
attached to this API key, the back-fill may stop at ~30 days ago. The
connector logs which window it actually got.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

KPLER_BASE_URL = "https://api.kpler.com/v2/maritime"


# ---------------------------------------------------------------------------
# Auth — HTTP Basic, per Kpler's official tutorial:
#
#   https://developers.kpler.com/api/tutorials/AIS
#
#   r = requests.get(API_URL,
#       headers={"Authorization": f"Basic {API_KEY}"}, ...)
#
# The KPLER_API_KEY env var is the value supplied in the developer portal,
# already encoded for use directly as the value after "Basic ". No token
# exchange is required — the portal-supplied key IS the credential.
#
# IMPORTANT: the API will return HTTP 401 even with a valid key if your
# account does not have an active subscription to the Maritime AIS product.
# The Kong gateway counts the request against your rate-limit quota
# (visible in x-ratelimit-* headers) but the resource server itself
# rejects the call. The fix is a portal-side entitlement: subscribe your
# API key to the "Maritime AIS" product. We surface this in the error
# message so it's actionable.
# ---------------------------------------------------------------------------


def _auth_headers() -> dict[str, str]:
    key = os.environ.get("KPLER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "KPLER_API_KEY is not set. Get a key from "
            "https://developers.kpler.com/ and put it in .env.production."
        )
    return {
        "Authorization": f"Basic {key}",
        "Accept": "application/json",
        "User-Agent": os.environ.get(
            "HORIZON_USER_AGENT", "HORIZON/0.1 (+79th Unit OSINT)"
        ),
    }


def _raise_for_status_with_hint(resp: httpx.Response) -> None:
    """
    Replacement for resp.raise_for_status() that records Kpler's 401 with
    enough context to debug but without inventing actions.

    Earlier versions of this function suggested a self-service portal
    subscription to "Maritime AIS" at developers.kpler.com. That advice
    was wrong — no such self-service subscription is actually available
    on the account that owns this key (confirmed by the operator
    2026-05-13). The 401 is real and the cause is unknown from our side.

    The Kpler beat schedule entry `ais-poll-latest` is disabled, so this
    function should never fire in production. It's kept in place so any
    manual one-shot call to `fetch_latest()` or `fetch_historical()`
    still reports a useful error if Kpler ever does become reachable.
    """
    if resp.status_code == 401:
        rl_remaining = resp.headers.get("ratelimit-remaining") or resp.headers.get(
            "x-ratelimit-remaining-minute"
        )
        raise RuntimeError(
            f"Kpler returned HTTP 401 Unauthorized. "
            f"Gateway rate-limit-remaining header={rl_remaining!r}. "
            f"Account has no working access path. "
            f"Body: {resp.text[:200]}"
        )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Position record
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PositionFix:
    """
    One AIS position fix decoded from a Kpler GeoJSON Feature.

    All vessel-dynamic fields (destination, eta, navStatus) live on this
    object so the caller can decide whether to write them to
    vessel_track_points (per-fix) or to the vessel entity's properties
    (latest-state). We do both.
    """

    mmsi: str
    imo: str | None
    vessel_name: str | None
    vessel_type: str | None
    flag: str | None
    lat: float
    lon: float
    sog: float | None
    cog: float | None
    heading: int | None
    rot: int | None
    nav_status: int | None
    destination: str | None
    eta: datetime | None
    pos_dt: datetime
    pos_src: str | None  # TER / ROAM / SAT


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Kpler returns ISO 8601 with trailing Z.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _feature_to_fix(feature: dict[str, Any]) -> PositionFix | None:
    """Decode one GeoJSON Feature into a PositionFix, or None if invalid."""
    props = feature.get("properties") or {}
    geom = feature.get("geometry") or {}
    coords = geom.get("coordinates") or []

    if not coords or len(coords) < 2:
        return None
    if props.get("mmsi") is None:
        return None

    lon, lat = float(coords[0]), float(coords[1])
    pos_dt = _parse_dt(props.get("posDt"))
    if pos_dt is None:
        # Without a timestamp we can't dedupe or order; skip.
        return None
    if pos_dt.tzinfo is None:
        pos_dt = pos_dt.replace(tzinfo=timezone.utc)

    return PositionFix(
        mmsi=str(props["mmsi"]),
        imo=str(props["imo"]) if props.get("imo") is not None else None,
        vessel_name=props.get("vesselName"),
        vessel_type=props.get("vesselType"),
        flag=props.get("flag"),
        lat=lat,
        lon=lon,
        sog=props.get("sog"),
        cog=props.get("cog"),
        heading=props.get("heading"),
        rot=props.get("rot"),
        nav_status=props.get("navStatus"),
        destination=props.get("destination"),
        eta=_parse_dt(props.get("eta")),
        pos_dt=pos_dt,
        pos_src=props.get("posSrcText"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def fetch_latest(mmsi_list: list[str], timeout_s: float = 15.0) -> list[PositionFix]:
    """
    Hit /ais-latest for one or more MMSIs. Returns at most one PositionFix
    per vessel (the latest seen in the past 7 days).

    Build an ECQL filter like: mmsi IN (244327000, 123456789)
    """
    if not mmsi_list:
        return []
    if len(mmsi_list) == 1:
        flt = f"mmsi = {mmsi_list[0]}"
    else:
        flt = "mmsi IN (" + ",".join(mmsi_list) + ")"

    params = {"filter": flt, "format": "json"}
    resp = httpx.get(
        f"{KPLER_BASE_URL}/ais-latest",
        params=params,
        headers=_auth_headers(),
        timeout=timeout_s,
    )
    _raise_for_status_with_hint(resp)
    data = resp.json()
    features = data.get("features") or []
    out: list[PositionFix] = []
    for f in features:
        fix = _feature_to_fix(f)
        if fix is not None:
            out.append(fix)
    return out


def fetch_historical(
    mmsi: str,
    start: datetime,
    end: datetime,
    downsample: str = "dynamic",
    timeout_s: float = 60.0,
) -> list[PositionFix]:
    """
    Hit /ais-historical for one vessel between [start, end].

    Kpler requires `posDt BETWEEN ... AND ...` plus an MMSI/vesselUid clause
    in the ECQL filter. `downsample=dynamic` keeps a position every 10 min
    + every sharp turn or speed change — that's what we want for plotting
    a clean route line on the map.

    Trial accounts cap to the most recent 30 days. The API will reject the
    request if start is earlier than that; we don't try to detect that
    upfront, we just let the request fail and let the caller decide.
    """
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    start_iso = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    flt = (
        f"posDt BETWEEN '{start_iso}' AND '{end_iso}' "
        f"AND mmsi = {mmsi}"
    )

    params = {
        "filter": flt,
        "format": "json",
        "downsample": downsample,
        "sortBy": "posDt ASC",
    }
    resp = httpx.get(
        f"{KPLER_BASE_URL}/ais-historical",
        params=params,
        headers=_auth_headers(),
        timeout=timeout_s,
    )
    _raise_for_status_with_hint(resp)
    data = resp.json()
    features = data.get("features") or []
    out: list[PositionFix] = []
    for f in features:
        fix = _feature_to_fix(f)
        if fix is not None:
            out.append(fix)
    return out
