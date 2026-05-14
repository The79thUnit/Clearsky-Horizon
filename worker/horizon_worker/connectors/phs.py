"""Public Health Scotland news scraper.

14 May 2026 rewrite: the old RSS feed at publichealthscotland.scot/all-news/rss.xml
was retired during their CMS migration. We now scrape the /news/ HTML
listing instead. NATO A1.
"""

from __future__ import annotations

import re
from datetime import date
from typing import ClassVar
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .html_scraper_base import HTMLScraperBase
from .text_utils import detect_serotype, parse_date_safe, strip_html
from .types import ParsedItem


_BASE = "https://publichealthscotland.scot"

# Match URLs like /news/2026/may/hantavirus-cruise-ship-outbreak/
_NEWS_URL_RE = re.compile(r"^/news/\d{4}/[a-z]+/[a-z0-9-]+/?$")
# Match month-year segments in URLs so we can derive a date if no <time> exists.
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _date_from_url(href: str) -> date | None:
    parts = href.strip("/").split("/")
    if len(parts) < 4 or parts[0] != "news":
        return None
    try:
        year = int(parts[1])
        month = _MONTH_NAMES.get(parts[2].lower())
        if not month:
            return None
        return date(year, month, 1)
    except (ValueError, IndexError):
        return None


class PHSConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "phs"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    LISTING_URL: ClassVar[str] = "https://publichealthscotland.scot/news/"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "Accept-Language": "en-GB,en;q=0.9",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "rodent-borne",
        "puumala",
        "seoul virus",
        "andes virus",
    ]

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        items: list[ParsedItem] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not _NEWS_URL_RE.match(href):
                continue
            full_url = urljoin(_BASE, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            title = strip_html(a.get_text(" ", strip=True))
            if not title or len(title) < 8:
                continue

            # Try to find a date in nearby DOM, else derive from URL.
            reported: date | None = None
            parent = a.find_parent(["article", "li", "div"])
            if parent is not None:
                t = parent.find("time")
                if t and t.get("datetime"):
                    reported = parse_date_safe(t["datetime"][:10], "%Y-%m-%d")
                if reported is None:
                    text = parent.get_text(" ", strip=True)
                    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
                    if m:
                        reported = parse_date_safe(m.group(1), "%Y-%m-%d")
            if reported is None:
                reported = _date_from_url(href)

            serotype = detect_serotype(title, country_iso2="GB")
            external_id = f"phs:{full_url}"
            canonical = f"{external_id}\n{title}".encode("utf-8")

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title[:300],
                    summary=None,
                    country_iso2="GB",
                    region="Scotland",
                    lat=None,
                    lng=None,
                    serotype_text=serotype,
                    reported_date=reported,
                    case_count=None,
                    death_count=None,
                    raw_url=full_url,
                    raw_content=canonical,
                )
            )

        return items
