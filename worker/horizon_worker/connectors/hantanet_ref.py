"""CDC HantaNet — Orthohantavirus RefSeq reference genome connector.

Fetches ALL Orthohantavirus RefSeq nucleotide records from NCBI E-utilities
(no reldate filter). This builds the static genomic reference layer derived
from the HantaNet reference genome set (CDCgov/HantaNet, PMC10675615).

HantaNet is a MicrobeTrace visualisation tool published by the CDC Molecular
Epidemiology and Bioinformatics Team (Viruses MDPI, November 2023). The 41
reference genomes it ships are stored in a proprietary .microbetrace binary
workspace; NCBI GenBank RefSeq is the canonical source of those same sequences.

Distinct from ncbi-virus (migration 038) which fetches RECENT sequences with
reldate=14 days for molecular confirmation of the active outbreak. This
connector fetches the full historical RefSeq set (~200-300 records covering
S/M/L segments for all major serotypes) as a permanent annotation layer.

NATO: A1 (NCBI RefSeq is US federal genomic data infrastructure).
provenance_type: sequence-record. Tier 2.
Beat: 07:47 UTC daily (RefSeq reference sequences update infrequently).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import ClassVar

import httpx

from .base import BaseConnector, FetchResult
from .types import ParsedItem

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Full Orthohantavirus RefSeq set — no reldate, permanent reference layer.
# refseq[filter] keeps only NM_/NC_/NR_-prefixed curated reference sequences.
_ESEARCH_PARAMS: dict[str, str | int] = {
    "db": "nucleotide",
    "term": "Orthohantavirus[Organism] AND refseq[filter]",
    "usehistory": "y",
    "retmode": "json",
    "retmax": 500,
}

# Fetch summaries 200 at a time (NCBI documented maximum for esummary).
_SUMMARY_BATCH = 200

# Organism substring → serotype code (lower-case key, substring match).
# NCBI uses "Andes orthohantavirus", "Sin Nombre orthohantavirus", etc.
# since the 2016 ICTV reclassification of the Hantaviridae family.
_ORGANISM_SEROTYPE: dict[str, str] = {
    "andes": "ANDV",
    "sin nombre": "SNV",
    "puumala": "PUUV",
    "hantaan": "HTNV",
    "seoul": "SEOV",
    "dobrava": "DOBV",
    "bayou": "BAYV",
    "black creek canal": "BCCV",
    "laguna negra": "LANV",
    "choclo": "CHOV",
    "saaremaa": "SAAV",
    "tula": "TULV",
}

# Default geographic centroid for each serotype's primary endemic region.
# Used for lat/lng when country-of-isolation is absent from the docsum.
_SEROTYPE_COORDS: dict[str, tuple[float, float]] = {
    "ANDV": (-38.0, -72.0),   # South-central Chile / Patagonia
    "SNV": (37.0, -96.0),     # Continental USA
    "PUUV": (64.0, 26.0),     # Finland / Scandinavia
    "HTNV": (38.0, 128.0),    # East Asia (Korea/China border region)
    "SEOV": (0.0, 0.0),       # Global (Rattus norvegicus, worldwide)
    "DOBV": (44.0, 20.0),     # Balkans
    "BAYV": (30.0, -91.0),    # Louisiana / lower Mississippi basin
    "BCCV": (25.5, -80.5),    # Florida, USA
    "LANV": (-20.0, -60.0),   # Paraguay / western Bolivia
    "CHOV": (8.0, -80.0),     # Panama
    "SAAV": (58.0, 22.0),     # Estonia / Northern Europe
    "TULV": (49.0, 16.5),     # Czech Republic / Central Europe
}

# Genome segment tokens in NCBI record titles.
_SEGMENT_PATTERNS: list[tuple[str, str]] = [
    ("segment s", "S"),
    ("segment m", "M"),
    ("segment l", "L"),
    ("s segment", "S"),
    ("m segment", "M"),
    ("l segment", "L"),
    ("small segment", "S"),
    ("medium segment", "M"),
    ("large segment", "L"),
]

# Country string → ISO2 for NCBI BioSource country fields.
# Covers the full endemic range of the 12 tracked serotypes.
_COUNTRY_ISO2: dict[str, str] = {
    "argentina": "AR",
    "austria": "AT",
    "belgium": "BE",
    "bolivia": "BO",
    "bosnia and herzegovina": "BA",
    "brazil": "BR",
    "bulgaria": "BG",
    "canada": "CA",
    "chile": "CL",
    "china": "CN",
    "croatia": "HR",
    "czech republic": "CZ",
    "denmark": "DK",
    "estonia": "EE",
    "finland": "FI",
    "france": "FR",
    "germany": "DE",
    "greece": "GR",
    "hungary": "HU",
    "japan": "JP",
    "korea": "KR",
    "south korea": "KR",
    "latvia": "LV",
    "lithuania": "LT",
    "netherlands": "NL",
    "north macedonia": "MK",
    "norway": "NO",
    "panama": "PA",
    "paraguay": "PY",
    "peru": "PE",
    "poland": "PL",
    "romania": "RO",
    "russia": "RU",
    "serbia": "RS",
    "slovakia": "SK",
    "slovenia": "SI",
    "sweden": "SE",
    "thailand": "TH",
    "ukraine": "UA",
    "united states": "US",
    "usa": "US",
    "uruguay": "UY",
    "venezuela": "VE",
}


def _resolve_serotype(organism: str) -> str | None:
    """Map NCBI organism name to our serotype registry code."""
    lower = organism.strip().lower()
    for key, code in _ORGANISM_SEROTYPE.items():
        if key in lower:
            return code
    return None


def _extract_segment(title: str) -> str | None:
    """Extract genome segment (S/M/L) from NCBI record title."""
    lower = title.lower()
    for pattern, seg in _SEGMENT_PATTERNS:
        if pattern in lower:
            return seg
    return None


def _parse_date(raw: str) -> date | None:
    """Parse NCBI date strings: 'YYYY/MM/DD', 'YYYY/MM', 'YYYY'."""
    if not raw:
        return None
    normalised = raw.strip().replace("/", "-")
    for fmt_len in (10, 7, 4):
        fragment = normalised[:fmt_len]
        try:
            if fmt_len == 10:
                return date.fromisoformat(fragment)
            if fmt_len == 7:
                # YYYY-MM → first of month
                y, m = fragment.split("-")
                return date(int(y), int(m), 1)
            if fmt_len == 4:
                return date(int(fragment), 1, 1)
        except ValueError:
            continue
    return None


def _country_from_extra(extra: str) -> str | None:
    """Extract ISO2 from the NCBI docsum 'extra' field.

    The extra field is a pipe-delimited string that sometimes embeds
    '[Country]' qualifiers for GenBank/RefSeq records, e.g.:
      'gi|12345|ref|NC_005217.1|[Finland]'
    We try to match any bracketed token against our country map.
    """
    if not extra:
        return None
    for token in extra.replace("|", " ").split():
        cleaned = token.strip("[]").lower()
        if cleaned in _COUNTRY_ISO2:
            return _COUNTRY_ISO2[cleaned]
    return None


class HantaNetRefConnector(BaseConnector):
    """Fetch the full Orthohantavirus RefSeq reference genome set via NCBI E-utilities.

    Source: NCBI GenBank RefSeq (the sequence data cited by the HantaNet tool).
    Fetches ALL records (no reldate filter) to build a static annotation layer
    that does not overlap with ncbi-virus (which uses reldate=14 days).
    """

    SOURCE_CODE: ClassVar[str] = "cdc-hantanet-ref"
    PARSER_VERSION: ClassVar[str] = "0.1.0"

    async def run(self) -> FetchResult:
        start = datetime.now(tz=UTC)
        try:
            async with httpx.AsyncClient(
                timeout=60,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                # Step 1 — esearch: get WebEnv + query_key for history server.
                esearch_resp = await client.get(_ESEARCH_URL, params=_ESEARCH_PARAMS)
                if esearch_resp.status_code in {429, 502, 503, 504}:
                    return FetchResult(
                        source_code=self.SOURCE_CODE,
                        parser_version=self.PARSER_VERSION,
                        http_status=esearch_resp.status_code,
                        latency_ms=int(
                            (datetime.now(tz=UTC) - start).total_seconds() * 1000
                        ),
                        items_seen=0, items=[], items_filtered=0, error=None,
                    )
                esearch_resp.raise_for_status()
                esearch_result = esearch_resp.json().get("esearchresult", {})

                total = int(esearch_result.get("count", 0))
                web_env = esearch_result.get("webenv", "")
                query_key = esearch_result.get("querykey", "1")

                if not total or not web_env:
                    latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
                    return FetchResult(
                        source_code=self.SOURCE_CODE,
                        parser_version=self.PARSER_VERSION,
                        http_status=200,
                        latency_ms=latency,
                        items_seen=0, items=[], items_filtered=0,
                        error="esearch returned 0 results",
                    )

                # Step 2 — esummary: fetch docsum records in batches.
                all_docs: list[dict] = []
                retstart = 0
                while retstart < total:
                    summary_resp = await client.get(
                        _ESUMMARY_URL,
                        params={
                            "db": "nucleotide",
                            "query_key": query_key,
                            "WebEnv": web_env,
                            "retstart": retstart,
                            "retmax": _SUMMARY_BATCH,
                            "retmode": "json",
                        },
                    )
                    summary_resp.raise_for_status()
                    result_block = summary_resp.json().get("result", {})
                    for uid in result_block.get("uids", []):
                        doc = result_block.get(uid)
                        if doc:
                            all_docs.append(doc)
                    retstart += _SUMMARY_BATCH

            items = self._parse_docs(all_docs)
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=200,
                latency_ms=latency,
                items_seen=len(items),
                items=items,
                items_filtered=0,
                error=None,
            )

        except Exception as exc:
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            logger.exception("HantaNet RefSeq fetch failed")
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=None,
                latency_ms=latency,
                items_seen=0, items=[], items_filtered=0, error=str(exc),
            )

    def _parse_docs(self, docs: list[dict]) -> list[ParsedItem]:
        """Convert NCBI esummary docsum records to ParsedItems.

        One ParsedItem per RefSeq accession. case_count is None (no case
        data — this is a genomic reference layer). death_count is 0.
        Dedup key is the accession number, so re-fetching the same set is
        idempotent via the source_id/external_id PK.
        """
        items: list[ParsedItem] = []
        seen: set[str] = set()

        for doc in docs:
            # caption holds the version-stripped accession (NC_005217).
            # acccessionversion holds NC_005217.1 — use caption for stable key.
            accession = doc.get("caption", "").strip()
            if not accession or accession in seen:
                continue
            seen.add(accession)

            title = doc.get("title", "").strip()
            organism = doc.get("organism", "").strip()
            create_date = doc.get("createdate", "")
            update_date = doc.get("updatedate", "")
            extra = doc.get("extra", "") or ""

            serotype_text = _resolve_serotype(organism)
            segment = _extract_segment(title)

            # Reported date: prefer createdate.
            reported = _parse_date(create_date) or _parse_date(update_date)

            # Country: try extra field first, then fall back to None.
            # Genomic reference records rarely have country in the docsum.
            country_iso2 = _country_from_extra(extra)

            # Coordinates: serotype default centroid.
            lat: float | None = None
            lng: float | None = None
            if serotype_text and serotype_text in _SEROTYPE_COORDS:
                lat, lng = _SEROTYPE_COORDS[serotype_text]

            # Structured title: "RefSeq NC_005217 (ANDV) [S-segment] — Andes orthohantavirus"
            sero_label = f" ({serotype_text})" if serotype_text else ""
            seg_label = f" [{segment}-segment]" if segment else ""
            item_title = (
                f"RefSeq {accession}{sero_label}{seg_label}"
                f" — {organism or 'Orthohantavirus spp.'}"
            )

            summary_parts: list[str] = [
                f"NCBI RefSeq {accession}: {title}.",
                f"Organism: {organism}." if organism else "",
                f"Serotype: {serotype_text}." if serotype_text else "",
                f"Genome segment: {segment}." if segment else "",
                f"Deposited: {reported.isoformat()}." if reported else "",
                (
                    "HantaNet CDC reference genome set. "
                    "Published by CDC Molecular Epidemiology and Bioinformatics Team "
                    "in Viruses (MDPI) November 2023 (PMC10675615). "
                    "Apache 2.0 + CC0. NCBI RefSeq curated reference sequence. "
                    "Covers S/M/L segments for all major Orthohantavirus serotypes."
                ),
            ]

            external_id = f"cdc-hantanet-ref:{accession}"
            canonical_content = (
                f"{external_id}\n{accession}\n{organism}\n{title}"
            ).encode()

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=item_title,
                    summary=" ".join(p for p in summary_parts if p),
                    country_iso2=country_iso2,
                    region=None,
                    lat=lat,
                    lng=lng,
                    serotype_text=serotype_text,
                    reported_date=reported,
                    case_count=None,   # Genomic reference: no case count
                    death_count=0,
                    raw_url=f"https://www.ncbi.nlm.nih.gov/nuccore/{accession}",
                    raw_content=canonical_content,
                )
            )

        return items
