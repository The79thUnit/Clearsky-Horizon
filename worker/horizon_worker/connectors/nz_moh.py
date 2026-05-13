"""New Zealand Ministry of Health (Manatū Hauora) news RSS connector.

Hantavirus not endemic but imported cases are notifiable. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class NZMoHConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "nz-moh"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.health.govt.nz/news-media/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "seoul virus",
        "rodent-borne",
        "imported case",
    ]
