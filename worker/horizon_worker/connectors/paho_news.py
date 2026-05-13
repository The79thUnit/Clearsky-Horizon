"""PAHO (Pan American Health Organization) general news RSS. NATO B2.

PAHO is the WHO regional office for the Americas. Their news RSS at
/en/rss.xml covers outbreak alerts, epidemiological advisories, and press
releases. This source complements paho-alerts (A1, hantavirus topic page)
by catching cross-disease items that mention hantavirus in general outbreak
news before the topic page is updated (e.g. comparative epi, ANDV updates
in broader WHO/PAHO bulletins).

URL history:
  0.1.0: https://www.paho.org/en/rss.xml — confirmed 200, 8276 bytes,
         10 items on 2026-05-13. Third item: "PAHO held Q&A session on
         hantavirus after outbreak on cruise ship" (MV Hondius cluster).
         application/rss+xml; charset=utf-8.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class PAHONewsConnector(RSSConnectorBase):
    """PAHO general news RSS — complements paho-alerts (hantavirus topic page).

    paho-alerts (A1) targets the hantavirus-specific topic listing.
    This source catches hantavirus mentions in the broader PAHO news
    stream before they propagate to the topic page, and covers regional
    outbreak context items (ANDV in Chile/Argentina, HFRS in Europe)
    that PAHO frames as hemispheric news rather than topic-page docs.
    """

    SOURCE_CODE: ClassVar[str] = "paho-news"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.paho.org/en/rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "hantavirosis",
        "hps",
        "hfrs",
        "hemorrhagic fever with renal syndrome",
        "hantavirus pulmonary syndrome",
        "orthohantavirus",
        "rodent-borne",
        "rodent reservoir",
        "oligoryzomys",
        "peromyscus",
        "zoonosis",
        "zoonotic",
        # Cruise-ship / MV Hondius context items
        "cruise ship",
        "hondius",
        # Spanish — PAHO bilingual releases sometimes mix languages
        "virus andes",
        "sindrome cardiopulmonar",
        "sindrome pulmonar",
        "hantavirosis",
        "roedor",
    ]
