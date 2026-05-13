"""PubMed E-utilities connector.

NCBI's biomedical literature database. We use esearch to find recent
hantavirus-tagged PMIDs, then esummary for metadata. Each PMID becomes one
ParsedItem. No API key required for low-volume polling (<3 req/sec).

Documented at https://www.ncbi.nlm.nih.gov/books/NBK25497/.

NATO A1 (peer-reviewed). Sort by reverse date so new papers surface first.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, ClassVar

import httpx

from .base import BaseConnector
from .text_utils import (
    detect_country,
    detect_serotype,
    extract_region,
    parse_date_safe,
)
from .types import ParsedItem


class PubMedConnector(BaseConnector):
    SOURCE_CODE: ClassVar[str] = "pubmed"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    ESEARCH: ClassVar[str] = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY: ClassVar[str] = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    # PubMed query: tag both MeSH ("hantavirus" + "hantavirus infections") and free
    # text so we catch papers that use the new orthohantavirus genus name.
    QUERY: ClassVar[str] = (
        '("Orthohantavirus"[MeSH] OR "Hantavirus Infections"[MeSH] '
        'OR hantavirus[Title/Abstract] OR "andes virus"[Title/Abstract] '
        'OR "sin nombre virus"[Title/Abstract] OR "puumala virus"[Title/Abstract])'
    )
    MAX_RESULTS: ClassVar[int] = 50

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        # Step 1: esearch returns a list of PMIDs sorted by reverse date.
        search_params = {
            "db": "pubmed",
            "term": self.QUERY,
            "retmax": str(self.MAX_RESULTS),
            "retmode": "json",
            "sort": "pub_date",
        }
        sr = await client.get(self.ESEARCH, params=search_params)
        sr.raise_for_status()
        sdata = json.loads(sr.content.decode("utf-8"))
        ids: list[str] = sdata.get("esearchresult", {}).get("idlist", []) or []
        if not ids:
            return b'{"result":{"uids":[]}}', sr.status_code

        # Step 2: esummary returns metadata for those PMIDs.
        summary_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        ur = await client.get(self.ESUMMARY, params=summary_params)
        ur.raise_for_status()
        return ur.content, ur.status_code

    def parse(self, raw: bytes) -> list[ParsedItem]:
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return []
        result = data.get("result", {})
        uids: list[str] = result.get("uids", []) or []

        out: list[ParsedItem] = []
        for pmid in uids:
            doc = result.get(pmid)
            if not isinstance(doc, dict):
                continue
            parsed = self._parse_doc(pmid, doc)
            if parsed is not None:
                out.append(parsed)
        return out

    @staticmethod
    def _parse_doc(pmid: str, doc: dict[str, Any]) -> ParsedItem | None:
        title = str(doc.get("title", "")).strip()
        # PubMed summary doesn't expose abstract, only title + authors + journal
        # + date. Abstract requires efetch (which we skip to keep volume low).
        journal = str(doc.get("fulljournalname") or doc.get("source") or "")
        authors_field = doc.get("authors") or []
        authors_str = ""
        if isinstance(authors_field, list):
            names = [a.get("name", "") for a in authors_field if isinstance(a, dict)]
            authors_str = ", ".join(filter(None, names))
        date_str = str(doc.get("pubdate") or "")
        reported: date | None = (
            parse_date_safe(date_str, "%Y %b %d")
            or parse_date_safe(date_str, "%Y %b")
            or parse_date_safe(date_str, "%Y")
        )

        # DOI for stable link, fall back to PMID URL
        articleids = doc.get("articleids") or []
        doi = ""
        if isinstance(articleids, list):
            for entry in articleids:
                if isinstance(entry, dict) and entry.get("idtype") == "doi":
                    doi = str(entry.get("value", "")).strip()
                    break
        link = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        summary = f"{journal}. {authors_str}." if journal or authors_str else None

        haystack = f"{title} {summary or ''}"
        country = detect_country(haystack)
        region = extract_region(title)
        serotype = detect_serotype(haystack)

        canonical = "\n".join([pmid, title, date_str, doi]).encode("utf-8")

        return ParsedItem(
            external_id=f"pubmed:{pmid}",
            title=title,
            summary=summary,
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
