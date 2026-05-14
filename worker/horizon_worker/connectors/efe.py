"""EFE wire service connector — hantavirus-filtered via Google News source query.

EFE is the world's largest Spanish-language news agency, headquartered
in Madrid. Dominant wire for Latin America — Argentina, Chile, Peru,
Bolivia, Paraguay all publish EFE dispatches ahead of Anglophone wires
on regional hantavirus events. Critical for ANDV coverage.
NATO B3 (usually reliable, possibly true). Tier 2.

Credibility 3 rather than 2: EFE articles are wire-grade but Spanish-
language content requires translation before analyst review; serotype
and case-count extraction is less reliable on non-English text.

Implementation: Google News RSS filtered to site:efe.com with Spanish
query terms. Locale set to es-419 (Latin American Spanish).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class EFEConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "efe-wire"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://news.google.com/rss/search?"
        "q=hantavirus+OR+%22virus+Andes%22+OR+%22hantavirus+pulmonar%22"
        "+site:efe.com"
        "&hl=es-419&gl=AR&ceid=AR:es-419"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "virus andes",
        "andes virus",
        "andv",
        "sin nombre",
        "puumala",
        "hantaan",
        "hfrs",
        "hps",
        "fiebre hemorragica",
        "sindrome pulmonar",
        "orthohantavirus",
    ]
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "user-agent": "Mozilla/5.0 (compatible; HORIZON/0.1; +https://79thunit.co.uk)",
    }
