"""One Health (Elsevier) journal RSS connector.

One Health is an Elsevier-published, open-access peer-reviewed journal
(ISSN 2352-7714) covering the human/animal/environment interface:
zoonotic spillover, vector-borne disease, AMR at the interface,
ecological drivers of emergence. Directly relevant to HORIZON's
hantavirus surveillance brief because:

  * Hantaviruses are reservoir-host pathogens (Peromyscus, Oligoryzomys,
    Apodemus, Rattus). One Health regularly publishes rodent-ecology +
    serosurvey papers that establish baseline prevalence and warn of
    range shifts before a human cluster appears.
  * Bat / rodent / livestock spillover papers in One Health frequently
    cover hantavirus alongside other agents — strong cross-corroboration
    signal for our extractor.

Verified 2026-05-13: feed at https://rss.sciencedirect.com/publication/
science/23527714 returns 200 with 63 KB Atom XML, 100 most-recent items
(Elsevier RSS exposes the full current TOC + ahead-of-print).

NATO rating: A2 (completely reliable source category — peer-reviewed
journal indexed in PubMed; individual paper claims need replication
hence credibility=2 not 1). Higher than CIDRAP commentary (A2->B2)
because peer-reviewed; lower than Eurosurveillance / EID which are
public-health-agency-published (A1).
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class OneHealthConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "one-health"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://rss.sciencedirect.com/publication/science/23527714"
    )
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
        # Reservoir-host genera — these papers often establish the
        # ecological baseline before a human cluster surfaces.
        "peromyscus",
        "oligoryzomys",
        "apodemus",
        # MV Hondius-specific so cruise-ship coverage surfaces even when
        # the title doesn't lead with a virus keyword.
        "hondius",
        "oceanwide",
        "cruise ship",
    ]
