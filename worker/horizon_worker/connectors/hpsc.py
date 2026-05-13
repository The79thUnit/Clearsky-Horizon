"""Health Protection Surveillance Centre (HPSC) Ireland RSS connector.

Ireland's HSE national surveillance centre for communicable diseases.
NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class HPSCConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "hpsc"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.hpsc.ie/news/RSS/"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "seoul virus",
        "rodent-borne",
        "zoonotic",
    ]
