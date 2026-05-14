"""Public Health Agency of Canada (PHAC) news connector.

14 May 2026 rewrite: the old `canada.ca/en/news.atom?dept=publichealthagencyofcanada`
returned 404 after Canada.ca's news platform migration. The replacement is
the `api.io.canada.ca` Atom feed which is the same JSON/XML data source that
backs the Canada.ca news page itself.

NATO A1 — Public Health Agency of Canada press releases.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PHACConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "phac"
    PARSER_VERSION: ClassVar[str] = "0.3.0"
    FEED_URL: ClassVar[str] = (
        "https://api.io.canada.ca/io-server/gc/news/en/v2"
        "?dept=publichealthagencyofcanada"
        "&type=newsreleases"
        "&sort=publishedDate"
        "&orderBy=desc"
        "&pick=30"
        "&format=atom"
    )
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.5",
        "Accept-Language": "en-CA,en;q=0.9",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "sin nombre",
        "deer mouse",
        "rodent-borne",
        "andes virus",
    ]
