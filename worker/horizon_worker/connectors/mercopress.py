"""Mercopress connector — South Atlantic / Southern Cone news agency.

Mercopress covers Argentina, Chile, Uruguay, Paraguay, Bolivia, Brazil,
and the Falkland Islands. Independent English-language wire focused
exclusively on the Southern Cone region — the primary ANDV endemic zone.
Frequently covers hantavirus outbreaks in Patagonia, Neuquén, Río Negro,
and Chilean regions before larger wires pick them up.
NATO C3 (fairly reliable, possibly true). Tier 3.

Direct RSS: https://en.mercopress.com/rss — confirmed public feed.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class MercopressConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "mercopress"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://en.mercopress.com/rss"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "andes virus",
        "andv",
        "sin nombre",
        "puumala",
        "fiebre hemorragica",
        "orthohantavirus",
    ]
