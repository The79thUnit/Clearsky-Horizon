"""Robert Koch Institute Epidemiologisches Bulletin RSS connector.

Germany's federal disease control + surveillance institute. Weekly bulletin
covers all notifiable diseases including hantavirus (Puumala dominant in DE).
NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class RKIConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "rki"
    # 0.2.0: switched feed URL after RKI restructured rki.de in 2025-26.
    # The old /SiteGlobals/Functions/RSSFeed/... endpoint now 404s; the
    # canonical Epidemiologisches Bulletin feed is now served from the
    # institutional edoc server. Verified 2026-05-13: returns valid
    # RSS 2.0, 4 recent items, weekly cadence preserved.
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://edoc.rki.de/feed/rss_2.0/176904/45"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "puuv",
        "dobrava",
        "dobv",
        "seoul virus",
        "seov",
        "hantaan",
        "htnv",
        "orthohantavirus",
        "nephropathia epidemica",
    ]
