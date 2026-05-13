"""arXiv Atom feed connector (preprints, mostly q-bio).

NATO B2 (usually reliable, probably true). Preprints precede peer review.
"""

from __future__ import annotations

from typing import ClassVar

from .rss_base import RSSConnectorBase


class ArxivConnector(RSSConnectorBase):
    SOURCE_CODE: ClassVar[str] = "arxiv"
    # 0.1.0: http://export.arxiv.org/api/query — HTTP; export.arxiv.org no
    #         longer listens on port 80, producing status_code=0 from OVH VPS.
    # 0.2.0: https:// — TLS required; confirmed 200, valid Atom, 2026-05-13.
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    FEED_URL: ClassVar[str] = (
        "https://export.arxiv.org/api/query?"
        "search_query=all:hantavirus+OR+all:%22Andes+virus%22"
        "&sortBy=submittedDate&sortOrder=descending&max_results=50"
    )
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "andes virus",
        "sin nombre",
        "puumala",
        "hantaan",
    ]
