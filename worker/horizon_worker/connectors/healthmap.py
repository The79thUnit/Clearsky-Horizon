"""HealthMap JSON connector. NATO B2.

HealthMap (Boston Children's Hospital) aggregates news + ProMED + WHO. They
expose JSON endpoints via healthmap.org/alerts/. We query for hantavirus.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class HealthMapConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "healthmap"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # HealthMap's public alerts API (best-effort; falls back to RSS-style HTML
    # if JSON is not served). Phase 3 may switch to the documented JSON feed
    # at /HMapi.php which requires an API key.
    ENDPOINT: ClassVar[str] = "https://www.healthmap.org/getAlerts.php"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "diseases": "hantavirus",
        "format": "json",
    }
    KEYWORDS: ClassVar[list[str]] = ["hantavirus", "hanta", "andes", "sin nombre", "puumala"]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "HORIZON/0.1 (+https://79thunit.co.uk)",
    }

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("summary") or item.get("disease") or "").strip()
        if not title:
            return None
        link = item.get("link") or item.get("source_url") or ""
        external_id = f"healthmap:{item.get('alert_id') or link or title[:80]}"

        date_str = str(item.get("date", ""))
        reported: date | None = parse_date_safe(
            date_str[:10], "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"
        )

        country = item.get("country") or detect_country(title)
        if isinstance(country, str) and len(country) > 2:
            country = detect_country(country)
        serotype = detect_serotype(title)

        canonical = f"{link}\n{title}\n{date_str}".encode()

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=None,
            country_iso2=country,
            region=None,
            lat=item.get("lat"),
            lng=item.get("lng"),
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=link,
            raw_content=canonical,
        )
