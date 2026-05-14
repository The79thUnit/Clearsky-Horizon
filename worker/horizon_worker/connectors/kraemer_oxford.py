"""Oxford Kraemer Lab — MV Hondius hantavirus line list connector.

Individual-level epidemiological line list for the 2026 Andes
orthohantavirus (ANDV) cluster aboard the MV Hondius cruise ship.

Maintained by Dr Moritz Kraemer (University of Oxford, Dept of Biology),
Sam Scarpino, and Andrew Rambaut (University of Edinburgh, Nextstrain).
Licence: CC0 1.0 (public domain waiver).

Data: https://github.com/kraemer-lab/Hondius_hantavirus_h2026
Raw CSV: data/linelist/2026_hantavirus.csv

Schema (28 columns, one row per tracked individual):
  Gh_ID             — row identifier (stable key)
  linked_id         — links to related case (family cluster, flight contact)
  status            — confirmed / probable / negative / monitored / tested
  symptom_onset     — ISO date or NA
  outcome           — "died" or blank (surviving / unknown)
  outcome_date      — ISO date of death
  treatment         — free text (ICU, hospitalised, biocontainment, etc.)
  cruise.crew..y.n. — crew flag
  passenger..y.n.   — passenger flag
  age, sex          — demographics (often missing)
  nationality       — free text, mapped to ISO 2-letter country code
  travel_to         — destination after ship, used as country fallback
  confirmed         — y/n
  confirmation_date — ISO date
  accession_id      — Pathoplexus/GenBank accession (PP_XXXXXX.X format)
  sources           — semicolon-delimited source URLs

NATO: B2 (usually reliable / probably true). Oxford/Edinburgh provenance;
sources column cross-references WHO DON600 and national health authority
press releases for every row. provenance_type: research-linelist. Tier 2.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, date, datetime
from typing import Any, ClassVar

import httpx

from .base import BaseConnector, FetchResult
from .types import ParsedItem

logger = logging.getLogger(__name__)

_CSV_URL = (
    "https://raw.githubusercontent.com/kraemer-lab/Hondius_hantavirus_h2026"
    "/main/data/linelist/2026_hantavirus.csv"
)

# Free-text nationality → ISO 3166-1 alpha-2.
# Entries are lower-cased before lookup; partial matches are tried if exact
# match fails (handles "singaporean permanent resident" → "SG").
_NATIONALITY_ISO2: dict[str, str] = {
    "dutch": "NL",
    "netherlands": "NL",
    "british": "GB",
    "uk": "GB",
    "english": "GB",
    "scottish": "GB",
    "welsh": "GB",
    "german": "DE",
    "swiss": "CH",
    "french": "FR",
    "american": "US",
    "usa": "US",
    "us": "US",
    "singaporean": "SG",
    "singapore": "SG",
    "spanish": "ES",
    "spain": "ES",
    "argentinian": "AR",
    "argentine": "AR",
    "argentina": "AR",
    "italian": "IT",
    "italy": "IT",
    "belgian": "BE",
    "belgium": "BE",
    "norwegian": "NO",
    "norway": "NO",
    "swedish": "SE",
    "sweden": "SE",
    "danish": "DK",
    "denmark": "DK",
    "finnish": "FI",
    "finland": "FI",
    "dutch/german": "NL",  # mixed nationality — use first
    "canadian": "CA",
    "canada": "CA",
    "australian": "AU",
    "australia": "AU",
    "new zealander": "NZ",
    "south african": "ZA",
    "south africa": "ZA",
    "japanese": "JP",
    "japan": "JP",
    "korean": "KR",
    "south korean": "KR",
    "chinese": "CN",
    "china": "CN",
}

# Free-text location strings found in travel_to / left_location → ISO2.
# Used as a fallback when nationality gives no result.
_LOCATION_ISO2: dict[str, str] = {
    "netherlands": "NL",
    "amsterdam": "NL",
    "rotterdam": "NL",
    "switzerland": "CH",
    "zurich": "CH",
    "bern": "CH",
    "geneva": "CH",
    "germany": "DE",
    "dusseldorf": "DE",
    "berlin": "DE",
    "frankfurt": "DE",
    "france": "FR",
    "paris": "FR",
    "lyon": "FR",
    "united states": "US",
    "usa": "US",
    "nebraska": "US",
    "new york": "US",
    "california": "US",
    "spain": "ES",
    "madrid": "ES",
    "barcelona": "ES",
    "argentina": "AR",
    "buenos aires": "AR",
    "italy": "IT",
    "rome": "IT",
    "milan": "IT",
    "singapore": "SG",
    "south africa": "ZA",
    "johannesburg": "ZA",
    "cape town": "ZA",
    "united kingdom": "GB",
    "uk": "GB",
    "london": "GB",
    "canada": "CA",
    "toronto": "CA",
    "montreal": "CA",
    "australia": "AU",
    "sydney": "AU",
    "melbourne": "AU",
}

# Status values that represent actual cases (not negatives/monitoring).
_CASE_STATUSES = {"confirmed", "probable"}
# Status values that get case_count=0 (they're being tracked, not cases).
_NON_CASE_STATUSES = {"negative", "monitored", "tested"}


def _parse_iso_date(val: str) -> date | None:
    """Parse ISO date string, returning None for blank / NA / invalid."""
    v = val.strip().upper()
    if not v or v in {"NA", "N/A", "UNKNOWN", "-"}:
        return None
    try:
        return date.fromisoformat(val.strip())
    except ValueError:
        return None


def _resolve_country(nationality: str, travel_to: str) -> str | None:
    """Resolve ISO2 from free-text nationality, falling back to travel_to."""
    if nationality:
        key = nationality.strip().lower()
        # Exact match
        if key in _NATIONALITY_ISO2:
            return _NATIONALITY_ISO2[key]
        # Partial match: check if any known key is a prefix of the value
        # (handles "singaporean permanent resident" → "SG")
        for known_key, iso2 in _NATIONALITY_ISO2.items():
            if key.startswith(known_key):
                return iso2

    if travel_to:
        tl = travel_to.strip().lower()
        for loc_key, iso2 in _LOCATION_ISO2.items():
            if loc_key in tl:
                return iso2

    return None


def _clean_col(name: str) -> str:
    """Normalise CSV column names: strip whitespace, lower, collapse dots."""
    return name.strip().lower().replace("..", ".").replace(".", "_")


def _first_url(sources_field: str) -> str | None:
    """Return the first URL from a semicolon-delimited sources field."""
    if not sources_field or sources_field.strip().upper() in {"NA", ""}:
        return None
    for part in sources_field.split(";"):
        candidate = part.strip()
        if candidate.startswith("http"):
            return candidate
    return None


class KraemerOxfordConnector(BaseConnector):
    """Fetch the Oxford Kraemer Lab MV Hondius ANDV individual line list."""

    SOURCE_CODE: ClassVar[str] = "kraemer-oxford"
    PARSER_VERSION: ClassVar[str] = "0.1.0"

    async def run(self) -> FetchResult:
        start = datetime.now(tz=UTC)
        try:
            async with httpx.AsyncClient(
                timeout=30,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(_CSV_URL)
                if response.status_code in {429, 502, 503, 504}:
                    return FetchResult(
                        source_code=self.SOURCE_CODE,
                        parser_version=self.PARSER_VERSION,
                        http_status=response.status_code,
                        latency_ms=int(
                            (datetime.now(tz=UTC) - start).total_seconds() * 1000
                        ),
                        items_seen=0, items=[], items_filtered=0, error=None,
                    )
                response.raise_for_status()
                raw = response.text

            items = self._parse_linelist(raw)
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=response.status_code,
                latency_ms=latency,
                items_seen=len(items),
                items=items,
                items_filtered=0,
                error=None,
            )
        except Exception as exc:
            latency = int((datetime.now(tz=UTC) - start).total_seconds() * 1000)
            logger.exception("Kraemer Oxford line list fetch failed")
            return FetchResult(
                source_code=self.SOURCE_CODE,
                parser_version=self.PARSER_VERSION,
                http_status=None,
                latency_ms=latency,
                items_seen=0, items=[], items_filtered=0, error=str(exc),
            )

    def _parse_linelist(self, raw_csv: str) -> list[ParsedItem]:
        """Parse the 28-column line list CSV into ParsedItems.

        One ParsedItem per row regardless of status. This preserves the full
        epidemiological picture (negatives + contacts show transmission chains).
        case_count is 1 for confirmed/probable, 0 for everything else.
        death_count is 1 only when outcome == "died".
        """
        reader = csv.DictReader(io.StringIO(raw_csv))
        # Normalise field names once
        if reader.fieldnames is None:
            return []
        clean_fields = {fn: _clean_col(fn) for fn in reader.fieldnames}

        items: list[ParsedItem] = []
        for raw_row in reader:
            row: dict[str, str] = {
                clean_fields.get(k, k): (v or "").strip()
                for k, v in raw_row.items()
            }

            gh_id = row.get("gh_id", "").strip()
            if not gh_id:
                continue

            status = row.get("status", "").strip().lower()
            nationality = row.get("nationality", "").strip()
            travel_to = row.get("travel_to", "").strip()
            symptom_onset = row.get("symptom_onset", "")
            outcome = row.get("outcome", "").strip().lower()
            confirmation_date = row.get("confirmation_date", "")
            treatment_date = row.get("treatment_date", "")
            sources_field = row.get("sources", "")
            accession = row.get("accession_id", "").strip().rstrip()
            treatment = row.get("treatment", "").strip()
            age = row.get("age", "").strip()
            sex = row.get("sex", "").strip()
            left_location = row.get("left_location", "").strip()
            context = row.get("context", "").strip()

            # Date: symptom onset is most accurate; fall back to confirmation
            # date, then treatment date.
            reported = (
                _parse_iso_date(symptom_onset)
                or _parse_iso_date(confirmation_date)
                or _parse_iso_date(treatment_date)
            )

            # Country: nationality first, travel_to as fallback, then
            # left_location (disembarkation port country).
            country_iso2 = _resolve_country(nationality, travel_to)
            if not country_iso2 and left_location:
                country_iso2 = _resolve_country("", left_location)

            # Case and death counts
            case_count: int | None = None
            if status in _CASE_STATUSES:
                case_count = 1
            elif status in _NON_CASE_STATUSES:
                case_count = 0

            death_count = 1 if outcome == "died" else 0

            raw_url = _first_url(sources_field)

            # Structured title
            status_label = status.title() if status else "Unknown"
            nat_label = nationality.title() if nationality else "unknown nationality"
            age_label = f"age {age}" if age and age.upper() not in {"NA", ""} else ""
            sex_label = sex if sex and sex.upper() not in {"NA", ""} else ""
            demo = ", ".join(filter(None, [age_label, sex_label]))
            outcome_label = " (DECEASED)" if outcome == "died" else ""
            title = (
                f"MV Hondius ANDV {status_label} — {nat_label}"
                f"{' (' + demo + ')' if demo else ''}"
                f"{outcome_label} [Kraemer-2026 ID {gh_id}]"
            )

            # Summary: pack all available metadata for text search + AI extraction
            summary_parts: list[str] = [
                f"Oxford Kraemer Lab MV Hondius line list — row {gh_id}.",
                f"Status: {status}.",
            ]
            if reported:
                summary_parts.append(f"Symptom onset: {reported.isoformat()}.")
            if outcome:
                summary_parts.append(
                    f"Outcome: {outcome}"
                    + (f" on {row.get('outcome_date', '').strip()}." if row.get("outcome_date") else ".")
                )
            if treatment:
                summary_parts.append(f"Treatment: {treatment}.")
            if nationality:
                summary_parts.append(f"Nationality: {nationality}.")
            if travel_to:
                summary_parts.append(f"Destination: {travel_to}.")
            if left_location:
                summary_parts.append(f"Disembarked: {left_location}.")
            if context:
                summary_parts.append(f"Context: {context}.")
            if accession and accession.upper() not in {"NA", ""}:
                summary_parts.append(
                    f"Pathoplexus/GenBank accession: {accession}."
                )
            summary_parts.append(
                "Andes orthohantavirus (ANDV) cluster — MV Hondius cruise ship 2026. "
                "Exposure suspected during Ushuaia pre-departure excursion, "
                "Tierra del Fuego, Argentina."
            )

            external_id = f"kraemer-oxford:hondius2026-{gh_id}"
            canonical_content = (
                f"{external_id}\n{status}\n{reported}\n{outcome}"
            ).encode()

            items.append(
                ParsedItem(
                    external_id=external_id,
                    title=title,
                    summary=" ".join(summary_parts),
                    country_iso2=country_iso2,
                    region="MV Hondius / Tierra del Fuego, Argentina",
                    lat=-54.8019,   # Ushuaia, Argentina (index exposure site)
                    lng=-68.3029,
                    serotype_text="ANDV",
                    reported_date=reported,
                    case_count=case_count,
                    death_count=death_count,
                    raw_url=raw_url or _CSV_URL,
                    raw_content=canonical_content,
                )
            )

        return items
