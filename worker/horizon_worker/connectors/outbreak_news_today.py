"""Outbreak News Today RSS connector.

Independent outbreak news site curated by Robert Herriman. NATO C3
(fairly reliable, possibly true). Useful for early signal; analyst review
mandatory before any high-confidence write.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class OutbreakNewsTodayConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "outbreak-news-today"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://outbreaknewstoday.com/feed/"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "dobrava",
    ]
