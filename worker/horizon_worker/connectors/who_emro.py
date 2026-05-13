"""WHO Regional Office for the Eastern Mediterranean news RSS.

Covers Egypt, Saudi Arabia, Iran, Iraq, etc. Hantavirus uncommon but kept
for completeness on zoonotic surveillance. NATO A2.

STATUS: DISABLED as of 2026-05-13 (migration 049).
  emro.who.int/rss-feeds/whoemro-rss.xml returns HTTP 302 then 404.
  The WHO CMS restructure that broke who-euro, who-searo, and who-wpro
  also decommissioned the EMRO RSS feed.
  EMRO region has minimal ANDV/HFRS burden; who-don (global disease
  outbreak news, NATO A1) provides adequate coverage.
  Re-enable path: check emro.who.int for a replacement RSS URL and
  update FEED_URL + bump PARSER_VERSION before re-enabling.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WHOEMROConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-emro"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.emro.who.int/rss-feeds/whoemro-rss.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "rodent-borne",
        "zoonotic",
    ]
