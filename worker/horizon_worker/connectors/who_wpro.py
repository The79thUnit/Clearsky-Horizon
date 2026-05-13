"""WHO news RSS (global English feed).

Originally targeted the WHO Regional Office for the Western Pacific
(WPRO) news RSS at /westernpacific/rss-feeds/news. WHO retired all
regional-office RSS feeds on who.int as part of a 2024-2025 site
restructure; the old URL returns HTTP 404.

Replacement (0.2.0, 2026-05-13, migration 047):
  https://www.who.int/rss-feeds/news-english.xml
  Confirmed 200, 25 items. This is WHO's canonical global English
  news RSS and is a superset of all regional office content.
  Top items on 2026-05-13 included both WHO DG hantavirus messages
  related to the MV Hondius cruise-ship cluster.

The source code and DB row are retained as 'who-wpro'. The DB notes
are updated via migration 047 to reflect the new feed scope.

Note: three other WHO regional RSS feeds are also dead as of this
investigation (all returning 404 or 302->404):
  who-euro:  https://www.who.int/europe/rss-feeds/news
  who-searo: https://www.who.int/southeastasia/rss-feeds/news
  who-emro:  https://www.emro.who.int/rss-feeds/whoemro-rss.xml
Those are tracked separately; this migration only fixes who-wpro.

NATO A2 (WHO authoritative source, probably true).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class WHOWPROConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-wpro"
    # 0.1.0: https://www.who.int/westernpacific/rss-feeds/news — 404 (retired)
    # 0.2.0: WHO global English news RSS — confirmed 200, 25 items, 2026-05-13
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://www.who.int/rss-feeds/news-english.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "puumala",
        "puuv",
        "orthohantavirus",
        "rodent-borne",
    ]
