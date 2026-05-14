"""BBC News Health RSS connector.

Established broadcaster, fact-checked editorial standards.
Picked up by Google's Knowledge Graph for entity matching.
NATO B2 (usually reliable, probably true). Tier 2.

BBC Health RSS is a confirmed public feed — no auth, no scraping.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class BBCHealthConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "bbc-health"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://feeds.bbci.co.uk/news/health/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "dobrava",
        "nephropathia",
        "orthohantavirus",
    ]
