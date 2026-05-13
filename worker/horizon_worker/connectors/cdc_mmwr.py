"""CDC MMWR (Morbidity and Mortality Weekly Report) RSS connector.

NATO A1 (completely reliable, confirmed). Weekly US surveillance + outbreak reports.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class CDCMMWRConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cdc-mmwr"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://tools.cdc.gov/api/v2/resources/media/132608.rss"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "sin nombre",
        "andes virus",
        "puumala",
    ]
