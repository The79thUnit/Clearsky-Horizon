"""WHO Disease Outbreak News (DON) connector.

WHO restructured its public website in 2024-25 and replaced static HTML
listings with JS-rendered pages backed by an OData JSON API. The
HTMLScraperBase version of this connector (0.1.x) returned 0 items
forever after that switch because the listing HTML no longer contains
direct <a href="/disease-outbreak-news/item/..."> elements — they're
injected client-side.

This rewrite (0.2.0, verified 2026-05-13) targets the canonical OData
endpoint directly:

  https://www.who.int/api/news/diseaseoutbreaknews
    ?$orderby=PublicationDateAndTime desc
    &$top=50

The endpoint returns:
  {
    "value": [
      {
        "Title": "Hantavirus cluster linked to cruise ship travel, Multi-country",
        "PublicationDateAndTime": "2026-05-08T...",
        "ItemDefaultUrl": "/2026-DON600",
        "OverrideTitle": null,
        "regionscountries": [...]
      },
      ...
    ]
  }

Verified 2026-05-13: most recent 2 entries are DON 600 + DON 599, both
the MV Hondius cluster — exactly what we want.

NATO A1. Most authoritative outbreak channel.
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

from .json_api_base import JSONAPIConnectorBase
from .text_utils import detect_country, detect_serotype, parse_date_safe
from .types import ParsedItem


class WHODonConnector(JSONAPIConnectorBase):
    SOURCE_CODE: ClassVar[str] = "who-don"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    ENDPOINT: ClassVar[str] = "https://www.who.int/api/news/diseaseoutbreaknews"
    QUERY_PARAMS: ClassVar[dict[str, str]] = {
        # OData params. $orderby ensures newest-first so the global
        # ingest dedup hits cleanly. $top caps the result set so the
        # response stays under ~1 MB even if WHO ever increases their
        # default page size.
        "$orderby": "PublicationDateAndTime desc",
        "$top": "50",
    }
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ("value",)
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "andes",
        "sin nombre",
        "puumala",
        "hantaan",
        "seoul virus",
        "orthohantavirus",
    ]

    @staticmethod
    def _full_url(item_default_url: Any) -> str:
        """Compose the canonical DON URL from the API's slug field.

        `ItemDefaultUrl` can be either a plain string ("/2026-DON600")
        or an OData expansion dict like {"Url": "/2026-DON600", "Type": "..."}.
        Handle both. The canonical web URL is:
          https://www.who.int/emergencies/disease-outbreak-news/item/{slug}
        """
        if isinstance(item_default_url, dict):
            slug = item_default_url.get("Url") or item_default_url.get("url") or ""
        else:
            slug = str(item_default_url or "")
        slug = slug.strip().lstrip("/")
        if not slug:
            return ""
        return f"https://www.who.int/emergencies/disease-outbreak-news/item/{slug}"

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        # WHO sometimes overrides the title; prefer Override when set.
        if item.get("UseOverrideTitle") and item.get("OverrideTitle"):
            title = str(item["OverrideTitle"]).strip()
        else:
            title = str(item.get("Title", "")).strip()
        if not title:
            return None

        url = self._full_url(item.get("ItemDefaultUrl"))
        if not url:
            return None

        # Date can be either FormattedDate ("08 May 2026") or
        # PublicationDateAndTime ("2026-05-08T12:00:00Z"). Try both.
        pub = item.get("PublicationDateAndTime") or item.get("FormattedDate") or ""
        reported: date | None = None
        if pub:
            reported = parse_date_safe(
                str(pub)[:10],
                "%Y-%m-%d",  # ISO
                "%d %B %Y",  # "08 May 2026"
                "%B %Y",
            )

        # WHO's `regionscountries` is a list of country expansions; first
        # one is typically the primary affected country. Strict ISO-2
        # lookup happens later in detect_country() as a fallback.
        country: str | None = None
        rcs = item.get("regionscountries") or []
        if isinstance(rcs, list) and rcs:
            first = rcs[0]
            if isinstance(first, dict):
                country = (first.get("CountryCode") or first.get("countryCode") or "")[:2].upper() or None
        if not country:
            country = detect_country(title)

        serotype = detect_serotype(title)
        canonical = f"{url}\n{title}\n{pub}".encode()

        return ParsedItem(
            external_id=f"who-don:{url}",
            title=title,
            summary=None,
            country_iso2=country,
            region=None,
            lat=None,
            lng=None,
            serotype_text=serotype,
            reported_date=reported,
            case_count=None,
            death_count=None,
            raw_url=url,
            raw_content=canonical,
        )
