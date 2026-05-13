"""mBio (ASM) RSS connector.

American Society for Microbiology open-access journal. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class MBioConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "mbio"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://journals.asm.org/action/showFeed?type=etoc&feed=rss&jc=mbio"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "dobrava",
        "orthohantavirus",
    ]
