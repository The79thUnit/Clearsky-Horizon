"""Base class for connectors backed by a JSON API endpoint.

Subclasses set SOURCE_CODE, ENDPOINT, and override parse_item() to turn a
single dict from the response into a ParsedItem.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

import httpx

from .base import BaseConnector
from .types import ParsedItem


class JSONAPIConnectorBase(BaseConnector):
    """Shared logic for any source that returns JSON over HTTP."""

    ENDPOINT: ClassVar[str] = ""
    QUERY_PARAMS: ClassVar[dict[str, str]] = {}
    EXTRA_HEADERS: ClassVar[dict[str, str]] = {}
    # Path through nested JSON to reach the list of items. Empty = root is list.
    ITEMS_PATH: ClassVar[tuple[str, ...]] = ()

    # Match RSSConnectorBase: transient upstream codes (rate-limit, 5xx)
    # return an empty body + actual status, no exception, no error log.
    _TRANSIENT_STATUSES: ClassVar[frozenset[int]] = frozenset({429, 502, 503, 504})

    async def fetch_raw(self, client: httpx.AsyncClient) -> tuple[bytes, int]:
        headers = {"accept": "application/json", **self.EXTRA_HEADERS}
        response = await client.get(
            self.ENDPOINT,
            params=self.QUERY_PARAMS or None,
            headers=headers,
        )
        if response.status_code in self._TRANSIENT_STATUSES:
            return b"", response.status_code
        response.raise_for_status()
        return response.content, response.status_code

    def parse(self, raw: bytes) -> list[ParsedItem]:
        try:
            data: Any = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return []

        # Drill into ITEMS_PATH
        for key in self.ITEMS_PATH:
            if not isinstance(data, dict):
                return []
            data = data.get(key, [])

        if not isinstance(data, list):
            return []

        out: list[ParsedItem] = []
        for raw_item in data:
            if not isinstance(raw_item, dict):
                continue
            parsed = self.parse_item(raw_item)
            if parsed is not None:
                out.append(parsed)
        return out

    def parse_item(self, item: dict[str, Any]) -> ParsedItem | None:
        """Override in subclass. Return None to drop the item."""
        raise NotImplementedError
