"""ECDC Epidemiological Updates RSS connector. NATO A2.

ECDC publishes Epidemiological Updates (EU) providing regular
surveillance summaries for pathogens of EU concern. Unlike the
CDTR weekly (ecdc-cdtr), epidemiological updates are pathogen-
specific documents published when new case data warrants an update.

Example items: "MERS-CoV worldwide overview" (2026-05-11).
For hantavirus, an ECDC epidemiological update would represent
a significant EU-level summary of case counts and geographic spread
-- high-value signal for the outbreak timeline.

URL history:
  0.1.0: https://www.ecdc.europa.eu/en/taxonomy/term/1310/feed
         Confirmed 200, RSS 2.0, 10 items, 2026-05-13.
         First item: "MERS-CoV worldwide overview" (2026-05-11).
         Separate sub-feed from ecdc-cdtr and ecdc-risk; dedup
         handles any content overlap in the ingest pipeline.

NATO A2: official EU public health agency. Epidemiological updates
are authoritative EU-wide surveillance summaries.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ECDCEpidUpdatesConnector(RSSConnectorBase):
    """ECDC Epidemiological Updates feed."""

    SOURCE_CODE: ClassVar[str] = "ecdc-updates"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.ecdc.europa.eu/en/taxonomy/term/1310/feed"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "puuv",
        "andes virus",
        "andv",
        "dobrava",
        "seoul virus",
        "seov",
        "hantaan",
        "htnv",
        "orthohantavirus",
        "rodent-borne",
        "zoonotic",
        # Cruise-ship cluster context
        "hondius",
        "cruise ship",
    ]
