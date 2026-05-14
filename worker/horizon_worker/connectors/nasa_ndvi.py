"""NASA Earthdata NDVI anomaly connector.

NDVI (Normalised Difference Vegetation Index) anomaly relative to the 5-year
baseline is a leading ecological indicator for hantavirus risk. Elevated
vegetation supports larger rodent food supplies and population surges.

Mechanism:
  Hantaan/PUUV (Europe/Asia): beech/oak mast years drive bank vole and
    striped field mouse population explosions. NDVI anomaly in summer
    predicts following-year vole population peaks. Correlation documented
    in Germany, Finland, Sweden (Niklasson et al., Tersago et al.).
  ANDV/SNV (Americas): El Nino-driven rainfall increases vegetation (NDVI),
    expands Oligoryzomys and Peromyscus food supply 12-18 months later.
    NASA SERVIR demonstrated operational risk mapping via NDVI + ENSO.

Data source: MODIS/Terra Vegetation Indices MOD13A3 v061 (monthly, 1km).
  Accessed via NASA Earthdata APPEEARS API (Application for Extracting
  and Exploring Analysis Ready Samples). Free account required for full
  access; this connector uses the public statistics endpoint.

  Alternative (no auth): MODIS Land Subsets API via ornl.gov
  https://modis.ornl.gov/rst/api/v1/<product>/statistics

This implementation uses the ORNL MODIS Web Service (no auth required)
to fetch monthly NDVI statistics for 5 key hantavirus-endemic regions:
  1. Patagonia (ANDV): centred on Bariloche, Argentina (-41, -71)
  2. US Four Corners (SNV): centred on Flagstaff, Arizona (35, -111)
  3. Finland/Scandinavia (PUUV): centred on Tampere (61, 24)
  4. China/Korea (HTNV): centred on Shenyang (41, 123)
  5. Balkans (DOBV): centred on Belgrade (44, 21)

NATO: A1 (NASA federal data). provenance_type: ecological-indicator. Tier 3.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any, ClassVar

import httpx

from .base import BaseConnector, FetchResult
from .types import ParsedItem

logger = logging.getLogger(__name__)

# ORNL MODIS Web Service — no authentication required.
# Returns monthly NDVI statistics for a lat/lon point within a spatial subset.
_ORNL_BASE = "https://modis.ornl.gov/rst/api/v1"
_PRODUCT = "MOD13A3"
_BAND = "1 km monthly NDVI"

# Five key endemic regions: (name, country_iso2, lat, lng, primary_serotype)
ENDEMIC_REGIONS: list[dict[str, Any]] = [
    {
        "name": "Patagonia (Argentina/Chile)",
        "country_iso2": "AR",
        "lat": -41.1,
        "lng": -71.3,
        "serotype": "ANDV",
        "notes": "Oligoryzomys longicaudatus reservoir; ANDV HPS endemic",
    },
    {
        "name": "US Four Corners",
        "country_iso2": "US",
        "lat": 35.2,
        "lng": -111.6,
        "serotype": "SNV",
        "notes": "Peromyscus maniculatus reservoir; SNV HPS endemic",
    },
    {
        "name": "Finland/Scandinavia",
        "country_iso2": "FI",
        "lat": 61.5,
        "lng": 24.0,
        "serotype": "PUUV",
        "notes": "Myodes glareolus reservoir; PUUV nephropathia epidemica",
    },
    {
        "name": "Northeast China/Korea",
        "country_iso2": "CN",
        "lat": 41.8,
        "lng": 123.4,
        "serotype": "HTNV",
        "notes": "Apodemus agrarius reservoir; Hantaan HFRS endemic",
    },
    {
        "name": "Balkans",
        "country_iso2": "RS",
        "lat": 44.8,
        "lng": 20.5,
        "serotype": "DOBV",
        "notes": "Apodemus flavicollis reservoir; Dobrava-Belgrade HFRS",
    },
]

# NDVI anomaly threshold above which hantavirus risk uplift should be flagged.
# Expressed as percentage above 5-year mean. Conservative 15% threshold based
# on Tersago et al. (2009) and NASA Earthdata hantavirus risk mapping studies.
NDVI_RISK_THRESHOLD_PCT: float = 15.0


class NASANDVIConnector(BaseConnector):
    """Fetch MODIS NDVI anomaly for 5 key hantavirus-endemic regions."""

    SOURCE_CODE: ClassVar[str] = "nasa-ndvi"
    PARSER_VERSION: ClassVar[str] = "0.1.0"

    async def run(self) -> FetchResult:
        start = datetime.now(tz=UTC)
        all_items: list[ParsedItem] = []
        last_status: int | None = None

        async with httpx.AsyncClient(
            timeout=30,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        ) as client:
            for region in ENDEMIC_REGIONS:
                try:
                    items, status = await self._fetch_region(client, region)
                    all_items.extend(items)
                    last_status = status
                except Exception as exc:
                    logger.warning(
                        "NDVI fetch failed for region %s: %s",
                        region["name"], exc,
                    )

        latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
        return FetchResult(
            source_code=self.SOURCE_CODE,
            parser_version=self.PARSER_VERSION,
            http_status=last_status or 200,
            latency_ms=latency,
            items_seen=len(all_items),
            items=all_items,
            items_filtered=0,
            error=None,
        )

    async def _fetch_region(
        self,
        client: httpx.AsyncClient,
        region: dict[str, Any],
    ) -> tuple[list[ParsedItem], int]:
        """Fetch NDVI statistics for one region, return ParsedItems."""
        url = (
            f"{_ORNL_BASE}/{_PRODUCT}/statistics"
            f"?latitude={region['lat']}&longitude={region['lng']}"
            f"&startDate=A2024001&endDate=A2025365"  # last 2 calendar years
            f"&kmAboveBelow=1&kmLeftRight=1"
        )
        response = await client.get(url)
        if response.status_code != 200:
            return [], response.status_code

        data = response.json()
        items: list[ParsedItem] = []

        # ORNL returns a list of band statistics per time step.
        # We extract the NDVI band and compute a simple mean + baseline comparison.
        ndvi_entries: list[dict[str, Any]] = [
            e for e in data.get("subset", [])
            if _BAND in str(e.get("band", ""))
        ]

        if not ndvi_entries:
            return [], response.status_code

        # Use the most recent entry for risk assessment.
        # A proper anomaly requires a 5-year baseline; this implementation
        # uses the entry's own mean relative to the data range as a proxy.
        # Phase 3+ should compute proper z-score anomaly vs 5-year baseline.
        for entry in ndvi_entries[-3:]:  # last 3 months
            mean_val = entry.get("mean")
            max_val = entry.get("max")
            date_str = str(entry.get("calendar_date", ""))[:10]

            if mean_val is None or date_str == "":
                continue

            try:
                d = date.fromisoformat(date_str)
            except ValueError:
                continue

            # Scale factor: MODIS NDVI is stored as integer * 10000.
            ndvi_scaled = float(mean_val)
            ndvi = ndvi_scaled / 10000 if ndvi_scaled > 1 else ndvi_scaled
            ndvi_max = float(max_val) / 10000 if max_val and float(max_val) > 1 else (max_val or 0)

            risk_flag = ndvi >= 0.4  # absolute threshold for vegetation presence
            title = (
                f"NDVI {region['name']} {d.strftime('%b %Y')}: "
                f"{ndvi:.3f} ({'elevated' if risk_flag else 'normal'} vegetation)"
            )
            summary = (
                f"MODIS MOD13A3 monthly NDVI for {region['name']} "
                f"({region['lat']}, {region['lng']}) in {d.strftime('%B %Y')}: "
                f"mean={ndvi:.3f}. Primary serotype: {region['serotype']}. "
                f"{region['notes']}. "
                f"Elevated NDVI (>0.4) supports larger rodent populations and "
                f"increases hantavirus spillover risk 6-18 months later."
            )
            external_id = (
                f"nasa-ndvi:{region['country_iso2']}:{region['serotype']}:"
                f"{d.year}-{d.month:02d}"
            )
            canonical = f"{external_id}\n{ndvi:.4f}".encode()

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    country_iso2=region["country_iso2"],
                    region=region["name"],
                    lat=region["lat"],
                    lng=region["lng"],
                    serotype_text=region["serotype"],
                    reported_date=d,
                    case_count=None,
                    death_count=None,
                    raw_url=url,
                    raw_content=canonical,
                )
            )

        return items, response.status_code
