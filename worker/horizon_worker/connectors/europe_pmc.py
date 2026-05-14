"""Europe PMC REST API connector. Peer-reviewed + preprint life-sciences literature.

Documented at https://europepmc.org/RestfulWebService.
Returns JSON when format=json is set.

NATO A1 for peer-reviewed records (resultType=core has peer-review flag).
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import (
    detect_country,
    detect_serotype,
    extract_region,
    parse_date_safe,
)
from .types import ParsedItem


class EuropePMCConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "europe-pmc"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    # 14 May 2026: simplified query string. The previous form with quoted
    # phrases ('"Andes virus"') was URL-encoded by httpx in a way Europe PMC's
    # query parser rejected, returning only {"version":"6.9"} on every call.
    # Plain "hantavirus" yields ~13k hits; the local KEYWORDS filter below
    # pulls out the serotype-tagged ones.
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "query": "hantavirus",
        "format": "json",
        "pageSize": "50",
        # No `sort` param: when httpx URL-encodes 'date desc' as 'date+desc',
        # Europe PMC's query parser rejects the whole request and returns
        # only {"version":"6.9"}. Default relevance ordering is acceptable
        # since we content_topic_hash-dedupe downstream.
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("resultList", "result")
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
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
    ]

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("title", "")).strip()
        abstract = str(item.get("abstractText", ""))
        pmid = item.get("pmid")
        doi = item.get("doi")
        epmcid = item.get("id")

        if doi:
            link = f"https://doi.org/{doi}"
        elif pmid:
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        elif epmcid:
            link = f"https://europepmc.org/article/MED/{epmcid}"
        else:
            link = ""

        external_id = f"europepmc:{pmid or doi or epmcid or title[:80]}"

        date_str = item.get("firstPublicationDate") or item.get("electronicPublicationDate") or ""
        reported: date | None = parse_date_safe(date_str, "%Y-%m-%d")

        haystack = f"{title} {abstract}"
        country = detect_country(haystack)
        region = extract_region(title)
        serotype = detect_serotype(haystack)

        canonical = "\n".join([str(epmcid or ""), str(pmid or ""), title, date_str]).encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=abstract[:600] if abstract else None,
            country_iso2=country,
            region=region,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=link,
            raw_content=canonical,
        )
