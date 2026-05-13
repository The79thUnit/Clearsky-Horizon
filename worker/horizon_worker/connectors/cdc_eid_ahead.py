"""CDC EID Ahead-of-Print RSS connector.

Pre-publication EID articles. Earlier signal than the monthly issue feed.
NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class CDCEIDAheadConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cdc-eid-ahead"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://wwwnc.cdc.gov/eid/rss/upcoming.xml"
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
