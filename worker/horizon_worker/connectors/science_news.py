"""Science magazine news RSS connector.

AAAS Science news feed. Hantavirus mentions rare but high-quality.
NATO A2.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ScienceNewsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "science-news"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.science.org/rss/news_current.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "sin nombre",
        "puumala",
        "orthohantavirus",
    ]
