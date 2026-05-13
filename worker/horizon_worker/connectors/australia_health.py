"""Australian Government Department of Health news RSS connector.

Hantavirus is not endemic in Australia but imported cases are notifiable.
Includes National Notifiable Diseases Surveillance System updates.
NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class AustraliaHealthConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "australia-health"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.health.gov.au/news/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "seoul virus",
        "puumala",
        "rodent-borne",
        "imported case",
    ]
