"""ECDC hantavirus topic page scraper. NATO A1.

ECDC publishes country-by-country surveillance data via the Surveillance Atlas
and free-form alerts at /en/hantavirus-infection. We scrape the alerts page.
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from bs4 import BeautifulSoup

from .html_scraper_base import HTMLScraperBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class ECDCConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "ecdc-tessy"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    LISTING_URL: ClassVar[str] = (
        "https://www.ecdc.europa.eu/en/hantavirus-infection/surveillance-and-disease-data"
    )
    KEYWORDS: ClassVar[list[str]] = ["hantavirus", "hanta", "andes", "puumala", "dobrava"]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "HORIZON/0.1 (+https://79thunit.co.uk)",
    }

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        out: list[ParsedItem] = []
        # Look for <a> linking to /en/publications-data/ or /en/news-events/
        for a in soup.find_all("a", href=True):
            href = str(a.get("href", ""))
            if not any(
                seg in href
                for seg in ("/en/publications-data/", "/en/news-events/", "/publications-data/")
            ):
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 8:
                continue
            link = href if href.startswith("http") else f"https://www.ecdc.europa.eu{href}"

            reported: date | None = None
            date_node = a.find_next("time") or a.find_next(
                class_=lambda c: bool(c and "date" in c.lower())
            )
            if date_node:
                attr = date_node.get("datetime") if date_node.name == "time" else None
                if isinstance(attr, list):
                    attr = attr[0] if attr else None
                date_str = str(attr) if attr else date_node.get_text(strip=True)
                reported = parse_date_safe(date_str[:10], "%Y-%m-%d", "%d %B %Y", "%B %d, %Y")

            country = detect_country(title)
            serotype = detect_serotype(title)
            canonical = f"{link}\n{title}".encode()

            out.append(
                ParsedItem(
                    external_id=f"ecdc:{link}",
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
                    raw_url=link,
                    raw_content=canonical,
                )
            )

        seen: set[str] = set()
        unique: list[ParsedItem] = []
        for item in out:
            if item.raw_url in seen:
                continue
            seen.add(item.raw_url)
            unique.append(item)
        return unique
