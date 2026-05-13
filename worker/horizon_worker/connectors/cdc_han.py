"""CDC Health Alert Network (HAN) connector.

CDC retired the static HTML HAN listing in 2024-25; the public landing
page at https://www.cdc.gov/han/php/notices/index.html now renders an
empty shell and pulls the actual HAN archive via XHR from a static
JSON endpoint. The HTMLScraperBase version of this connector (0.1.x)
returned 0 items forever after that switch because the index HTML no
longer contains direct <a href="/han/php/notices/hanNNNNN.html"> links.

This rewrite (0.2.0, verified 2026-05-13) targets the canonical archive
JSON directly:

  https://www.cdc.gov/han/php/modules/han-archive.static.json

The endpoint returns:
  {
    "responseHeader": { ... },
    "response": {
      "numFound": 38,
      "docs": [
        {
          "id": "1984_480",
          "title_txt": "Ongoing Risk of Dengue Virus Infections...",
          "permalink": "https://www.cdc.gov/han/php/notices/han00523.html",
          "cdc_article_date_dt": "2025-03-26T18:06:22Z",
          ...
        },
        ...
      ]
    }
  }

NATO A1. CDC HAN is the canonical US public-health alert channel.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class CDCHANConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cdc-han"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://www.cdc.gov/han/php/modules/han-archive.static.json"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {}
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("response", "docs")
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "orthohantavirus",
    ]

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("title_txt") or item.get("title") or "").strip()
        if not title:
            return None

        url = str(item.get("permalink") or item.get("url") or "").strip()
        if not url:
            return None

        # CDC stores dates as ISO-8601 with timezone, e.g.
        # "2025-03-26T18:06:22Z". Take the date portion.
        date_raw = item.get("cdc_article_date_dt") or item.get("cdc_last_reviewed_date") or ""
        reported: date | None = None
        if date_raw:
            reported = parse_date_safe(str(date_raw)[:10], "%Y-%m-%d")

        # HAN bulletins are US-authored by default; detect_country may
        # surface a more specific country if the title mentions one.
        country = detect_country(title) or "US"
        serotype = detect_serotype(title)

        # The CDC HAN ID (e.g. "1984_480") is stable; use it as the
        # external_id so re-fetches dedup correctly.
        cdc_id = item.get("id") or url
        canonical = f"{url}\n{title}\n{date_raw}".encode()

        return ParsedItem(
            external_id=f"cdc-han:{cdc_id}",
            title=title,
            summary=None,
            country_iso2=country,
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
