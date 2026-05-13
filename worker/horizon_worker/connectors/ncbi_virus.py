"""NCBI GenBank orthohantavirus sequence-record connector.

Two-step E-utilities fetch: esearch returns GI/accession IDs for recent
orthohantavirus submissions; esummary returns the metadata record per
accession (title, organism, host, country, collection date, segment,
isolate name).

Why this matters for HORIZON:

  * Genome submissions to GenBank are the molecular confirmation layer.
    A case that appears in news sources as "suspected hantavirus" gets
    elevated to confirmed once a full ANDV/HTNV/PUUV/SEOV sequence is
    deposited. The Swiss MV Hondius case (Hu-3337/2026) landed as
    PZ385161-163 on 2026-05-11 — three segments, all annotated
    Homo sapiens / Switzerland / 2026-05-04.

  * GenBank submissions precede formal WHO DON updates. Labs deposit
    sequences before the patient count is officially confirmed, giving
    HORIZON an early-warning 24-72h lead on geographic spread.

  * Isolate naming carries epidemiological signal.
    `ANDV/Switzerland/Hu-3337/2026` tells us: ANDV serotype,
    Switzerland, human patient, reference 3337, 2026.
    HORIZON's extractor reads this to infer country and serotype
    without waiting for an analyst to review.

Deduplication: GenBank deposits one record per segment (S/M/L for
tri-segmented orthohantaviruses). This connector keeps ONE record per
isolate (the L-segment / complete genome where available, else M, else
S) to avoid tripling the case count in the DB.

Fetch window: `reldate=14` (last 14 days, publication date). At the
current ANDV cluster submission rate this returns 20-60 records / fetch.

NATO rating: A1 (completely reliable, confirmed by definition — the
sequence submission IS primary molecular evidence, not commentary on it).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import ClassVar

import httpx

from .base import BaseConnector, FetchResult
from .text_utils import detect_serotype
from .types import ParsedItem

logger = logging.getLogger(__name__)

# Preferred segment priority for dedup: keep the most complete record.
_SEGMENT_PRIORITY: dict[str, int] = {"L": 0, "M": 1, "S": 2}

# Map GenBank 3-char ISO country strings (mostly INSDC standard) to ISO-2.
# Only the ones likely to appear in MV Hondius / endemic ANDV coverage.
# For everything else we fall through to detect_country() or leave None.
_COUNTRY_TO_ISO2: dict[str, str] = {
    "Switzerland": "CH",
    "Argentina": "AR",
    "Chile": "CL",
    "Brazil": "BR",
    "Paraguay": "PY",
    "Bolivia": "BO",
    "Peru": "PE",
    "USA": "US",
    "Canada": "CA",
    "Germany": "DE",
    "France": "FR",
    "Netherlands": "NL",
    "United Kingdom": "GB",
    "China": "CN",
    "Japan": "JP",
    "South Korea": "KR",
    "South Africa": "ZA",
    "Finland": "FI",
    "Sweden": "SE",
    "Russia": "RU",
    "Ukraine": "UA",
    "Hungary": "HU",
    "Czech Republic": "CZ",
    "Slovakia": "SK",
    "Austria": "AT",
    "Belgium": "BE",
    "Denmark": "DK",
    "Norway": "NO",
    "Croatia": "HR",
    "Slovenia": "SI",
    "Thailand": "TH",
    "Laos": "LA",
    "Cambodia": "KH",
    "Vietnam": "VN",
    "India": "IN",
}

# Map from NCBI organism name (prefix-match) to our serotype code.
_ORGANISM_TO_SEROTYPE: dict[str, str] = {
    "Orthohantavirus andesense": "ANDV",
    "Orthohantavirus sinnombreense": "SNV",
    "Orthohantavirus puumalaense": "PUUV",
    "Orthohantavirus hantanense": "HTNV",
    "Orthohantavirus seoulense": "SEOV",
    "Orthohantavirus dobravaense": "DOBV",
    "Orthohantavirus tulaense": "TULV",
    "Orthohantavirus murinae": "SEOV",   # historical synonym
    "Orthohantavirus laguna-negraense": "LANV",
    "Orthohantavirus bayouvirusense": "BAYV",
    "Orthohantavirus blackcreekcanalense": "BCCV",
    "Orthohantavirus newyorkense": "NYV",
    "Andes virus": "ANDV",              # older name still used by some submitters
    "Sin Nombre virus": "SNV",
    "Puumala virus": "PUUV",
    "Hantaan virus": "HTNV",
    "Seoul virus": "SEOV",
    "Dobrava-Belgrade virus": "DOBV",
}

# E-utilities base
_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _serotype_from_organism(organism: str) -> str | None:
    """Resolve NCBI organism name → HORIZON serotype code."""
    for prefix, code in _ORGANISM_TO_SEROTYPE.items():
        if organism.lower().startswith(prefix.lower()):
            return code
    # Fall back to keyword scan
    return detect_serotype(organism)


def _parse_subfields(subname: str, subtype: str) -> dict[str, str]:
    """Split NCBI pipe-delimited subname/subtype fields into a lookup."""
    names = subname.split("|")
    types = subtype.split("|")
    out: dict[str, str] = {}
    for typ, val in zip(types, names):
        out[typ.strip()] = val.strip()
    return out


def _country_to_iso2(country_str: str) -> str | None:
    """Convert NCBI country field (may include region: 'USA: California') to ISO-2."""
    base = country_str.split(":")[0].strip()
    return _COUNTRY_TO_ISO2.get(base)


class NCBIVirusConnector(BaseConnector):
    """Sequence-record connector for NCBI GenBank orthohantavirus submissions.

    Lifecycle differs from RSS/JSON-API connectors: two sequential GET
    requests (esearch → esummary) before parse. We override run() via the
    base class's curl_cffi skip (no FEED_URL/ENDPOINT class var) so both
    steps go through the httpx async client path.
    """

    SOURCE_CODE: ClassVar[str] = "ncbi-virus"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    KEYWORDS: ClassVar[list[str]] = []  # All returned records are orthohantavirus

    _SEARCH_TERM: ClassVar[str] = "orthohantavirus[organism]"
    _RELDATE: ClassVar[int] = 14           # look back this many days
    _PAGE_SIZE: ClassVar[int] = 100        # accessions per esummary batch

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        """Two-step E-utilities fetch: esearch → esummary."""
        # Step 1: esearch — get a list of GI IDs matching recent
        # orthohantavirus submissions.
        esearch_resp = await client.get(
            f"{_EUTILS}/esearch.fcgi",
            params={
                "db": "nuccore",
                "term": self._SEARCH_TERM,
                "retmode": "json",
                "retmax": str(self._PAGE_SIZE),
                "sort": "date",
                "reldate": str(self._RELDATE),
                "datetype": "pdat",
            },
        )
        if esearch_resp.status_code != 200:
            return b"", esearch_resp.status_code

        esearch_data = esearch_resp.json()
        ids: list[str] = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return b'{"result":{"uids":[]}}', 200

        # Step 2: esummary — get metadata for each ID.
        esummary_resp = await client.get(
            f"{_EUTILS}/esummary.fcgi",
            params={
                "db": "nuccore",
                "id": ",".join(ids),
                "retmode": "json",
            },
        )
        if esummary_resp.status_code != 200:
            return b"", esummary_resp.status_code

        return esummary_resp.content, 200

    def parse(self, raw: bytes) -> list[ParsedItem]:
        """Parse esummary JSON into ParsedItems. Deduplicates by isolate."""
        import json as _json

        try:
            data: dict = _json.loads(raw.decode("utf-8"))
        except Exception:
            return []

        result = data.get("result", {})
        uids: list[str] = result.get("uids", [])
        if not uids:
            return []

        # Group by isolate name; keep best segment per isolate.
        # isolate_best: isolate → (priority, uid, rec)
        isolate_best: dict[str, tuple[int, str, dict]] = {}

        for uid in uids:
            rec = result.get(uid)
            if not isinstance(rec, dict):
                continue

            subname = rec.get("subname", "") or ""
            subtype = rec.get("subtype", "") or ""
            fields = _parse_subfields(subname, subtype)

            isolate = fields.get("isolate") or rec.get("title", uid)
            segment = fields.get("segment", "?")
            priority = _SEGMENT_PRIORITY.get(segment, 3)

            existing = isolate_best.get(isolate)
            if existing is None or priority < existing[0]:
                isolate_best[isolate] = (priority, uid, rec)

        items: list[ParsedItem] = []
        for isolate, (_, uid, rec) in isolate_best.items():
            item = self._build_item(uid, rec, isolate)
            if item is not None:
                items.append(item)

        return items

    def _build_item(self, uid: str, rec: dict, isolate: str) -> ParsedItem | None:
        subname = rec.get("subname", "") or ""
        subtype = rec.get("subtype", "") or ""
        fields = _parse_subfields(subname, subtype)

        organism = rec.get("organism", "") or ""
        serotype = _serotype_from_organism(organism)

        country_str = fields.get("country", "") or rec.get("country", "") or ""
        country_iso2 = _country_to_iso2(country_str) if country_str else None

        host = fields.get("host", "") or ""
        collection_date_str = fields.get("collection_date", "") or ""
        segment = fields.get("segment", "?")

        accession = rec.get("accessionversion", str(uid))
        title_raw = rec.get("title", "") or ""
        create_date_str = rec.get("createdate", "") or ""
        update_date_str = rec.get("updatedate", "") or ""

        # Parse reported date from collection_date or create_date
        reported: date | None = None
        for ds in (collection_date_str, update_date_str, create_date_str):
            if ds:
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%b-%Y", "%Y"):
                    try:
                        reported = datetime.strptime(ds[:10], fmt).date()
                        break
                    except ValueError:
                        continue
            if reported:
                break

        is_human = "sapiens" in host.lower() or "human" in host.lower()

        title = f"Sequence: {isolate} ({organism or 'orthohantavirus'})"
        if country_str:
            title += f" — {country_str}"

        geo_part = f"Country: {country_str}. " if country_str else ""
        host_part = f"Host: {host}. " if host else ""
        date_part = f"Collected: {collection_date_str}. " if collection_date_str else ""
        seg_part = f"Segment(s): {segment}. "
        summary = (
            f"GenBank accession {accession}. {geo_part}{host_part}"
            f"{date_part}{seg_part}"
            f"Deposited: {create_date_str}. "
            f"{'Human case — molecular confirmation.' if is_human else ''}"
        ).strip()

        canonical = "\n".join(
            [uid, accession, isolate, organism, country_str, collection_date_str, host]
        ).encode("utf-8")

        return ParsedItem(
            external_id=accession,
            title=title,
            summary=summary,
            country_iso2=country_iso2,
            region=country_str or None,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=f"https://www.ncbi.nlm.nih.gov/nuccore/{accession}",
            raw_content=canonical,
        )

    def filter_relevant(self, items: list[ParsedItem]) -> list[ParsedItem]:
        """All returned records are orthohantavirus by construction."""
        return items
