"""KDCA — Korea Disease Control and Prevention Agency English press releases.

KDCA publishes English press releases for international stakeholders at
https://www.kdca.go.kr/contents.es?mid=a30201000000 . The page is a listing
of cards with title, date, and a link to the full release.

NATO B2 (usually reliable, probably true). Korean primary source for HTNV
(Hantaan virus) and SEOV surveillance — Korea is HTNV endemic. provenance_type:
official-authority. Tier 2.
"""

from __future__ import annotations

import re
from datetime import date
from typing import ClassVar

from bs4 import BeautifulSoup

from .html_scraper_base import HTMLScraperBase
from .text_utils import (
    detect_country,
    detect_serotype,
    parse_date_safe,
)
from .types import ParsedItem


class KDCAConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "kdca"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # KDCA English news page (press releases for international stakeholders).
    LISTING_URL: ClassVar[str] = (
        "https://www.kdca.go.kr/contents.es?mid=a30201000000"
    )
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "Accept-Language": "en-GB,en;q=0.9",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "haemorrhagic fever with renal syndrome",
        "hemorrhagic fever with renal syndrome",
        "rodent",
    ]

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        """Parse the KDCA listing page into ParsedItems.

        Tolerant of layout drift: tries multiple selector strategies so a
        partial CSS-class rename upstream doesn't blank the feed.
        """
        items: list[ParsedItem] = []

        # Strategy 1: anchor tags inside list elements whose href contains
        # contentsView / boardView (KDCA's article-detail routes).
        anchors = soup.select(
            "a[href*='contentsView'], a[href*='boardView'], a[href*='view.es']"
        )
        seen_urls: set[str] = set()

        for a in anchors:
            href = a.get("href", "").strip()
            if not href or href.startswith("#"):
                continue
            if href in seen_urls:
                continue
            seen_urls.add(href)

            title = " ".join(a.get_text(" ", strip=True).split())
            if not title or len(title) < 8:
                continue

            # Resolve relative URL
            if href.startswith("/"):
                href = f"https://www.kdca.go.kr{href}"
            elif not href.startswith("http"):
                href = f"https://www.kdca.go.kr/{href.lstrip('./')}"

            # Try to find a date in nearby DOM. KDCA lists put the date in a
            # sibling <span class="date"> or in a parent <li>. We look at the
            # parent's text and regex-match a YYYY-MM-DD pattern.
            parent = a.parent
            date_text = parent.get_text(" ", strip=True) if parent else ""
            date_match = re.search(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})", date_text)
            reported: date | None = None
            if date_match:
                raw = date_match.group(1).replace(".", "-").replace("/", "-")
                # Normalise single-digit month/day
                parts = raw.split("-")
                if len(parts) == 3:
                    yyyy, mm, dd = parts
                    reported = parse_date_safe(
                        f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}",
                        "%Y-%m-%d",
                    )

            country = detect_country(title) or "KR"
            serotype = detect_serotype(title)

            external_id = f"kdca:{href}"
            canonical = f"{external_id}\n{title}\n{date_text}".encode("utf-8")

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title[:280],
                    summary=None,
                    country_iso2=country,
                    region=None,
                    lat=None,
                    lng=None,
                    serotype_text=serotype,
                    reported_date=reported,
                    case_count=None,
                    death_count=None,
                    raw_url=href,
                    raw_content=canonical,
                )
            )

        return items
