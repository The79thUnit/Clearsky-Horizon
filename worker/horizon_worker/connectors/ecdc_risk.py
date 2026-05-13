"""ECDC Rapid Risk Assessments RSS connector. NATO A2.

ECDC publishes Rapid Risk Assessments (RRA) when novel or unexpected
public health events require an EU-level scientific assessment.
RRAs are high-signal publications: when hantavirus appears in one, it
means ECDC has assessed it as a significant EU-level threat.

Example relevance:
  During the 2026 MV Hondius ANDV cruise-ship cluster, ECDC published
  an RRA covering the probability of secondary spread in repatriated
  European passengers -- exactly the kind of alert this feed targets.

URL history:
  0.1.0: https://www.ecdc.europa.eu/en/taxonomy/term/1295/feed
         Confirmed 200, RSS 2.0, 10 items, 2026-05-13.
         Separate from ecdc-cdtr (which uses the broader publications
         feed at /taxonomy/term/1244). Content-topic dedup handles
         any overlap in the ingest pipeline.

NATO A2: official EU public health agency. RRAs are peer-reviewed
internally and represent the highest-confidence ECDC signal.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ECDCRiskConnector(RSSConnectorBase):
    """ECDC Rapid Risk Assessments feed."""

    SOURCE_CODE: ClassVar[str] = "ecdc-risk"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = "https://www.ecdc.europa.eu/en/taxonomy/term/1295/feed"
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
