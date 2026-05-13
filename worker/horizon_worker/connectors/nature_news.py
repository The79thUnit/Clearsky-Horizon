"""Nature.com news RSS connector.

Nature's general news feed across all subject areas. Hantavirus mentions are
rare but high-quality (typically major outbreaks or research breakthroughs).
NATO A2.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class NatureNewsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "nature-news"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.nature.com/nature.rss"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "sin nombre",
        "puumala",
        "orthohantavirus",
    ]
