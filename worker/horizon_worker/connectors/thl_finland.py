"""National Institute for Health and Welfare (THL) — Finland connector.

THL (Terveyden ja hyvinvoinnin laitos) is Finland's national public health
authority. Finland has the highest hantavirus notification rate in Europe
at 14.5 per 100,000 population (ECDC Annual Epidemiological Report 2023),
driven by Puumala virus (PUUV) in the bank vole reservoir. Peak season
follows bank vole population cycles, typically July-August, with major
epidemic years in 2008, 2012, 2016, 2020 (beech/oak mast-year correlation).

THL publishes news in Finnish (fi) and English (en). We query the
English-language news RSS which includes infectious disease bulletins.

NATO A1 (completely reliable / confirmed). Tier 1. official-authority.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class THLFinlandConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "thl-finland"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    # THL English-language news RSS feed.
    # Covers infectious disease bulletins, outbreak notifications, and
    # annual epidemiological summaries. Finnish-language items are excluded
    # by the keyword filter -- all hantavirus alerts are also issued in EN.
    FEED_URL: ClassVar[str] = "https://thl.fi/en/web/infectious-diseases-and-vaccinations/-/topics/hantavirus-in-finland/-/categories/rss"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "puumala",
        "puuv",
        "nephropathia epidemica",
        "myyräkuume",          # Finnish: "vole fever"
        "hfrs",
        "seoul virus",
        "orthohantavirus",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # THL blocks generic bots; a descriptive UA avoids 403.
        "Accept-Language": "en-US,en;q=0.9",
    }
