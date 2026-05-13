"""PLOS Pathogens RSS connector.

Open-access peer-reviewed journal for pathogen biology. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PLOSPathogensConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "plos-pathogens"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://journals.plos.org/plospathogens/feed/atom"
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
        "htnv",
        "seoul virus",
        "seov",
        "dobrava",
        "dobv",
        "orthohantavirus",
    ]
