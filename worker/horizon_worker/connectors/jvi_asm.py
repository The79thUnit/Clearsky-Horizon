"""Journal of Virology (ASM) RSS connector.

American Society for Microbiology's flagship virology journal.
Peer-reviewed. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class JVIASMConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "jvi-asm"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://journals.asm.org/action/showFeed?type=etoc&feed=rss&jc=jvi"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
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
