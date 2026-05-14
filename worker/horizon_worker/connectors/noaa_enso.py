"""NOAA ENSO MEI.v2 (Multivariate ENSO Index) connector.

NOAA's Physical Sciences Laboratory publishes the MEI.v2 -- the most widely
used composite measure of El Nino/La Nina strength. MEI.v2 values:
  > +0.5: El Nino conditions (wet, drives vegetation and rodent boom in Americas)
  > +1.5: Moderate El Nino
  > +2.0: Strong El Nino
  < -0.5: La Nina conditions
  -0.5 to +0.5: Neutral

Relevance to hantavirus surveillance:
  In Latin America (ANDV/SNV endemic regions), El Nino increases rainfall,
  vegetation (NDVI), rodent food supply, and Oligoryzomys/Peromyscus populations
  by 12-24 months later. This is the single strongest ecological predictor of
  HPS case increases in Chile and Argentina. NOAA ENSO MEI.v2 correlation with
  ANDV outbreaks has been documented in multiple epidemiological studies.

Data source: NOAA PSL tab-separated text file (monthly, updated ~3rd week
each month). No API key required.

NATO: A1 (completely reliable). provenance_type: ecological-indicator. Tier 3.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any, ClassVar

import httpx

from .base import BaseConnector, FetchResult
from .types import ParsedItem

logger = logging.getLogger(__name__)

_ENSO_URL = "https://psl.noaa.gov/enso/mei/data/meiv2.data"

# MEI threshold above which El Nino signal is meaningful for ANDV risk.
ENSO_ELNINO_THRESHOLD: float = 0.5
ENSO_STRONG_THRESHOLD: float = 1.5


class NOAAENSOConnector(BaseConnector):
    """Fetch NOAA MEI.v2 monthly ENSO index and store as ecological indicator records."""

    SOURCE_CODE: ClassVar[str] = "noaa-enso"
    PARSER_VERSION: ClassVar[str] = "0.1.0"

    async def run(self) -> FetchResult:
        start = datetime.now(tz=UTC)
        try:
            async with httpx.AsyncClient(
                timeout=30,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(_ENSO_URL)
                if response.status_code in {429, 502, 503, 504}:
                    return FetchResult(
                        source_code=self.SOURCE_CODE,
                        parser_version=self.PARSER_VERSION,
                        http_status=response.status_code,
                        latency_ms=int((datetime.now(tz=UTC) - start).total_seconds() * 1000),
                        items_seen=0,
                        items=[],
                        items_filtered=0,
                        error=None,
                    )
                response.raise_for_status()
                raw = response.content

            items = self._parse_meiv2(raw)
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=response.status_code,
                latency_ms=latency,
                items_seen=len(items),
                items=items,
                items_filtered=0,
                error=None,
            )
        except Exception as exc:
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            logger.exception("NOAA ENSO fetch failed")
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=None,
                latency_ms=latency,
                items_seen=0,
                items=[],
                items_filtered=0,
                error=str(exc),
            )

    def _parse_meiv2(self, raw: bytes) -> list[ParsedItem]:
        """Parse NOAA MEI.v2 fixed-format text into ParsedItems.

        File format (space/tab delimited):
          YEAR  Jan   Feb   Mar   Apr   May   Jun   Jul   Aug   Sep   Oct   Nov   Dec
          1979  0.07  0.12  ...
          ...
        Missing values are -999.00.

        We emit one ParsedItem per month, for the most recent 12 months only
        (older data is in the DB from previous fetches). Each item title is
        "ENSO MEI.v2: <month> <year> = <value>" and the ecological context
        is embedded in the summary for the text_utils detector.
        """
        lines = raw.decode("ascii", errors="replace").splitlines()
        items: list[ParsedItem] = []

        # Find the most recent non-empty data line (skip header and trailing lines)
        data_rows: list[tuple[int, list[float]]] = []
        for line in lines:
            parts = line.split()
            if len(parts) == 13:
                try:
                    year = int(parts[0])
                    values = [float(v) for v in parts[1:]]
                    if 1979 <= year <= 2100:
                        data_rows.append((year, values))
                except ValueError:
                    continue

        if not data_rows:
            return []

        # Only emit the most recent 12 months to avoid re-ingesting historical data.
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        recent: list[tuple[date, float]] = []
        for year, values in data_rows[-2:]:  # last 2 years covers recent 12 months
            for i, val in enumerate(values):
                if val != -999.0:
                    try:
                        d = date(year, i + 1, 1)
                        recent.append((d, val))
                    except ValueError:
                        continue

        # Keep only last 12 months
        recent.sort(key=lambda x: x[0])
        recent = recent[-12:]

        for d, mei in recent:
            month_name = months[d.month - 1]
            condition = (
                "strong El Nino" if mei > ENSO_STRONG_THRESHOLD
                else "El Nino" if mei > ENSO_ELNINO_THRESHOLD
                else "La Nina" if mei < -ENSO_ELNINO_THRESHOLD
                else "neutral"
            )
            title = f"ENSO MEI.v2 {month_name} {d.year}: {mei:+.2f} ({condition})"
            summary = (
                f"NOAA Multivariate ENSO Index v2 for {month_name} {d.year}: "
                f"MEI = {mei:.2f}. Condition: {condition}. "
                f"El Nino (MEI > 0.5) increases vegetation and rodent populations "
                f"in ANDV/SNV endemic regions of Latin America 12-24 months later, "
                f"elevating hantavirus HPS risk."
            )
            external_id = f"noaa-enso:{d.year}-{d.month:02d}"
            canonical = f"{external_id}\n{mei}".encode()

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    country_iso2=None,  # global index
                    region="Global",
                    lat=None,
                    lng=None,
                    serotype_text=None,
                    reported_date=d,
                    case_count=None,
                    death_count=None,
                    raw_url=_ENSO_URL,
                    raw_content=canonical,
                )
            )

        return items
