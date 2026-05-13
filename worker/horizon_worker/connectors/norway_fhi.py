"""Folkehelseinstituttet (FHI) — Norwegian Institute of Public Health RSS.

NATO A2. Norway has documented PUUV (Puumala virus) cases, primarily in
Southeast Norway (Innlandet / former Hedmark and Oppland counties). FHI
is the Norwegian national public health institute responsible for
communicable disease surveillance, epidemiological investigation, and
public health recommendations.

Hantavirus context:
  PUUV (Puumala virus): the primary hantavirus in Norway. Endemic in
  the Innlandet region (Hedmark, Oppland). Lower per-capita incidence
  than Sweden or Finland but annual cases are reported. The bank vole
  (Myodes glareolus) is the reservoir. Norwegian term for the human
  disease is "hantavirusinfeksjon" or informally "musesjuke" (mouse
  disease). FHI also monitors Seoul virus risk from imported rodents.

URL history:
  0.1.0: https://www.fhi.no/rss/nyheter/
         Confirmed 200, RSS 2.0, 20 items, 2026-05-13.
         General FHI news RSS. Norwegian language.

NATO A2: official Norwegian government public health institute.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class NorwayFHIConnector(RSSConnectorBase):
    """Folkehelseinstituttet general news RSS (Norway)."""

    SOURCE_CODE: ClassVar[str] = "norway-fhi"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.fhi.no/rss/nyheter/"
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept-language": "nb-NO,nb;q=0.9,no;q=0.8,en;q=0.7",
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
        # Norwegian — primary language of FHI publications
        "hantavirusinfeksjon",    # hantavirus infection
        "musesjuke",              # mouse disease (colloquial for PUUV)
        "gnager",                 # rodent
        "zoonose",
        "blodfeber",              # hemorrhagic fever
        "nefropati",              # nephropathy (NE)
        "nephropathia epidemica",
        # Norwegian geography (PUUV-endemic regions)
        "innlandet",
        "hedmark",
        "oppland",
        "østlandet",
    ]
