"""Viruses (MDPI) journal RSS connector.

Open-access peer-reviewed virology journal. NATO B2 (MDPI editorial standards
are looser than top-tier publishers; still peer-reviewed).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class VirusesMDPIConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "viruses-mdpi"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.mdpi.com/rss/journal/viruses"
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
