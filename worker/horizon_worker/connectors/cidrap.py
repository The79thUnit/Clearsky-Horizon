"""CIDRAP News RSS connector.

University of Minnesota Center for Infectious Disease Research and Policy.
Editorial outbreak coverage; gold standard for English-language US/global
public health journalism. NATO B2 (usually reliable, probably true).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class CIDRAPNewsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cidrap-news"
    # 0.2.0: feed URL updated 2026-05-13. CIDRAP retired the
    # /news-perspective/feed path; canonical feed is now /rss.xml at
    # the site root. Verified: HTTP 200, application/rss+xml,
    # ~85 KB body, fresh items.
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://www.cidrap.umn.edu/rss.xml"
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
        "orthohantavirus",
        "rodent-borne",
        "deer mouse",
    ]
