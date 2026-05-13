"""Google News RSS connector. Real-time global news coverage filtered by query.

NATO C3 (fairly reliable, possibly true). Wide coverage but mixed source quality;
analyst review required to escalate any individual record.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class GoogleNewsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "google-news"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # Query: hantavirus OR Andes virus, English only. Google's RSS endpoint
    # accepts `q=` for keyword search and `hl=en-GB&gl=GB&ceid=GB:en` for locale.
    FEED_URL: ClassVar[str] = (
        "https://news.google.com/rss/search?"
        "q=hantavirus+OR+%22Andes+virus%22+OR+%22Sin+Nombre+virus%22"
        "&hl=en-GB&gl=GB&ceid=GB:en"
    )
    KEYWORDS: ClassVar[list[str]] = ["hantavirus", "hanta", "andes virus", "sin nombre", "puumala"]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # Google News is friendlier with a real user-agent string.
        "user-agent": "Mozilla/5.0 (compatible; HORIZON/0.1; +https://79thunit.co.uk)",
    }
