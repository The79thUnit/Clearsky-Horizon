"""Public Health Agency of Canada (PHAC) news Atom feed.

Government of Canada news filtered to PHAC department. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PHACConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "phac"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.canada.ca/en/news.atom?dept=publichealthagencyofcanada"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "sin nombre",
        "deer mouse",
        "rodent-borne",
    ]
