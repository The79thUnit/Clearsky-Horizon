"""GDELT 2.0 DOC API connector. Global news monitoring across 65 languages.

Documented at https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/.
Returns JSON when format=json is set.

NATO C2 (fairly reliable, probably true). Aggregated news; individual
records need analyst confidence before they're elevated.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class GDELTConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "gdelt"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://api.gdeltproject.org/api/v2/doc/doc"
    # 14 May 2026: simplified the OR-quoted query to bare "hantavirus".
    # The previous form ('hantavirus OR "Andes virus" OR "Sin Nombre virus"')
    # was URL-encoded by httpx in a way GDELT's query parser couldn't handle,
    # and we were also being rate-limited by the explicit sort=DateDesc.
    # Default DOC API ordering + local KEYWORDS filter is fine.
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "mode": "ArtList",
        "format": "json",
        "maxrecords": "75",
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("articles",)
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "sin nombre",
        "puumala",
    ]

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("title", "")).strip()
        if not title:
            return None
        url = item.get("url", "")
        external_id = f"gdelt:{url}"

        # GDELT date format: 20260510T093000Z. We only need the date portion.
        date_str = str(item.get("seendate", ""))
        reported: date | None = parse_date_safe(date_str[:8], "%Y%m%d") if date_str else None

        # Use GDELT's sourcecountry hint when available, else heuristic
        source_country = item.get("sourcecountry", "")
        country_iso2 = (
            source_country[:2].upper() if source_country and len(source_country) >= 2 else None
        )
        if not country_iso2:
            country_iso2 = detect_country(title)

        serotype = detect_serotype(title, country_iso2=country_iso2)
        domain = item.get("domain", "")

        canonical = "\n".join([url, title, date_str]).encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=f"Source: {domain}" if domain else None,
            country_iso2=country_iso2,
            region=None,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=url,
            raw_content=canonical,
        )
