"""ECDC Scientific and Technical Publications RSS connector.

Covers ECDC's full scientific/technical publication stream: Communicable
Disease Threats Reports (CDTR, weekly), Rapid Risk Assessments, Rapid
Scientific Advisories (including the 2026-05-13 MV Hondius RSA), and
peer-reviewed technical guidance. NATO A2.

URL history:
  0.1.0: /en/publications-data/rss.xml — 404 as of 2026-05-13 (ECDC CMS
          migration removed the generic publications feed).
  0.2.0: /en/taxonomy/term/1244/feed — ECDC taxonomy feed for "Scientific
          and technical publications". Confirmed 200 at 8 KB on 2026-05-13.
          Contains CDTR week 19 (2-8 May 2026) and MV Hondius RSA.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ECDCCDTRConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "ecdc-cdtr"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = "https://www.ecdc.europa.eu/en/taxonomy/term/1244/feed"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "puumala",
        "dobrava",
        "seoul virus",
        "hantaan",
        "orthohantavirus",
        "rodent-borne",
    ]
