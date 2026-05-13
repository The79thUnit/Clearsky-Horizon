"""Argentina Boletín Epidemiológico Nacional (BEN) scraper. NATO A1.

Argentina is the global ANDV epicentre; Patagonia has documented
person-to-person transmission. The BEN is the canonical weekly
epidemiological bulletin published by Ministerio de Salud de la Nación.

URL history:
  0.1.0: https://www.argentina.gob.ar/salud/noticias.xml (RSS) — 404 as of
          2026-05-13. RSS feed retired; no announced replacement.
  0.2.0: HTMLScraperBase against the 2026 BEN bulletin index at
          argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026.
          Confirmed 200 at 40 KB on 2026-05-13. Parses <h4> bulletin headers
          + <li> disease topics; one ParsedItem per qualifying bulletin
          pointing at the PDF download URL.

Note: LISTING_URL is year-specific (/boletines-2026). Update the class
constant when the calendar year rolls over.

Keywords are bilingual EN/ES because the source is Spanish-language.
"""

from __future__ import annotations

import re
from datetime import date
from typing import ClassVar

from bs4 import BeautifulSoup, Tag

from .html_scraper_base import HTMLScraperBase
from .text_utils import detect_serotype, extract_case_count_claim, extract_death_count_claim
from .types import ParsedItem

# Spanish month names -> ISO month number.
_MONTHS_ES: dict[str, int] = {
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

# "BEN 807 SE 17 (26 de abril al 2 de Mayo 2026)"
_BEN_HEADER = re.compile(r"BEN\s+(\d+)\s+SE\s+\d+", re.IGNORECASE)

# Spanish date: "2 de Mayo 2026", "25 de Abril 2026", or "3 de Enero de 2026"
# The optional (?:de\s+)? handles the "de YYYY" variant used in year-boundary
# headers where the end date falls in January (e.g. BEN 790 SE 53).
_DATE_ES = re.compile(r"\b(\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})\b", re.IGNORECASE)


def _parse_es_date(text: str) -> date | None:
    """Return the last Spanish-format date found in text (week end-date)."""
    found = _DATE_ES.findall(text)
    if not found:
        return None
    day_s, month_s, year_s = found[-1]
    month = _MONTHS_ES.get(month_s.lower())
    if month is None:
        return None
    try:
        return date(int(year_s), month, int(day_s))
    except ValueError:
        return None


def _fix_pdf_url(href: str) -> str:
    """Normalise the non-standard PDF hrefs used by argentina.gob.ar.

    Two observed patterns on 2026-05-13:
      blank:#/sites/default/files/...pdf      -> relative, strip "blank:#"
      blank:#https://www.argentina.gob.ar/... -> full URL, strip "blank:#"
    """
    if href.startswith("blank:#https://"):
        return href[len("blank:#"):]
    if href.startswith("blank:#/"):
        return "https://www.argentina.gob.ar" + href[len("blank:#"):]
    if href.startswith("/"):
        return "https://www.argentina.gob.ar" + href
    return href


class ArgentinaMSALConnector(HTMLScraperBase):
    """Argentina BEN weekly bulletin index scraper.

    The listing page groups one <h4> bulletin header followed by <li>
    disease-topic items and a PDF download link per bulletin entry. We
    parse all bulletins and return one ParsedItem per entry; the inherited
    filter_relevant() applies the keyword list as the final pass, keeping
    only those bulletins that list hantavirus-related topics.
    """

    SOURCE_CODE: ClassVar[str] = "argentina-msal"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    LISTING_URL: ClassVar[str] = (
        "https://www.argentina.gob.ar"
        "/salud/boletin-epidemiologico-nacional/boletines-2026"
    )
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {
        # Signal Spanish-language preference; helps if the CDN does content
        # negotiation (argentina.gob.ar is Spanish-only, but belt-and-braces).
        "accept-language": "es-AR,es;q=0.9,en;q=0.8",
    }
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hantavirosis",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        # Spanish
        "virus andes",
        "sindrome cardiopulmonar",
        "sindrome pulmonar por hantavirus",
        "fiebre hemorrágica",
        "fiebre hemorragica",
        "roedor",
        "ratón colilargo",
        "oligoryzomys",
        "malbrán",
        "malbran",
    ]

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        """Parse all BEN bulletin entries from the 2026 listing page.

        Returns one ParsedItem per bulletin. Items whose topic list does
        not contain hantavirus-related terms will be dropped by the
        inherited filter_relevant().
        """
        items: list[ParsedItem] = []

        for h4 in soup.find_all("h4"):
            header_text = h4.get_text(strip=True)
            m = _BEN_HEADER.search(header_text)
            if not m:
                continue

            ben_number = int(m.group(1))

            # Walk siblings until the next BEN bulletin header.
            topics: list[str] = []
            pdf_url: str | None = None

            for sibling in h4.find_next_siblings():
                if not isinstance(sibling, Tag):
                    continue
                # Stop at the start of the next bulletin.
                if sibling.name == "h4" and _BEN_HEADER.search(
                    sibling.get_text(strip=True)
                ):
                    break
                # Collect <li> disease-topic labels (handles any nesting depth).
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        topics.append(text)
                # Edge case: sibling itself is a bare <li>.
                if sibling.name == "li":
                    text = sibling.get_text(strip=True)
                    if text and text not in topics:
                        topics.append(text)
                # Locate the PDF download link (first .pdf or ben_ href wins).
                if pdf_url is None:
                    for a in sibling.find_all("a", href=True):
                        href = str(a["href"])
                        if ".pdf" in href.lower() or "ben_" in href.lower():
                            pdf_url = _fix_pdf_url(href)
                            break

            if not topics:
                continue

            reported = _parse_es_date(header_text)
            topic_str = ", ".join(topics)

            # Title = the canonical bulletin header as published.
            # Summary = topic list for keyword matching + analyst context.
            title = header_text
            summary = f"Temas cubiertos: {topic_str}."

            raw_url = pdf_url or self.LISTING_URL
            # Chain-of-custody anchor for dedup: bulletin number + header text.
            raw_content = f"argentina-ben:{ben_number}\n{header_text}".encode()

            items.append(
                ParsedItem(
                    external_id=f"argentina-ben:{ben_number}",
                    title=title,
                    summary=summary,
                    country_iso2="AR",
                    region="Argentina",
                    lat=None,
                    lng=None,
                    serotype_text=detect_serotype(f"{title} {summary}"),
                    reported_date=reported,
                    case_count=extract_case_count_claim(summary),
                    death_count=extract_death_count_claim(summary),
                    raw_url=raw_url,
                    raw_content=raw_content,
                )
            )

        return items
