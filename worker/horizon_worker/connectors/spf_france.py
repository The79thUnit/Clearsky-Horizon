"""Santé publique France (SPF) news RSS connector. NATO A2.

Santé publique France is France's national public health agency (ANSP) --
the direct successor to InVS. It is the primary French authority for
communicable disease surveillance, epidemiological alerts, and outbreak
investigation.

Hantavirus context:
  France is not ANDV-endemic but is affected via:
    1. Imported cases -- the 2026 MV Hondius cruise-ship cluster produced
       a confirmed French case cluster (43 cases in the France production
       cluster as of 2026-05-13). SPF is the coordinating authority for
       French case tracking and risk communications.
    2. PUUV (Puumala virus) -- PUUV is endemic in Northeastern France
       (Ardennes, Champagne-Ardenne) where nephropathia epidemica cases
       are reported annually. SPF publishes weekly BEH surveillance data.

URL history:
  0.1.0: https://www.santepubliquefrance.fr/rss/news/1008
         Confirmed 200, RSS 2.0, 30 items, 2026-05-13.
         Dublin Core namespace; pubDate fields may be empty -- feedparser
         falls back to updated_parsed. French language.
         Portal at /rss lists all themed feeds; /rss/news/1008 is the
         general public health news stream.

NATO A2: official French government public health authority.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class SPFFranceConnector(RSSConnectorBase):
    """Santé publique France general public health news RSS."""

    SOURCE_CODE: ClassVar[str] = "spf-france"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.santepubliquefrance.fr/rss/news/1008"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        # WHO standard / English
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "hps",
        "hfrs",
        "hemorrhagic fever",
        "orthohantavirus",
        "puumala",
        "puuv",
        "seoul virus",
        "seov",
        "rodent",
        "zoonosis",
        # French — primary language of SPF publications
        "hantavirose",
        "syndrome pulmonaire",
        "syndrome cardiopulmonaire",
        "fièvre hémorragique",
        "fievre hemorragique",
        "rongeur",
        "zoonose",
        "surveillance épidémiologique",
        "surveillance epidemiologique",
        "alerte épidémiologique",
        "alerte epidemiologique",
        "maladie émergente",
        "maladie emergente",
        "nephropathia epidemica",
        "néphropathie épidémique",
        "nefropathia",
        # French geography (PUUV-endemic region)
        "ardennes",
        "champagne",
        # MV Hondius cruise-ship cluster context
        "hondius",
        "croisière",
        "croisiériste",
    ]
