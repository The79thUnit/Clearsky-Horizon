"""Health Protection Surveillance Centre (HPSC) Ireland — news scraper.

14 May 2026 rewrite: HPSC retired their RSS feed at /news/RSS/. The /news/
HTML page is still live and exposes article links in the form
/news/title-NNNNN-en.html . NATO A1.
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


_BASE = "https://www.hpsc.ie"
_TITLE_URL_RE = re.compile(r"/news/title-\d+-en\.html$")


class HPSCConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "hpsc"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    LISTING_URL: ClassVar[str] = "https://www.hpsc.ie/news/"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "Accept-Language": "en-IE,en-GB;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "seoul virus",
        "rodent-borne",
        "zoonotic",
        "andes virus",
    ]

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        items: list[ParsedItem] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not _TITLE_URL_RE.search(href):
                continue
            full_url = urljoin(_BASE, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            title = strip_html(a.get_text(" ", strip=True))
            if not title or len(title) < 8:
                continue

            reported: date | None = None
            parent = a.find_parent(["article", "li", "div", "tr"])
            if parent is not None:
                text = parent.get_text(" ", strip=True)
                # HPSC dates: "10 May 2026" or "10/05/2026"
                m = re.search(
                    r"(\d{1,2})\s+(January|February|March|April|May|June|July|"
                    r"August|September|October|November|December)\s+(\d{4})",
                    text,
                    re.IGNORECASE,
                )
                if m:
                    day = int(m.group(1))
                    month_str = m.group(2).lower()
                    months = {
                        "january": 1, "february": 2, "march": 3, "april": 4,
                        "may": 5, "june": 6, "july": 7, "august": 8,
                        "september": 9, "october": 10, "november": 11, "december": 12,
                    }
                    month = months.get(month_str)
                    year = int(m.group(3))
                    if month:
                        try:
                            reported = date(year, month, day)
                        except ValueError:
                            reported = None
                if reported is None:
                    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
                    if m:
                        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                        try:
                            reported = date(y, mo, d)
                        except ValueError:
                            reported = None

            serotype = detect_serotype(title, country_iso2="IE")
            external_id = f"hpsc:{full_url}"
            canonical = f"{external_id}\n{title}".encode("utf-8")

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title[:300],
                    summary=None,
                    country_iso2="IE",
                    region=None,
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
