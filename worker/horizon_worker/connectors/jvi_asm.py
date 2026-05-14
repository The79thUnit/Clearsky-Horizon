"""Journal of Virology (ASM) — Crossref-proxied.

14 May 2026 rewrite: journals.asm.org is WAF-blocked. We pull the same
article set via Crossref, ISSN-filtered to 0022-538X (Journal of Virology's
print ISSN). NATO A1 peer-reviewed.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .eurosurveillance import EurosurveillanceConnector


class JVIASMConnector(EurosurveillanceConnector):
    SOURCE_CODE: ClassVar[str] = "jvi-asm"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://api.crossref.org/journals/0022-538X/works"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "rows": "50",
    }

    def parse_item(self, item: dict[str, Any]):  # type: ignore[override]
        parsed = super().parse_item(item)
        if parsed is None:
            return None
        ext = parsed.external_id.replace("eurosurveillance:", "jvi-asm:", 1)
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
