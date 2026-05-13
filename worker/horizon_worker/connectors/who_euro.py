"""WHO Regional Office for Europe news RSS connector.

Covers European region including Russia + Central Asia + Israel. NATO A2.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WHOEUROConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-euro"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.who.int/europe/rss-feeds/news"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "puuv",
        "dobrava",
        "dobv",
        "seoul virus",
        "seov",
        "hantaan",
        "htnv",
        "orthohantavirus",
        "nephropathia epidemica",
    ]
