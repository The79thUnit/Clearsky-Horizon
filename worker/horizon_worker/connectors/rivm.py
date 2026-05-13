"""RIVM (Netherlands National Institute for Public Health) news scraper.

RIVM is the Dutch government's central public-health surveillance body
(equivalent to UKHSA / CDC / ECDC). For HORIZON specifically, RIVM is
critical because:

  * MV Hondius is Netherlands-flagged (operator: Oceanwide Expeditions,
    headquartered in Vlissingen). RIVM is the home-country authority.
  * Rotterdam is the disinfection port; remaining crew + medical staff
    are sailing there for arrival ~17 May 2026.
  * The Dutch index couple — 70-year-old Dutch male (deceased aboard
    2026-04-11) and 69-year-old female spouse (PCR-confirmed ANDV,
    deceased in South Africa 2026-04-26) — are the laboratory anchors
    of the entire cluster.
  * RIVM has actively published MV Hondius coverage; verified
    2026-05-13 the /en/news listing carries:
      /en/news/hantavirus-cruise-ship-passengers-have-arrived-by-plane-start-of-quarantine-period
      /en/news/update-hantavirus
    Both are direct, on-topic RIVM communications.

RIVM does NOT publish a public RSS feed (verified 2026-05-13 — every
plausible /en/rss.xml, /rss.xml, /news/rss path returns HTTP 404). The
news listing is SSR-rendered HTML at https://www.rivm.nl/en/news so we
scrape that directly.

NATO A1 — top-tier authoritative national MoH source.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import ClassVar

from bs4 import BeautifulSoup

from .html_scraper_base import HTMLScraperBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class RIVMConnector(HTMLScraperBase):
    SOURCE_CODE: ClassVar[str] = "rivm"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    LISTING_URL: ClassVar[str] = "https://www.rivm.nl/en/news"
    KEYWORDS: ClassVar[list[str]] = [
        # English (the /en/ path serves English titles)
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "seoul virus",
        "puumala",
        "puuv",
        "orthohantavirus",
        # MV Hondius specific (broad catch even if title doesn't say "hantavirus")
        "hondius",
        "cruise ship",
        "oceanwide",
        # Dutch equivalents in case the EN path occasionally serves NL
        "hantavirusinfectie",
        "muizenkoorts",  # colloquial NL for hantavirus disease
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # RIVM serves the same English content regardless of UA. Use a
        # plain identifying UA so we honour the site's logs.
        "user-agent": "HORIZON/0.1 (+https://hantavirus.software)",
    }

    # Match /en/news/{slug} but NOT /en/news (the index itself) or
    # /en/news?... (filter URLs). The slug must be a non-empty path
    # segment composed of lowercase-with-hyphens.
    _ARTICLE_HREF_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^/en/news/[a-z0-9][a-z0-9-]+$"
    )

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        out: list[ParsedItem] = []
        seen_urls: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = str(a.get("href", ""))
            if not self._ARTICLE_HREF_RE.match(href):
                continue

            link = f"https://www.rivm.nl{href}"
            if link in seen_urls:
                continue
            seen_urls.add(link)

            # RIVM article anchors usually have either:
            #   <a href="/en/news/foo"><h3>Title</h3>…</a>
            #   <a href="/en/news/foo">Title</a>
            # Take the inner text. Anchors that only wrap an image yield
            # an empty stripped string — drop those (the human-readable
            # anchor for the same article will be picked up below).
            title = a.get_text(strip=True)
            if not title or len(title) < 8:
                continue

            # RIVM puts a <time datetime="2026-05-12"> alongside each
            # article block. Find the closest <time> in the same
            # parent article/li/div.
            reported: date | None = None
            container = a.find_parent(["article", "li", "div"])
            if container is not None:
                time_node = container.find("time")
                if time_node is not None:
                    dt_attr = time_node.get("datetime") or ""
                    if dt_attr:
                        try:
                            reported = datetime.fromisoformat(
                                dt_attr.replace("Z", "+00:00")
                            ).date()
                        except (ValueError, TypeError):
                            reported = None
                    if reported is None:
                        # Fallback: parse the human-readable text
                        # "12 May 2026" or "May 12, 2026".
                        date_text = time_node.get_text(strip=True)
                        if date_text:
                            reported = parse_date_safe(
                                date_text,
                                "%d %B %Y",
                                "%B %d, %Y",
                                "%Y-%m-%d",
                            )

            # RIVM is the NL national authority — default country code
            # is NL; detect_country may surface a more specific one if
            # the title explicitly mentions another country.
            country = detect_country(title) or "NL"
            serotype = detect_serotype(title)

            # Berkeley-style canonical content: URL + title + slug-derived
            # external id keeps re-fetches deterministic.
            slug = href.rsplit("/", 1)[-1]
            canonical = f"{link}\n{title}\n{slug}".encode("utf-8")

            out.append(
                ParsedItem(
                    external_id=f"rivm:{slug}",
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
        return out
