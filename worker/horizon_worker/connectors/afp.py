"""Agence France-Presse connector — hantavirus-filtered via Google News source query.

AFP is the third major global wire service. Strong francophone and
Latin American bureau network — critical for ANDV/PUUV coverage where
French-language reporting (France, Switzerland, Belgium) or AFP's
Buenos Aires and Santiago bureaus may move before Anglophone wires.
NATO B2 (usually reliable, probably true). Tier 2.

Implementation: Google News RSS filtered to site:afp.com.
AFP has no free public RSS; Google News source-filtered is the
standard aggregator route.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class AFPConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "afp-wire"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://news.google.com/rss/search?"
        "q=hantavirus+OR+%22virus+Andes%22+OR+%22hantavirus+pulmonaire%22"
        "+site:afp.com"
        "&hl=en-US&gl=US&ceid=US:en"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "virus andes",
        "andv",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "dobrava",
        "orthohantavirus",
        "pulmonaire",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "Mozilla/5.0 (compatible; HORIZON/0.1; +https://79thunit.co.uk)",
    }
