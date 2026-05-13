"""iNaturalist rodent-reservoir observations connector.

Tracks recent verified observations of known hantavirus reservoirs:
Peromyscus maniculatus (SNV), Oligoryzomys longicaudatus (ANDV),
Apodemus agrarius (HTNV), Myodes glareolus (PUUV), Rattus norvegicus (SEOV).

Each observation gives time/location context for the host species
distribution; NOT a case report. NATO C3 (citizen-science verifiable).
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import parse_date_safe
from .types import ParsedItem

_TAXA_TO_SEROTYPE: dict[int, str] = {
    46259: "SNV",  # Peromyscus maniculatus (deer mouse)
    73375: "ANDV",  # Oligoryzomys longicaudatus (long-tailed pygmy rice rat)
    46289: "HTNV",  # Apodemus agrarius (striped field mouse)
    46261: "PUUV",  # Myodes glareolus (bank vole)
    46276: "SEOV",  # Rattus norvegicus (brown rat)
}

_TAXA_TO_NAME: dict[int, str] = {
    46259: "Peromyscus maniculatus",
    73375: "Oligoryzomys longicaudatus",
    46289: "Apodemus agrarius",
    46261: "Myodes glareolus",
    46276: "Rattus norvegicus",
}


class INaturalistConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "inaturalist"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    ENDPOINT: ClassVar[str] = "https://api.inaturalist.org/v1/observations"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        "taxon_id": "46259,73375,46289,46261,46276",
        "quality_grade": "research",
        "per_page": "50",
        "order_by": "observed_on",
        "order": "desc",
        "verifiable": "true",
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("results",)
    # Observations are reservoir-host events; don't keyword-filter on
    # hantavirus mentions (the post text rarely names the virus).
    KEYWORDS: ClassVar[list[str]] = []

    def filter_relevant(self, items: list[ParsedItem]) -> list[ParsedItem]:
        # All returned items are reservoir-host observations by construction
        # (taxon_id filter at the API). Skip the default keyword filter.
        return items

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        obs_id = item.get("id")
        if obs_id is None:
            return None
        taxon = item.get("taxon") or {}
        taxon_id = taxon.get("id")
        species_name = (
            _TAXA_TO_NAME.get(int(taxon_id), str(taxon.get("name", ""))) if taxon_id else ""
        )
        serotype = _TAXA_TO_SEROTYPE.get(int(taxon_id)) if taxon_id else None

        place_guess = str(item.get("place_guess") or "").strip()
        observed_on = str(item.get("observed_on") or "")
        reported: date | None = parse_date_safe(observed_on, "%Y-%m-%d")

        geojson = item.get("geojson") or {}
        coords = geojson.get("coordinates") if isinstance(geojson, dict) else None
        lat: float | None = None
        lng: float | None = None
        if isinstance(coords, list) and len(coords) >= 2:
            try:
                lng = float(coords[0])
                lat = float(coords[1])
            except (TypeError, ValueError):
                pass

        title = f"Reservoir observation: {species_name} at {place_guess or 'unknown'}"
        summary = (
            f"iNaturalist research-grade observation of {species_name}, a known "
            f"reservoir for {serotype or 'orthohantavirus'}. Observed {observed_on}."
        )

        # iNaturalist places have a country buried in the place ancestry; we
        # leave country_iso2 unresolved here and let analyst review map it.
        country_iso2: str | None = None

        canonical = "\n".join(
            [
                str(obs_id),
                species_name,
                observed_on,
                place_guess,
            ]
        ).encode("utf-8")

        return ParsedItem(
            external_id=f"inat:{obs_id}",
            title=title,
            summary=summary,
            country_iso2=country_iso2,
            region=place_guess or None,
            lat=lat,
            lng=lng,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=f"https://www.inaturalist.org/observations/{obs_id}",
            raw_content=canonical,
        )
