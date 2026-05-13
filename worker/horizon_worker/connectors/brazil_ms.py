"""Brazil Ministério da Saúde news RSS connector.

Brazil reports significant hantavirus activity across the southern and
central states (HPS caused by Araraquara, Juquitiba, and Laguna Negra
viruses). NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class BrazilMSConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "brazil-ms"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.gov.br/saude/pt-br/assuntos/noticias/RSS"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        # Portuguese
        "hantavirose",
        "sindrome cardiopulmonar",
        "síndrome cardiopulmonar",
        "febre hemorrágica",
        "febre hemorragica",
        "araraquara",
        "juquitiba",
        "laguna negra",
        "roedor",
        "ratos silvestres",
    ]
