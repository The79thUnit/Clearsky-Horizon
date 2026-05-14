"""mBio (American Society for Microbiology) — Crossref-proxied.

14 May 2026 rewrite: journals.asm.org is behind a Cloudflare WAF that
blocks direct fetches (403 with Chrome 120 impersonation). We pull the
same DOI-resolved article set from Crossref, ISSN-filtered to 2150-7511
(mBio's electronic ISSN). NATO A1 peer-reviewed.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .eurosurveillance import EurosurveillanceConnector


class MBioConnector(EurosurveillanceConnector):
    SOURCE_CODE: ClassVar[str] = "mbio"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://api.crossref.org/journals/2150-7511/works"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "rows": "50",
    }

    def parse_item(self, item: dict[str, Any]):  # type: ignore[override]
        parsed = super().parse_item(item)
        if parsed is None:
            return None
        # Rewrite the external_id namespace from "eurosurveillance:" -> "mbio:".
        ext = parsed.external_id.replace("eurosurveillance:", "mbio:", 1)
        return parsed.__class__(
            external_id=ext,
            title=parsed.title,
            summary=parsed.summary,
            country_iso2=parsed.country_iso2,
            region=parsed.region,
            lat=parsed.lat,
            lng=parsed.lng,
            serotype_text=parsed.serotype_text,
            reported_date=parsed.reported_date,
            case_count=parsed.case_count,
            death_count=parsed.death_count,
            raw_url=parsed.raw_url,
            raw_content=parsed.raw_content,
        )
