"""Public Health Scotland news RSS connector.

Scotland's national public-health body. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PHSConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "phs"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://publichealthscotland.scot/all-news/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "rodent-borne",
        "puumala",
        "seoul virus",
    ]
