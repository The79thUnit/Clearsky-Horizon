"""PLOS Neglected Tropical Diseases RSS connector.

Open-access peer-reviewed journal covering neglected tropical diseases.
Hantavirus straddles the boundary: not formally NTD, but covered when
outbreaks affect poor / rural populations. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PLOSNTDsConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "plos-ntds"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://journals.plos.org/plosntds/feed/atom"
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
