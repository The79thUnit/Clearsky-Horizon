"""Base class for connectors that scrape a listing page (HTML).

Subclasses set SOURCE_CODE, LISTING_URL, and override parse_soup() to turn
a parsed page into ParsedItems. BeautifulSoup is used as the HTML parser.
"""

from __future__ import annotations

from typing import ClassVar

import httpx
from bs4 import BeautifulSoup

from .base import BaseConnector
from .types import ParsedItem


class HTMLScraperBase(BaseConnector):
    """Shared logic for HTML-listing scrapers."""

    LISTING_URL: ClassVar[str] = ""
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {}
    HTML_PARSER: ClassVar[str] = "lxml"  # falls back to html.parser if lxml absent

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        headers = {
            "accept": "text/html,application/xhtml+xml",
            **self.EXTRA_HEADERS,
        }
        response = await client.get(self.LISTING_URL, headers=headers)
        response.raise_for_status()
        return response.content, response.status_code

    def parse(self, raw: bytes) -> list[ParsedItem]:
        try:
            soup = BeautifulSoup(raw, self.HTML_PARSER)
        except Exception:
            soup = BeautifulSoup(raw, "html.parser")
        return self.parse_soup(soup)

    def parse_soup(self, soup: BeautifulSoup) -> list[ParsedItem]:
        """Override in subclass."""
        raise NotImplementedError
