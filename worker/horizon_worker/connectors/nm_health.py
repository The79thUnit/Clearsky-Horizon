"""New Mexico Department of Health HPS scraper. NATO A2.

Phase 1 endemic-zone source: NM is Four Corners region. Page lists per-county
case counts. We surface page-level updates as events (count totals); per-case
records would require parsing the JSON table behind the visualisation, deferred
to Phase 3.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from bs4 import BeautifulSoup

from .html_scraper_base import HTMLScraperBase
from .text_utils import detect_serotype
from .types import ParsedItem


class NMHealthConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "nmh-data"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    LISTING_URL: ClassVar[str] = "https://www.nmhealth.org/about/erd/ideb/zdp/hps/"
    KEYWORDS: ClassVar[list[str]] = ["hantavirus", "hanta", "hps", "sin nombre"]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "HORIZON/0.1 (+https://79thunit.co.uk)",
    }

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        # NM Health: surface the headline + main article text as a single
        # "page snapshot" record. Phase 3 will parse the case table directly.
        title_node = soup.find("h1") or soup.find("title")
        title = title_node.get_text(strip=True) if title_node else "NM Health HPS update"
        # Pull the first 600 chars of body text as the summary.
        body = soup.find("main") or soup.body
        summary = body.get_text(" ", strip=True)[:600] if body else None

        today = datetime.now(tz=UTC).date()
        external_id = f"nmh:{today.isoformat()}"
        canonical = f"{self.LISTING_URL}\n{title}\n{today}".encode()

        return [
            ParsedItem(
                external_id=external_id,
                title=title,
                summary=summary,
                country_iso2="US",
                region="New Mexico",
                lat=None,
                lng=None,
                serotype_text=detect_serotype(f"{title} {summary or ''}"),
                reported_date=today,
                case_count=None,
                death_count=None,
                raw_url=self.LISTING_URL,
                raw_content=canonical,
            )
        ]
