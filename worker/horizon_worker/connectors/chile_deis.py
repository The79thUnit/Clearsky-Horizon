"""Chile Departamento de Epidemiología (DEIS / MINSAL) news RSS.

Chile reports significant Andes virus activity, especially in Aysén and
Los Lagos regions. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ChileDEISConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "chile-deis"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.minsal.cl/feed/"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "virus andes",
        "sindrome cardiopulmonar",
        "fiebre hemorrágica",
        "aysén",
        "aysen",
    ]
