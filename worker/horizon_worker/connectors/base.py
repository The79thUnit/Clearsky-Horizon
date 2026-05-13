"""Abstract connector base class.

Subclasses implement `fetch_raw` and `parse`. `filter_relevant` defaults to a
keyword match on title + summary; override for richer filtering.
"""

from __future__ import annotations

import abc
import logging
import time
from dataclasses import dataclass
from typing import ClassVar

import httpx

from .types import ParsedItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FetchResult:
    items: list[ParsedItem]
    http_status: int
    latency_ms: int
    items_seen: int
    items_filtered: int
    parser_version: str
    error: str | None = None


class BaseConnector(abc.ABC):
    """Abstract ingest connector.

    Lifecycle:
      run() -> fetch_and_parse(client) -> fetch_raw + parse + filter_relevant.

    Tests should call fetch_and_parse with a MockTransport-backed httpx client.
    Production code calls run() which creates a real client.
    """

    SOURCE_CODE: ClassVar[str]
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    KEYWORDS: ClassVar[list[str]] = ["hantavirus", "hanta", "hps", "hfrs"]
    TIMEOUT_SEC: ClassVar[float] = 30.0

    def __init__(self, *, user_agent: str = "HORIZON/0.1") -> None:
        self.user_agent = user_agent

    @abc.abstractmethod
    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        """Fetch the upstream payload. Returns (bytes, http_status)."""

    @abc.abstractmethod
    def parse(self, raw: bytes) -> list[ParsedItem]:
        """Parse raw into ParsedItems (may include irrelevant items)."""

    def filter_relevant(self, items: list[ParsedItem]) -> list[ParsedItem]:
        """Default: keyword match on title + summary."""
        keywords_lower = [k.lower() for k in self.KEYWORDS]
        out: list[ParsedItem] = []
        for item in items:
            haystack = f"{item.title} {item.summary or ''}".lower()
            if any(k in haystack for k in keywords_lower):
                out.append(item)
        return out

    async def fetch_and_parse(self, client: httpx.AsyncClient) -> FetchResult:
        """Production-and-test entry point. Inject the client."""
        start = time.perf_counter()
        try:
            raw, status = await self.fetch_raw(client)
        except httpx.HTTPError as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.warning("connector %s fetch failed: %s", self.SOURCE_CODE, exc)
            return FetchResult(
                items=[],
                http_status=0,
                latency_ms=elapsed_ms,
                items_seen=0,
                items_filtered=0,
                parser_version=self.PARSER_VERSION,
                error=f"fetch error: {exc}",
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        try:
            all_items = self.parse(raw)
        except Exception as exc:
            logger.exception("connector %s parse failed", self.SOURCE_CODE)
            return FetchResult(
                items=[],
                http_status=status,
                latency_ms=elapsed_ms,
                items_seen=0,
                items_filtered=0,
                parser_version=self.PARSER_VERSION,
                error=f"parse error: {exc}",
            )

        relevant = self.filter_relevant(all_items)
        return FetchResult(
            items=relevant,
            http_status=status,
            latency_ms=elapsed_ms,
            items_seen=len(all_items),
            items_filtered=len(all_items) - len(relevant),
            parser_version=self.PARSER_VERSION,
        )

    async def run(self) -> FetchResult:
        """Convenience wrapper that creates a default client.

        Two-phase fetch identical to clearsky-web/api/helpers/page_fetch.py:

          1. Try curl_cffi with Chrome TLS-fingerprint impersonation.
             This defeats Akamai/Cloudflare bot-fight checks that key off
             the JA3/JA4 TLS handshake (Python's default httpx exposes a
             distinctive fingerprint that anti-bot WAFs recognise).
             Verified 2026-05-13 to recover australia-health from a
             total block.

          2. Fall back to plain httpx if curl_cffi isn't installed or
             returns non-200. Httpx handles the long tail of plain HTTP
             sources where TLS fingerprinting isn't a concern.

        The fallback is one-way: if curl_cffi succeeds (200 OK), we use
        its body. If it returns anything else, we let httpx try.
        Connectors don't need to know which path was used — both
        produce the same (bytes, status) tuple via _ImpersonatedClient.
        """
        try:
            from curl_cffi import requests as _cffi  # type: ignore
        except ImportError:
            _cffi = None  # type: ignore[assignment]

        # Phase 1: curl_cffi with Chrome impersonation
        if _cffi is not None:
            result = await self._run_via_curl_cffi(_cffi)
            if result is not None:
                return result

        # Phase 2: httpx fallback (the original code path)
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.TIMEOUT_SEC,
            follow_redirects=True,
        ) as client:
            return await self.fetch_and_parse(client)

    async def _run_via_curl_cffi(self, cffi_module: object) -> FetchResult | None:
        """
        Attempt the fetch via curl_cffi with Chrome 120 TLS fingerprint.
        Returns:
          FetchResult — on 200 OK, parsed and filtered
          None       — on any non-200, signalling the caller to try httpx

        Connectors that aren't a single GET (PubMed, Kpler — multi-step
        flows) keep their existing httpx code paths because they
        override fetch_raw with custom logic. The default
        BaseConnector.fetch_raw signature is `(client) -> (bytes, status)`
        which curl_cffi can't fulfill directly (it's sync, not an
        AsyncClient); so this method calls fetch_raw indirectly by
        asking subclasses for the URL via getattr fallbacks and
        replaying the result through fetch_and_parse with a stub client.
        """
        # Discover the URL the connector wants to fetch. RSSConnectorBase
        # exposes FEED_URL; HTMLScraperBase exposes LISTING_URL;
        # JSONAPIConnectorBase exposes ENDPOINT + QUERY_PARAMS. Multi-
        # step connectors (PubMed, Kpler) leave these unset and we
        # therefore skip curl_cffi for them (httpx path still runs).
        url = (
            getattr(self, "FEED_URL", "")
            or getattr(self, "LISTING_URL", "")
            or getattr(self, "ENDPOINT", "")
        )
        if not url:
            return None  # multi-step connector — let httpx handle it

        extra_headers = dict(getattr(self, "EXTRA_HEADERS", {}) or {})
        query_params = dict(getattr(self, "QUERY_PARAMS", {}) or {})

        # Browser-like headers. Anti-bot WAFs look at the full header
        # set, not just the TLS handshake. Mirror clearsky-web's
        # page_fetch.py header bundle.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "application/rss+xml;q=0.9,application/atom+xml;q=0.9,"
                "application/json;q=0.8,*/*;q=0.5"
            ),
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
            **extra_headers,
        }

        import asyncio
        import time as _time

        start = _time.perf_counter()
        try:
            # curl_cffi is synchronous; offload to a thread so we don't
            # block the asyncio event loop.
            def _sync_get() -> tuple[bytes, int]:
                resp = cffi_module.get(  # type: ignore[attr-defined]
                    url,
                    params=query_params or None,
                    headers=headers,
                    impersonate="chrome120",
                    timeout=self.TIMEOUT_SEC,
                    allow_redirects=True,
                    max_redirects=5,
                )
                return resp.content, resp.status_code

            raw, status = await asyncio.to_thread(_sync_get)
        except Exception as exc:  # curl_cffi raises requests.RequestsError
            logger.debug(
                "connector %s curl_cffi failed (will fall through to httpx): %s",
                self.SOURCE_CODE, exc,
            )
            return None

        if status != 200:
            # Non-200 via curl_cffi → let httpx try too. Don't burn the
            # quality-log entry on a fingerprint-impersonated attempt.
            return None

        elapsed_ms = int((_time.perf_counter() - start) * 1000)
        try:
            all_items = self.parse(raw)
        except Exception as exc:  # noqa: BLE001
            logger.exception("connector %s parse failed (curl_cffi path)", self.SOURCE_CODE)
            return FetchResult(
                items=[],
                http_status=status,
                latency_ms=elapsed_ms,
                items_seen=0,
                items_filtered=0,
                parser_version=self.PARSER_VERSION,
                error=f"parse error: {exc}",
            )
        relevant = self.filter_relevant(all_items)
        return FetchResult(
            items=relevant,
            http_status=status,
            latency_ms=elapsed_ms,
            items_seen=len(all_items),
            items_filtered=len(all_items) - len(relevant),
            parser_version=self.PARSER_VERSION,
        )
