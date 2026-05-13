"""
MyShipTracking public-page scraper.

myshiptracking.com displays every vessel's latest AIS-reported position
on a public HTML page at:

    https://www.myshiptracking.com/vessels/<slug>-mmsi-<mmsi>-imo-<imo>

The page embeds the live data in a single JavaScript function call,
right in the HTML:

    canvas_map_generate("map_locator", 4, LAT, LNG, COG, SOG, "...");

We parse that with a regex, no JS execution required, no API key,
no rate-limit headers (yet). Good public-data hygiene: one polite
request every 5 minutes per vessel + a real browser User-Agent.

This is a complement to the aisstream.io websocket (which has gappy
mid-ocean coverage) — MyShipTracking aggregates the global AIS network
and almost always has a recent position for vessels currently tracked
by MarineTraffic / their feed partners.

Empirically verified live on 2026-05-12 for MV Hondius MMSI 244327000:
returned 29.34485°N, -15.43688°W, course 16.4°, speed 11.8kn — a
plausible position for a ship 2 days out of Tenerife heading NNE.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

log = logging.getLogger("horizon.myshiptracking")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "(+https://hantavirus.software; 79th Unit OSINT)"
)

# Page URL pattern. The slug after /vessels/ doesn't affect the response
# (myshiptracking accepts any slug as long as the MMSI matches), so we
# use a generic placeholder.
_URL_FMT = (
    "https://www.myshiptracking.com/vessels/x-mmsi-{mmsi}-imo-{imo}"
)

# Regex for the canvas_map_generate() call. Tolerates whitespace and
# optional + signs. Captures lat, lng, cog, sog.
_CMG_RE = re.compile(
    r"""canvas_map_generate\s*\(
        \s*"[^"]*"\s*,                   # element id
        \s*\d+\s*,                       # zoom level
        \s*(?P<lat>-?\d+\.\d+)\s*,       # latitude
        \s*(?P<lng>-?\d+\.\d+)\s*,       # longitude
        \s*(?P<cog>-?\d+(?:\.\d+)?)\s*,  # course over ground (deg)
        \s*(?P<sog>-?\d+(?:\.\d+)?)      # speed over ground (knots)
    """,
    re.VERBOSE,
)


@dataclass(frozen=True, slots=True)
class MstFix:
    """One position fix scraped from a MyShipTracking vessel page."""

    mmsi: str
    imo: str
    lat: float
    lng: float
    cog: float
    sog: float
    fetched_at: datetime  # we don't have the AIS receive time; using fetch ts


def fetch_position(mmsi: str, imo: str, timeout_s: float = 20.0) -> MstFix | None:
    """
    Fetch the public MyShipTracking page for a vessel and parse the
    canvas_map_generate() call. Returns None if not found (vessel page
    missing, position blank, page structure changed).
    """
    url = _URL_FMT.format(mmsi=mmsi, imo=imo)
    headers = {
        "User-Agent": os.environ.get("HORIZON_USER_AGENT", _USER_AGENT),
        "Accept": "text/html",
        "Accept-Language": "en-GB,en;q=0.9",
    }
    resp = httpx.get(url, headers=headers, timeout=timeout_s, follow_redirects=True)
    if resp.status_code != 200:
        log.warning("myshiptracking %s: HTTP %s", mmsi, resp.status_code)
        return None
    body = resp.text
    m = _CMG_RE.search(body)
    if not m:
        log.warning(
            "myshiptracking %s: canvas_map_generate not in page body "
            "(page structure may have changed, or no recent position)",
            mmsi,
        )
        return None
    try:
        lat = float(m.group("lat"))
        lng = float(m.group("lng"))
        cog = float(m.group("cog"))
        sog = float(m.group("sog"))
    except (ValueError, TypeError) as exc:
        log.warning("myshiptracking %s: parse error %s", mmsi, exc)
        return None
    # Plausibility check — reject clearly bogus values that some pages
    # show as placeholders when no recent position is available.
    if abs(lat) < 0.0001 and abs(lng) < 0.0001:
        log.info("myshiptracking %s: 0,0 placeholder, treating as no fix", mmsi)
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        log.warning("myshiptracking %s: out-of-range lat/lng %s,%s", mmsi, lat, lng)
        return None
    return MstFix(
        mmsi=mmsi,
        imo=imo,
        lat=lat,
        lng=lng,
        cog=cog,
        sog=sog,
        fetched_at=datetime.now(timezone.utc),
    )
