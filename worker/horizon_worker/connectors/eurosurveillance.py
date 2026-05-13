"""Eurosurveillance RSS connector.

ECDC's peer-reviewed weekly journal of epidemiology, prevention and control
of communicable diseases in Europe. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class EurosurveillanceConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "eurosurveillance"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://www.eurosurveillance.org/action/showFeed?type=etoc&feed=rss&jc=esw"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "puuv",
        "dobrava",
        "dobv",
        "seoul virus",
        "seov",
        "hantaan",
        "htnv",
        "orthohantavirus",
        "nephropathia epidemica",
    ]
