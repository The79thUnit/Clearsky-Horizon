"""CDC Emerging Infectious Diseases journal RSS connector.

NATO A1 (completely reliable, confirmed). Peer-reviewed CDC journal of record
for emerging infectious diseases. Ahead-of-print articles (pre-issue).

URL history:
  0.1.0: current.xml (monthly finalized issue) — CDC retired this feed ~2025.
  0.2.0: ahead-of-print.xml — CDC's primary EID pre-publication feed, confirmed
          200 at 4 KB on 2026-05-13. Overlaps with cdc-eid-ahead (upcoming.xml)
          on most items; content_topic_hash cross-source dedup links them.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class CDCEIDConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "cdc-eid"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://wwwnc.cdc.gov/eid/rss/ahead-of-print.xml"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "hantaan",
        "htnv",
        "seoul virus",
        "seov",
        "dobrava",
        "dobv",
        "orthohantavirus",
    ]
