"""Shared types for connector outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class ParsedItem:
    """A single ingest-ready item produced by a connector.

    `raw_content` holds the canonical per-item bytes used for chain-of-custody
    hashing. For RSS feeds this is typically link + title + pubdate concatenated.
    For JSON APIs it is the per-item JSON serialised back to bytes.

    `case_classification` follows the WHO/CDC/ECDC tripartite definition:
      - 'confirmed': lab-confirmed (IgM, IgG 4-fold rise, RT-PCR, or IHC)
      - 'probable':  compatible clinical presentation + epidemiological link
      - 'suspected': compatible presentation, no lab confirmation or epi link
      - 'unknown':   default for automated ingest where classification is unclear

    `lab_method` records the diagnostic method when available:
      igm | igg_4x | rt_pcr | ihc | none | unknown
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
    # Epidemiological classification fields (Pass 2). Defaults keep all
    # existing connectors working without modification.
    case_classification: str = "unknown"
    lab_method: str = "unknown"
