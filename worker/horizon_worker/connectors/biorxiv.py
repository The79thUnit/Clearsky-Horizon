"""bioRxiv JSON API connector (preprints, biology).

Documented at https://api.biorxiv.org. We query the recent posts feed
and filter for hantavirus keywords.

NATO B2 (usually reliable, probably true). Preprints precede peer review.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

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
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # Fetch the most recent 30 days of posts; we filter locally.
    ENDPOINT: ClassVar[str] = "https://api.biorxiv.org/details/biorxiv/30d/0/json"
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
