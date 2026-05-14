"""Base class for connectors backed by an RSS / Atom feed.

Subclasses set SOURCE_CODE, FEED_URL, KEYWORDS, optionally PARSER_VERSION.
The base handles fetch + feedparser-based parsing + keyword filtering.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, ClassVar

import feedparser
import httpx

from .base import BaseConnector
from .text_utils import detect_country, detect_serotype, extract_region, strip_html
from .types import ParsedItem


class RSSConnectorBase(BaseConnector):
    """Shared logic for any source that exposes an RSS or Atom feed."""

    FEED_URL: ClassVar[str] = ""
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {}

    # HTTP status codes treated as TRANSIENT — upstream is briefly
    # rate-limiting (429), unreachable (502), overloaded (503), or its
    # backend timed out (504). These are not connector bugs and they
    # don't deserve an "error" log line every tick. We record the
    # actual status code honestly and return an empty body so the
    # ingest summary shows http_status=429/5xx, items_seen=0, error=None.
    _TRANSIENT_STATUSES: ClassVar[frozenset[int]] = frozenset({429, 502, 503, 504})

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        response = await client.get(self.FEED_URL, headers=self.EXTRA_HEADERS or None)
        if response.status_code in self._TRANSIENT_STATUSES:
            return b"", response.status_code
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
            # Strip any HTML the feed shoves into title/summary (Google News
            # wraps everything in <a> + <font> tags; many RSS feeds embed
            # markup in the description). We store plain text only.
            title = strip_html(getattr(entry, "title", "") or "")
            raw_summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
            summary = strip_html(raw_summary) if raw_summary else None
            link = (getattr(entry, "link", "") or "").strip()
            published_str = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""
            reported = self._parse_date(entry)

            haystack = f"{title} {summary or ''}"
            country = detect_country(haystack)
            region = extract_region(title)
            serotype = detect_serotype(haystack, country_iso2=country)

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
                    external_id=str(external_id) or f"{self.SOURCE_CODE}:{link}",
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
    def _parse_date(entry: Any) -> date | None:
        for attr in ("published_parsed", "updated_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    return datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=UTC).date()
                except (TypeError, ValueError, IndexError):
                    continue
        return None
