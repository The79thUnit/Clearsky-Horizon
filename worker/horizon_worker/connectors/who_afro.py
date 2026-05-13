"""WHO Regional Office for Africa (AFRO) news RSS connector.

Africa-region public-health bulletin separate from the global WHO DON feed.
Less directly relevant to hantavirus (mostly absent in Africa) but kept for
completeness + future zoonotic surveillance. NATO A2.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WHOAFROConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-afro"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.afro.who.int/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "rodent-borne",
        "zoonotic",
    ]
