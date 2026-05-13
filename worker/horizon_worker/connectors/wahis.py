"""WOAH WAHIS (World Animal Health Information System) RSS connector.

World Organisation for Animal Health (formerly OIE). Tracks emerging
animal disease events globally; relevant for hantavirus because rodent
reservoir mortality and species jumps surface here first. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WAHISConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "wahis"
    # 0.2.0: the original wahis.woah.org/rss/list/EVENT path now 404s
    # (the WAHIS data portal moved entirely behind a React app + REST
    # API at wahis.woah.org/api/v1/...). That REST API requires auth
    # credentials we don't have. However the WOAH organisation's main
    # news feed at www.woah.org/en/rss/ remains open and DOES carry
    # hantavirus-relevant items — verified 2026-05-13: feed includes
    # "WOAH Statement on Hantavirus" dated 8 May 2026 (the official
    # WOAH position on the MV Hondius cluster). The animal-disease
    # event tracker is lost, but the high-signal items remain.
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://www.woah.org/en/rss/"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "orthohantavirus",
        "rodent",
        "peromyscus",
        "apodemus",
        "myodes",
        "oligoryzomys",
        "rattus norvegicus",
    ]
