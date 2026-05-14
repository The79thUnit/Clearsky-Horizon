"""bioRxiv JSON API connector (preprints, biology).

Documented at https://api.biorxiv.org. We query the recent posts feed
and filter for hantavirus keywords.

NATO B2 (usually reliable, probably true). Preprints precede peer review.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, ClassVar

import httpx

from .json_api_base import JSONAPIConnectorBase
from .text_utils import (
    detect_country,
    detect_serotype,
    extract_region,
    parse_date_safe,
)
from .types import ParsedItem


class BioRxivConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "biorxiv"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    # 14 May 2026: bioRxiv API no longer accepts the "30d" relative-date
    # shorthand. fetch_raw computes a yyyy-mm-dd window dynamically.
    # ENDPOINT must be empty so BaseConnector._run_via_curl_cffi short-circuits
    # to None and the httpx path (which calls our fetch_raw) runs. Otherwise
    # curl_cffi GETs the base URL, gets "collection":[], and returns 0 items
    # before fetch_raw ever runs.
    ENDPOINT: ClassVar[str] = ""
    BASE_ENDPOINT: ClassVar[str] = "https://api.biorxiv.org/details/biorxiv/"
    SERVER: ClassVar[str] = "biorxiv"
    LOOKBACK_DAYS: ClassVar[int] = 30
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("collection",)
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "hantaan",
    ]

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        today = date.today()
        start = today - timedelta(days=self.LOOKBACK_DAYS)
        url = (
            f"https://api.biorxiv.org/details/{self.SERVER}/"
            f"{start.isoformat()}/{today.isoformat()}/0/json"
        )
        response = await client.get(url, headers={"accept": "application/json"})
        if response.status_code in self._TRANSIENT_STATUSES:
            return b"", response.status_code
        response.raise_for_status()
        return response.content, response.status_code

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("title", "")).strip()
        abstract = str(item.get("abstract", ""))
        doi = item.get("doi")
        link = f"https://www.biorxiv.org/content/{doi}v1" if doi else ""
        external_id = f"biorxiv:{doi}" if doi else f"biorxiv:{title[:80]}"

        date_str = item.get("date") or ""
        reported: date | None = parse_date_safe(date_str, "%Y-%m-%d")

        haystack = f"{title} {abstract}"
        country = detect_country(haystack)
        region = extract_region(title)
        serotype = detect_serotype(haystack)

        canonical = "\n".join([str(doi or ""), title, date_str]).encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=abstract[:600] if abstract else None,
            country_iso2=country,
            region=region,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=link,
            raw_content=canonical,
        )
