"""Peru Ministerio de Salud (MINSA) JSON API connector. NATO B2.

Peru is ANDV-endemic; documented case geography includes Amazonas, Loreto,
and Ucayali departments (upper Amazon basin). Peru is substantially
under-reported in international databases relative to Argentina and Chile.
MINSA publishes health news via the Peruvian government portal gob.pe.

URL history:
  0.1.0: https://www.gob.pe/institucion/minsa/noticias.json
         Confirmed 200, application/json; charset=utf-8, 9 items on
         2026-05-13. Returns: title, description, url, image, date.
         Date field is in Spanish long-form: "17 de marzo de 2026".
         The underlying site (minsa.gob.pe) returns HTTP 403 for direct
         access; gob.pe is the accessible government portal.

NATO B2: official Peruvian government source. Reporting quality is
moderate; hantavirus coverage is sparse but the portal does publish
epidemiological alerts. Keyword filter reduces noise.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_serotype
from .types import ParsedItem

# Spanish month name -> month number.
_ES_MONTHS: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _parse_spanish_date(s: str) -> date | None:
    """Parse "17 de marzo de 2026" -> date(2026, 3, 17). Returns None on failure."""
    if not s:
        return None
    parts = s.strip().lower().split()
    # Expected: ['17', 'de', 'marzo', 'de', '2026']
    try:
        if len(parts) >= 5 and parts[1] == "de" and parts[3] == "de":
            day = int(parts[0])
            month = _ES_MONTHS.get(parts[2])
            year = int(parts[4])
            if month:
                return date(year, month, day)
    except (ValueError, IndexError):
        pass
    return None


class PeruMINSAConnector(JSONAPIConnectorBase):
    """Peru MINSA news JSON API on the gob.pe government portal.

    The API returns a flat list of news items. Each item has:
      title       (str)
      description (str, truncated with '...')
      url         (str, full permalink on gob.pe)
      image       (str, CDN URL)
      date        (str, Spanish long-form: "17 de marzo de 2026")

    ITEMS_PATH is empty because the root of the response is already a list.
    """

    SOURCE_CODE: ClassVar[str] = "peru-minsa"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    ENDPOINT: ClassVar[str] = "https://www.gob.pe/institucion/minsa/noticias.json"
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ()   # root is list
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        "accept-language": "es-PE,es;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        # English / WHO standard
        "hantavirus",
        "hanta",
        "andes virus",
        "andv",
        "sin nombre",
        "hps",
        "hfrs",
        "hemorrhagic fever",
        "orthohantavirus",
        "rodent",
        "zoonosis",
        # Spanish — primary language of MINSA publications
        "hantavirosis",
        "virus andes",
        "sindrome cardiopulmonar",
        "sindrome pulmonar por hantavirus",
        "fiebre hemorragica",
        "fiebre hemorrágica",
        "roedor",
        "vigilancia epidemiologica",
        "vigilancia epidemiológica",
        "alerta epidemiologica",
        "alerta epidemiológica",
        "brote",
        "zoonosis",
        # Peru-specific geography relevant to hantavirus
        "amazonas",
        "loreto",
        "ucayali",
        "selva",
        "amazonia",
    ]

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        title = str(item.get("title") or "").strip()
        if not title:
            return None

        url = str(item.get("url") or "").strip()
        if not url:
            return None

        description = str(item.get("description") or "").strip() or None
        date_raw = str(item.get("date") or "").strip()
        reported = _parse_spanish_date(date_raw)

        # Use the URL as a stable external identifier (slug is permalink).
        external_id = url

        # Canonical bytes for chain-of-custody hashing: URL + title + date.
        canonical = f"{url}\n{title}\n{date_raw}".encode("utf-8")

        return ParsedItem(
            external_id=external_id,
            title=title,
            summary=description,
            country_iso2="PE",
            region=None,
            lat=None,
            lng=None,
            serotype_text=detect_serotype(f"{title} {description or ''}"),
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=url,
            raw_content=canonical,
        )
