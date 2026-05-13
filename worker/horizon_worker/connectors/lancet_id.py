"""The Lancet Infectious Diseases current-issue RSS connector.

Tier-1 peer-reviewed infectious disease journal. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class LancetIDConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "lancet-id"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.thelancet.com/rssfeed/laninf_current.xml"
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
