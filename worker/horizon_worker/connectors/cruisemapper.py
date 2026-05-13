"""
CruiseMapper public-page scraper.

cruisemapper.com embeds a vessel's live AIS position directly in the
HTML as a JSON object on every vessel page:

    {"lat":32.58179,"lon":-14.33316,"imo":"9818709","mmsi":"244327000","zoomDistance":"188244"}

This JSON is injected by their map JS and reliably appears in the raw
page source with no JS execution required. It reflects the most recent
AIS fix in their database (typically terrestrial + satellite blended).

Empirically verified live on 2026-05-12 for MV Hondius MMSI 244327000:
returned 32.58°N, 14.33°W — considerably further north than the stale
MyShipTracking fix (~29.3°N) at the same time, confirming CruiseMapper
has a fresher (likely satellite AIS) update.

URL pattern: https://www.cruisemapper.com/?mmsi={mmsi}
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

log = logging.getLogger("horizon.cruisemapper")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "(+https://hantavirus.software; 79th Unit OSINT)"
)

_URL_FMT = "https://www.cruisemapper.com/?mmsi={mmsi}"

# Primary: the JSON blob embedded for the map widget.
# Tolerates key-ordering variation and extra fields.
_POS_RE = re.compile(
    r'"lat"\s*:\s*(?P<lat>-?\d+\.\d+)'
    r'(?:[^}]{0,200}?)'
    r'"lon"\s*:\s*(?P<lon>-?\d+\.\d+)',
    re.DOTALL,
)

# SOG: look for "speed":11 or "sog":11 patterns in the surrounding JS.
_SOG_RE = re.compile(
    r'"(?:speed|sog|Speed|SOG)"\s*:\s*(?P<sog>\d+(?:\.\d+)?)',
)

# COG: look for "course":16 or "cog":16 etc.
_COG_RE = re.compile(
    r'"(?:course|cog|heading|Course|COG|Heading)"\s*:\s*(?P<cog>\d+(?:\.\d+)?)',
)


@dataclass(frozen=True, slots=True)
class CmFix:
    """One position fix scraped from a CruiseMapper vessel page."""

    mmsi: str
    lat: float
    lon: float
    sog: float | None    # knots, or None if not found in page
    cog: float | None    # degrees, or None if not found in page
    fetched_at: datetime  # wall-clock fetch time (AIS timestamp not in page)


def fetch_position(mmsi: str, timeout_s: float = 20.0) -> CmFix | None:
    """
    Fetch the CruiseMapper page for one MMSI and parse the embedded
    position JSON. Returns None if the page is missing, rate-limited,
    or the JSON is not found.
    """
    url = _URL_FMT.format(mmsi=mmsi)
    headers = {
        "User-Agent": os.environ.get("HORIZON_USER_AGENT", _USER_AGENT),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    try:
        resp = httpx.get(
            url, headers=headers, timeout=timeout_s, follow_redirects=True
        )
    except httpx.RequestError as exc:
        log.warning("cruisemapper %s: request error %s", mmsi, exc)
        return None

    if resp.status_code != 200:
        log.warning("cruisemapper %s: HTTP %s", mmsi, resp.status_code)
        return None

    body = resp.text

    m = _POS_RE.search(body)
    if not m:
        log.warning(
            "cruisemapper %s: position JSON not found in page "
            "(structure may have changed or no recent position)",
            mmsi,
        )
        return None

    try:
        lat = float(m.group("lat"))
        lon = float(m.group("lon"))
    except (ValueError, TypeError) as exc:
        log.warning("cruisemapper %s: coordinate parse error %s", mmsi, exc)
        return None

    # Plausibility checks.
    if abs(lat) < 0.0001 and abs(lon) < 0.0001:
        log.info("cruisemapper %s: 0,0 placeholder — treating as no fix", mmsi)
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        log.warning(
            "cruisemapper %s: out-of-range coordinates %.4f, %.4f",
            mmsi, lat, lon,
        )
        return None

    # SOG / COG are optional — CruiseMapper doesn't always expose them in
    # the page source, but check nearby JS variables anyway.
    sog: float | None = None
    cog: float | None = None

    sm = _SOG_RE.search(body)
    if sm:
        try:
            sog = float(sm.group("sog"))
        except (ValueError, TypeError):
            pass

    cm = _COG_RE.search(body)
    if cm:
        try:
            cog_val = float(cm.group("cog"))
            # COG must be 0-360; reject obviously wrong values
            if 0.0 <= cog_val <= 360.0:
                cog = cog_val
        except (ValueError, TypeError):
            pass

    return CmFix(
        mmsi=mmsi,
        lat=lat,
        lon=lon,
        sog=sog,
        cog=cog,
        fetched_at=datetime.now(timezone.utc),
    )
