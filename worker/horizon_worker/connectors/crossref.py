"""Crossref Works API connector. DOI registry, returns peer-reviewed records.

Documented at https://api.crossref.org.

NATO B1 (usually reliable, confirmed by other sources). Metadata only,
no abstracts unless the publisher deposits them.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype
from .types import ParsedItem


class CrossrefConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "crossref"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    ENDPOINT: ClassVar[str] = "https://api.crossref.org/works"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "rows": "30",
        "sort": "published",
        "order": "desc",
        "filter": "type:journal-article",
        "select": "DOI,title,abstract,issued,container-title,author",
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("message", "items")
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "andes virus",
        "sin nombre",
        "puumala",
        "hantaan",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # Crossref encourages a polite user-agent with mailto.
        "user-agent": "HORIZON/0.1 (mailto:research@79thunit.co.uk)",
    }

    @staticmethod
    def _strip_jats(text: str) -> str:
        import re

        return re.sub(r"<[^>]+>", "", text).strip()

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        titles = item.get("title") or []
        title = (titles[0] if titles else "").strip()
        if not title:
            return None
        doi = item.get("DOI", "")
        abstract_raw = item.get("abstract", "")
        abstract = self._strip_jats(abstract_raw) if abstract_raw else ""

        link = f"https://doi.org/{doi}" if doi else ""
        external_id = f"crossref:{doi}" if doi else f"crossref:{title[:80]}"

        reported: date | None = None
        issued = item.get("issued", {}).get("date-parts", [[]])[0]
        if issued and len(issued) >= 1:
            try:
                y = int(issued[0])
                m = int(issued[1]) if len(issued) > 1 else 1
                d = int(issued[2]) if len(issued) > 2 else 1
                reported = date(y, m, d)
            except (TypeError, ValueError):
                reported = None

        haystack = f"{title} {abstract}"
        country = detect_country(haystack)
        serotype = detect_serotype(haystack)

        canonical = "\n".join([str(doi), title]).encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=abstract[:600] if abstract else None,
            country_iso2=country,
            region=None,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=link,
            raw_content=canonical,
        )
