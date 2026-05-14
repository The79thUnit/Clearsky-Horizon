"""Reuters wire connector — hantavirus-filtered via Google News source query.

Reuters is one of the three major global wire services. Reports are
wire-grade edited before publication; corrections are issued formally.
NATO B2 (usually reliable, probably true). Tier 2.

Implementation: Google News RSS filtered to site:reuters.com.
Reuters discontinued most direct RSS in 2020; the Google News route
provides equivalent coverage with stable URL semantics.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ReutersHealthConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "reuters-health"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://news.google.com/rss/search?"
        "q=hantavirus+OR+%22Andes+virus%22+OR+%22hantavirus+pulmonary%22"
        "+site:reuters.com"
        "&hl=en-US&gl=US&ceid=US:en"
    )
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
        "orthohantavirus",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "Mozilla/5.0 (compatible; HORIZON/0.1; +https://79thunit.co.uk)",
    }
