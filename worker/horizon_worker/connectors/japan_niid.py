"""Japan National Institute of Infectious Diseases IDWR RSS connector.

NIID's Infectious Disease Weekly Report. Japan periodically reports HFRS
clusters (Seoul virus from imported rats). NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class JapanNIIDConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "japan-niid"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.niid.go.jp/niid/en/rss/whatsnew-en.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "orthohantavirus",
    ]
