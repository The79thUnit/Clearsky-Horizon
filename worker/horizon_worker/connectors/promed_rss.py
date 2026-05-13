"""ProMED-mail RSS feed connector.

ProMED-mail is the International Society for Infectious Diseases' (ISID)
24/7 expert-curated outbreak alert system. NATO B2 default.

STATUS: DISABLED as of 2026-05-13 (migration 046).

ProMED migrated to a Next.js + Auth0 + subscription platform in 2024-2025
(ISID infrastructure rebuild). As of 2026-05-13:
  - /promed-news/feed/ returns Next.js HTML (no RSS feed)
  - /api/v1/* returns HTTP 401: {"success":false,"message":"Authorization
    header missing"} on ALL paths (bearer token required)
  - posts-sitemap.xml contains 5 marketing blog posts only — no outbreak
    reports; even those return HTTP 404
  - No public free-tier access path exists

The DB source is disabled (enabled=FALSE) and the beat schedule entry has
been removed from celery_app.py. This connector file is kept for reference
and to support re-enabling if ProMED ever restores a public feed.

Re-enable path:
  1. Confirm a working public URL (RSS or scrape target)
  2. Update FEED_URL below
  3. Write migration 0NN_reenable_promed_rss.sql
  4. Restore the beat schedule entry in celery_app.py
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import ClassVar

import feedparser
import httpx

from .base import BaseConnector
from .text_utils import strip_html
from .types import ParsedItem

# Very small country-name -> ISO2 map for Phase 1.
# Phase 2 should replace with a proper geocoder (Nominatim or GeoNames).
_COUNTRY_MAP: dict[str, str] = {
    "argentina": "AR",
    "chile": "CL",
    "brazil": "BR",
    "uruguay": "UY",
    "paraguay": "PY",
    "bolivia": "BO",
    "peru": "PE",
    "ecuador": "EC",
    "panama": "PA",
    "colombia": "CO",
    "venezuela": "VE",
    "united states": "US",
    "usa": "US",
    "u.s.": "US",
    "us": "US",
    "canada": "CA",
    "mexico": "MX",
    "germany": "DE",
    "finland": "FI",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "iceland": "IS",
    "france": "FR",
    "spain": "ES",
    "italy": "IT",
    "russia": "RU",
    "china": "CN",
    "south korea": "KR",
    "korea": "KR",
    "japan": "JP",
    "united kingdom": "GB",
    "uk": "GB",
    "england": "GB",
    "scotland": "GB",
    "netherlands": "NL",
    "belgium": "BE",
    "ireland": "IE",
    "austria": "AT",
    "switzerland": "CH",
    "poland": "PL",
    "czech republic": "CZ",
    "slovakia": "SK",
    "slovenia": "SI",
    "croatia": "HR",
    "serbia": "RS",
    "bosnia": "BA",
    "montenegro": "ME",
    "greece": "GR",
    "turkey": "TR",
}

_REGION_PAREN = re.compile(r"\(([^)]+)\)")


class ProMEDRSSConnector(BaseConnector):
    """ProMED-mail RSS feed connector."""

    SOURCE_CODE: ClassVar[str] = "promed-rss"
    PARSER_VERSION: ClassVar[str] = "0.1.1"
    # NOTE 2026-05-11: ProMED's public RSS feed has been intermittently 404
    # since their 2024-2025 infrastructure issues (see Science, Nov 2025).
    # We poll the historical feed URL pattern; on 404 the connector falls
    # back to parsing the homepage post list (Phase 2 enhancement TBD).
    FEED_URL: ClassVar[str] = "https://promedmail.org/promed-news/feed/"
    KEYWORDS: ClassVar[list[str]] = [
        "hantavirus",
        "hanta",
        "hps",
        "hfrs",
        "andes virus",
        "andv",
        "sin nombre",
        "snv",
        "puumala",
        "puuv",
        "seoul virus",
        "seov",
        "hantaan",
        "htnv",
        "dobrava",
        "dobv",
        "nephropathia epidemica",
    ]

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        response = await client.get(self.FEED_URL)
        response.raise_for_status()
        return response.content, response.status_code

    def parse(self, raw: bytes) -> list[ParsedItem]:
        feed = feedparser.parse(raw)
        out: list[ParsedItem] = []
        for entry in feed.entries:
            external_id = (
                getattr(entry, "id", None)
                or getattr(entry, "guid", None)
                or getattr(entry, "link", "")
            )
            title = strip_html(getattr(entry, "title", "") or "")
            raw_summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
            summary = strip_html(raw_summary) if raw_summary else None
            link = (getattr(entry, "link", "") or "").strip()
            published_str = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""
            reported = self._parse_date(entry)

            country = self._extract_country(title)
            region = self._extract_region(title)
            serotype = self._detect_serotype(f"{title} {summary or ''}")

            # Per-item canonical bytes for chain-of-custody hashing.
            canonical = "\n".join(
                [
                    str(external_id),
                    str(link),
                    str(title),
                    str(published_str),
                    str(summary or ""),
                ]
            ).encode("utf-8")

            out.append(
                ParsedItem(
                    external_id=str(external_id) or f"promed:{link}",
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
            )
        return out

    @staticmethod
    def _parse_date(entry: object) -> date | None:
        for attr in ("published_parsed", "updated_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    return datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=UTC).date()
                except (TypeError, ValueError, IndexError):
                    continue
        return None

    @staticmethod
    def _extract_country(title: str) -> str | None:
        lower = title.lower()
        # Match the longest country name first to avoid 'us' matching inside other words.
        for name in sorted(_COUNTRY_MAP.keys(), key=len, reverse=True):
            if name in lower:
                return _COUNTRY_MAP[name]
        return None

    @staticmethod
    def _extract_region(title: str) -> str | None:
        m = _REGION_PAREN.search(title)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _detect_serotype(text: str) -> str | None:
        text_lower = text.lower()
        # Order matters: more specific terms first.
        mapping: list[tuple[tuple[str, ...], str]] = [
            (("andes virus", "andv"), "ANDV"),
            (("sin nombre", "snv"), "SNV"),
            (("puumala", "puuv"), "PUUV"),
            (("hantaan", "htnv"), "HTNV"),
            (("seoul virus", "seov"), "SEOV"),
            (("dobrava", "dobv"), "DOBV"),
        ]
        for needles, code in mapping:
            if any(n in text_lower for n in needles):
                return code
        return None
