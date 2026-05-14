"""CNN Health RSS feed connector.

CNN's health RSS feed at rss.cnn.com is the canonical machine-readable
surface for CNN Health coverage. NATO B2 (usually reliable, probably true).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class CNNConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cnn"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # 14 May 2026: CNN deprecated the `edition_health.rss` form. The base
    # cnn_health.rss feed at rss.cnn.com is still live (HTTP only — their
    # cert chain on rss.cnn.com is broken). HTTP is acceptable for a public
    # RSS feed; no auth or PII flows over this connection.
    FEED_URL: ClassVar[str] = "http://rss.cnn.com/rss/cnn_health.rss"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept": "application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.5",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "hantaan",
        "seoul virus",
    ]
