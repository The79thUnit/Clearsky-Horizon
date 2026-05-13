"""Venezuela Ministerio del Poder Popular para la Salud (MPPS) RSS connector.

NATO B2. Venezuela is ANDV-endemic; case reports for hantavirus pulmonary
syndrome (HPS/HPS-like) have been documented in the Orinoco basin and
Andean foothills (Mérida, Barinas, Trujillo states). Venezuelan surveillance
data is significantly under-reported in international databases.

URL history:
  0.1.0: https://mpps.gob.ve/feed/ — confirmed 200,
         application/rss+xml; charset=UTF-8, 10 items on 2026-05-13.
         WordPress RSS 2.0. Spanish-language health news.
         Example item: "SAIAE realizó encuentro sobre Arbovirus en Venezuela"
         (2026-05-12). Keyword filter catches hantavirus-specific items.

NATO B2: official Venezuelan government source. Reporting quality and
cadence are highly variable given Venezuela's domestic situation; English-
language international coverage of Venezuelan hantavirus is extremely sparse.
This feed closes a significant gap in ANDV-region LatAm coverage.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class VenezuelaMPPSConnector(RSSConnectorBase):
    """Venezuela Ministry of Health (MPPS) WordPress RSS feed.

    Spanish-language official health news. Keyword list is bilingual because
    PAHO-origin documents and Venezuelan academic publications use WHO
    standard English acronyms alongside Spanish terminology.
    """

    SOURCE_CODE: ClassVar[str] = "venezuela-mpps"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://mpps.gob.ve/feed/"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept-language": "es-VE,es;q=0.9,en;q=0.8",
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
        # Spanish — primary language of MPPS publications
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
        # Venezuela-specific geography relevant to ANDV
        "orinoco",
        "merida",
        "barinas",
        "trujillo",
    ]
