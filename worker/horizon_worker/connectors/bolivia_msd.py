"""Bolivia Ministerio de Salud y Deportes (MSD) RSS connector. NATO B2.

Bolivia is endemic for ANDV (Andes orthohantavirus). Human cases are
documented primarily in the Beni and Pando departments (Amazon basin,
dense forest rodent habitat). The MSD publishes surveillance bulletins
and health news via a Joomla CMS RSS feed.

URL history:
  0.1.0: https://www.minsalud.gob.bo/?format=feed&type=rss — confirmed 200
         on 2026-05-13. Joomla 3.x RSS 2.0 feed. Items include ministry
         health news in Spanish. Example item: "BOLIVIA FORTALECE SISTEMA
         DE VIGILANCIA DE VIRUS RESPIRATORIOS CON CAPACITACION TECNICA"
         (2026-05-13). Keyword filter catches hantavirus-specific items.

NATO B2: official Bolivian government source. Reporting quality and
cadence are variable; hantavirus coverage is sparse relative to Argentina
and Chile, but Bolivia is under-reported in international databases.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class BoliviaMSDConnector(RSSConnectorBase):
    """Bolivia Ministry of Health and Sports RSS feed (Joomla CMS).

    Spanish-language official health news. Keyword list is bilingual
    because some MSD releases use English acronyms (HPS, HFRS) and
    WHO standardised terminology alongside Spanish text.
    """

    SOURCE_CODE: ClassVar[str] = "bolivia-msd"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.minsalud.gob.bo/?format=feed&type=rss"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # Signal Spanish-language preference; Joomla does content negotiation.
        "accept-language": "es-BO,es;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        # English / WHO standard
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "hps",
        "hfrs",
        "hemorrhagic fever",
        "orthohantavirus",
        "rodent",
        "zoonosis",
        "oligoryzomys",
        "peromyscus",
        # Spanish — primary language of MSD publications
        "hantavirosis",
        "virus andes",
        "sindrome cardiopulmonar",
        "sindrome pulmonar por hantavirus",
        "fiebre hemorragica",
        "fiebre hemorrágica",
        "roedor",
        "ratón colilargo",
        "raton colilargo",
        "vigilancia epidemiologica",
        "vigilancia epidemiológica",
        "brote",
        "zoonosis",
        "malbran",
        "malbrán",
    ]
