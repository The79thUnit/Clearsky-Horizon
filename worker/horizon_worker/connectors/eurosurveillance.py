"""Eurosurveillance — ECDC peer-reviewed weekly journal.

14 May 2026 rewrite: direct scraping of `eurosurveillance.org` is blocked
by their Cloudflare WAF (403 even with Chrome 120 impersonation). We now
pull the same article set via the Crossref REST API, ISSN-filtered to
1560-7917 (Eurosurveillance's electronic ISSN).

NATO A1 — official ECDC publication, peer-reviewed.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


def _date_parts_to_date(dp: Any) -> date | None:
    """Crossref returns date as nested ``[[YYYY, MM, DD]]`` or ``[[YYYY, MM]]``."""
    if not dp:
        return None
    try:
        inner = dp[0] if isinstance(dp, list) else None
        if not inner:
            return None
        if len(inner) >= 3:
            return parse_date_safe(
                f"{int(inner[0]):04d}-{int(inner[1]):02d}-{int(inner[2]):02d}",
                "%Y-%m-%d",
            )
        if len(inner) == 2:
            return parse_date_safe(
                f"{int(inner[0]):04d}-{int(inner[1]):02d}-01",
                "%Y-%m-%d",
            )
        if len(inner) == 1:
            return parse_date_safe(f"{int(inner[0]):04d}-01-01", "%Y-%m-%d")
    except (TypeError, ValueError, IndexError):
        return None
    return None


class EurosurveillanceConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "eurosurveillance"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    # ISSN 1560-7917 = Eurosurveillance (electronic). Crossref's
    # `/journals/<issn>/works` restricts results to that one journal;
    # &query= adds full-text matching across title + abstract.
    ENDPOINT: ClassVar[str] = "https://api.crossref.org/journals/1560-7917/works"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "rows": "50",
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("message", "items")
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "dobrava",
        "orthohantavirus",
        "nephropathia epidemica",
    ]

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title_arr = item.get("title") or []
        title = (title_arr[0] if title_arr else "").strip()
        if not title:
            return None

        doi = item.get("DOI", "")
        link = f"https://doi.org/{doi}" if doi else ""
        external_id = f"eurosurveillance:{doi}" if doi else f"eurosurveillance:{title[:80]}"

        reported = (
            _date_parts_to_date(item.get("published-print", {}).get("date-parts"))
            or _date_parts_to_date(item.get("published-online", {}).get("date-parts"))
            or _date_parts_to_date(item.get("issued", {}).get("date-parts"))
        )

        abstract = (item.get("abstract") or "").strip()
        if abstract:
            # Crossref inlines JATS tags (<jats:p>...). Strip them.
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        haystack = f"{title} {abstract}"
        country = detect_country(haystack)
        serotype = detect_serotype(haystack, country_iso2=country)

        canonical = f"{external_id}\n{title}\n{doi}".encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title[:300],
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
