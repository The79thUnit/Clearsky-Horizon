"""GBIF (Global Biodiversity Information Facility) rodent-reservoir connector.

Pulls recent occurrence records for known hantavirus reservoir species from
museums, monitoring programmes and academic surveys. Lower-volume than
iNaturalist citizen science but typically higher pedigree (museum vouchers,
verified academic surveys). NATO B2.

Documented at https://www.gbif.org/developer/occurrence.

URL history:
  0.1.0: QUERY_PARAMS dict carried only taxonKey=2436895 (Peromyscus maniculatus,
          SNV host only). Four of five reservoir species were silently dropped.
  0.2.0: fetch_raw overrides to pass all five taxonKeys as repeated URL params
          via httpx list-of-tuples. curl_cffi path skipped (no WAF on api.gbif.org;
          httpx handles GBIF fine). All five reservoir hosts now polled per cycle:
          P. maniculatus (SNV), O. longicaudatus (ANDV), A. agrarius (HTNV),
          M. glareolus (PUUV), R. norvegicus (SEOV).
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

import httpx

from .json_api_base import JSONAPIConnectorBase
from .text_utils import parse_date_safe
from .types import ParsedItem

# GBIF taxonKeys for our five reservoir species. Resolved 2026-05.
_TAXA_TO_SEROTYPE: dict[int, str] = {
    2436895: "SNV",  # Peromyscus maniculatus
    2438009: "ANDV",  # Oligoryzomys longicaudatus
    2437394: "HTNV",  # Apodemus agrarius
    8260714: "PUUV",  # Myodes glareolus  (sometimes Clethrionomys glareolus)
    2439261: "SEOV",  # Rattus norvegicus
}


class GBIFConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "gbif"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://api.gbif.org/v1/occurrence/search"
    # QUERY_PARAMS is intentionally empty: fetch_raw builds repeated taxonKey
    # params as a list-of-tuples that httpx supports but dict[str,str] cannot.
    QUERY_PARAMS: ClassVar[dict[str, str]] = {}
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("results",)
    KEYWORDS: ClassVar[list[str]] = []

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        """Build repeated taxonKey params for all five reservoir species.

        GBIF occurrence search accepts taxonKey as a repeated query parameter
        (taxonKey=A&taxonKey=B&...). httpx supports this via list-of-tuples.
        The base-class QUERY_PARAMS dict cannot express repeated keys.
        """
        params: list[tuple[str, str]] = [
            ("taxonKey", str(k)) for k in _TAXA_TO_SEROTYPE
        ] + [("limit", "50")]
        response = await client.get(
            self.ENDPOINT,
            params=params,
            headers={"accept": "application/json"},
        )
        if response.status_code in self._TRANSIENT_STATUSES:
            return b"", response.status_code
        response.raise_for_status()
        return response.content, response.status_code

    async def _run_via_curl_cffi(self, cffi_module: object) -> None:
        """Skip curl_cffi for GBIF.

        api.gbif.org has no Cloudflare/Akamai WAF, so there is no fingerprint
        benefit. More importantly: QUERY_PARAMS is empty (the multi-taxonKey
        list lives only in fetch_raw), so the curl_cffi path would send a
        bare GET to the endpoint and return unsorted global occurrences.
        Returning None here falls through to the httpx path in BaseConnector.run().
        """
        return None  # type: ignore[return-value]

    def filter_relevant(self, items: list[ParsedItem]) -> list[ParsedItem]:
        # Already filtered by taxonKey at the API; skip keyword filter.
        return items

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        occ_id = item.get("key")
        if occ_id is None:
            return None
        taxon_key = item.get("taxonKey") or item.get("acceptedTaxonKey")
        species_name = str(item.get("species") or item.get("scientificName") or "")
        serotype: str | None = None
        if isinstance(taxon_key, int):
            serotype = _TAXA_TO_SEROTYPE.get(taxon_key)

        country_code = item.get("countryCode")
        country_iso2: str | None = str(country_code).upper()[:2] if country_code else None
        locality = str(item.get("locality") or item.get("stateProvince") or "")

        event_date_str = str(item.get("eventDate") or "")
        reported: date | None = (
            parse_date_safe(event_date_str[:10], "%Y-%m-%d") if event_date_str else None
        )

        lat_raw = item.get("decimalLatitude")
        lng_raw = item.get("decimalLongitude")
        lat: float | None = None
        lng: float | None = None
        try:
            if lat_raw is not None:
                lat = float(lat_raw)
            if lng_raw is not None:
                lng = float(lng_raw)
        except (TypeError, ValueError):
            pass

        title = (
            f"Reservoir record: {species_name} "
            f"({locality or country_iso2 or 'unknown locality'})"
        )
        summary = (
            f"GBIF occurrence record of {species_name}, a known reservoir for "
            f"{serotype or 'orthohantavirus'}. Source dataset: "
            f"{item.get('datasetName', 'GBIF')}."
        )

        canonical = "\n".join(
            [
                str(occ_id),
                species_name,
                event_date_str,
                country_iso2 or "",
                locality,
            ]
        ).encode("utf-8")

        return ParsedItem(
            external_id=f"gbif:{occ_id}",
            title=title,
            summary=summary,
            country_iso2=country_iso2,
            region=locality or None,
            lat=lat,
            lng=lng,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=f"https://www.gbif.org/occurrence/{occ_id}",
            raw_content=canonical,
        )
