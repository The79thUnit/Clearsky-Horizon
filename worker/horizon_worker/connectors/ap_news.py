"""Associated Press connector — hantavirus-filtered via Google News source query.

AP is one of the three major global wire services. Member-funded,
non-profit structure; strong editorial independence and correction policy.
First to move on most US domestic outbreak reports (CDC/NIH embargoes
lift simultaneously to AP wire).
NATO B2 (usually reliable, probably true). Tier 2.

Implementation: Google News RSS filtered to site:apnews.com.
AP has no public topic RSS; the Google News route is the standard
approach used by downstream aggregators.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class APNewsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "ap-news"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://news.google.com/rss/search?"
        "q=hantavirus+OR+%22Andes+virus%22+OR+%22hantavirus+pulmonary%22"
        "+site:apnews.com"
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
