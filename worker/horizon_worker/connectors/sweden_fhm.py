"""Folkhälsomyndigheten (FHM) — Swedish Public Health Agency RSS connector.

NATO A2. Sweden has one of the highest PUUV (Puumala virus) incidence
rates in Europe. Significant annual cycles of nephropathia epidemica
(NE) are documented, primarily in northern Sweden (Norrland, Ångermanland,
Västernorrland, Jämtland). FHM is the primary Swedish authority for
communicable disease surveillance and outbreak alerts.

Hantavirus context:
  PUUV (Puumala virus): the dominant hantavirus in Sweden. The bank
  vole (Myodes glareolus) is the primary reservoir. Swedish term for
  the human disease is "sorkfeber" (bank vole fever). FHM publishes
  annual NE surveillance summaries and outbreak alerts during high-
  incidence years.

URL history:
  0.1.0: https://www.folkhalsomyndigheten.se/nyheter-och-press/nyhetsarkiv/
          ?topic=smittskydd-och-sjukdomar&syndication=rss
         Confirmed 200, RSS 2.0, 21 items, 2026-05-13.
         Topic filter: "smittskydd-och-sjukdomar" (communicable disease
         control and illness). Narrows the general news feed to
         infectious-disease items. Swedish language.

NATO A2: official Swedish government public health authority.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class SwedenFHMConnector(RSSConnectorBase):
    """Folkhälsomyndigheten infectious-disease news RSS (Sweden)."""

    SOURCE_CODE: ClassVar[str] = "sweden-fhm"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://www.folkhalsomyndigheten.se/nyheter-och-press/nyhetsarkiv/"
        "?topic=smittskydd-och-sjukdomar&syndication=rss"
    )
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept-language": "sv-SE,sv;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        # WHO standard / English
        "hantavirus",
        "hanta",
        "puumala",
        "puuv",
        "orthohantavirus",
        "hps",
        "hfrs",
        "hemorrhagic fever",
        "rodent",
        "zoonosis",
        # Swedish — primary language of FHM publications
        "sorkfeber",              # bank vole fever (PUUV disease / NE)
        "nephropathia epidemica",
        "gnagare",                # rodent
        "zoonos",
        "hemorragi",
        "blödningsfeber",         # hemorrhagic fever
        "sorkpopulation",         # bank vole population (outbreak predictor)
        # Swedish geography (high-PUUV-incidence regions)
        "norrland",
        "västernorrland",
        "ångermanland",
        "jämtland",
        "norrbotten",
        "västerbotten",
        "sundsvall",
        "härnösand",
    ]
