"""UK Health Security Agency news (via GOV.UK) Atom feed.

Official UK public-health authority (successor to PHE). Atom feed for all
UKHSA-tagged announcements on gov.uk. NATO A1.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class UKHSAConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "ukhsa"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    FEED_URL: ClassVar[str] = (
        "https://www.gov.uk/government/organisations/uk-health-security-agency.atom"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "rodent-borne",
        "puumala",
        "seoul virus",
        "dobrava",
    ]
