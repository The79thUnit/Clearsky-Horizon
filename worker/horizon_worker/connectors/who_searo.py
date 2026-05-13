"""WHO Regional Office for South-East Asia news RSS.

India, Indonesia, Thailand, Myanmar, etc. NATO A2.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WHOSEAROConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-searo"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.who.int/southeastasia/rss-feeds/news"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "orthohantavirus",
        "rodent-borne",
    ]
