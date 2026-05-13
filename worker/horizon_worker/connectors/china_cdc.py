"""China CDC Weekly RSS connector.

China CDC's peer-reviewed weekly bulletin. China is the global HFRS
heartland (Hantaan + Seoul virus dominant). NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ChinaCDCConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "china-cdc"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://weekly.chinacdc.cn/rss/Article.htm"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "haemorrhagic fever with renal syndrome",
        "hemorrhagic fever with renal syndrome",
        "orthohantavirus",
    ]
