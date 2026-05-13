"""Shared types for connector outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ParsedItem:
    """A single ingest-ready item produced by a connector.

    `raw_content` holds the canonical per-item bytes used for chain-of-custody
    hashing. For RSS feeds this is typically link + title + pubdate concatenated.
    For JSON APIs it is the per-item JSON serialised back to bytes.
    """

    external_id: str
    title: str
    summary: str | None
    country_iso2: str | None
    region: str | None
    lat: float | None
    lng: float | None
    serotype_text: str | None
    reported_date: date | None
    case_count: int | None
    death_count: int | None
    raw_url: str
    raw_content: bytes
