"""Berkeley Protocol chain-of-custody for ingested records.

UN/UC Berkeley Human Rights Center Protocol on Digital Open Source Investigations
(OHCHR/UC Berkeley Law, 2020) requires every collected item to have:
  - timestamp of capture (UTC, millisecond precision)
  - URL of origin (immutable at capture time)
  - integrity hash of original payload (SHA-256 of raw bytes)
  - hash of HTTP response headers (proves server-side delivery integrity)
  - capture tool name and version (reproducibility)
  - collection activity type (audit trail)

The SHA-256 content hash proves the stored bytes are intact since storage.
The http_headers_hash proves the stored bytes match what the server delivered.
Together they close the gap between "we stored this faithfully" and "the source
published this faithfully" -- required for forensic defensibility under
adversarial challenge.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

# Canonical tool identifier written into every custody record.
# Bump the version suffix when the ingest pipeline changes materially.
CAPTURE_TOOL: str = "horizon-worker/0.3.0"


@dataclass(frozen=True, slots=True)
class ChainOfCustody:
    """Forensic provenance record for one ingested item (Berkeley Protocol)."""

    raw_url: str
    raw_content_hash: str
    captured_at: datetime
    parser_version: str
    # Extended Berkeley Protocol fields
    http_headers_hash: str | None = None
    capture_tool: str = CAPTURE_TOOL
    collection_activity: str = "automated_scrape"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "raw_url": self.raw_url,
            "raw_content_hash": self.raw_content_hash,
            "captured_at": self.captured_at.isoformat(timespec="milliseconds"),
            "parser_version": self.parser_version,
            "http_headers_hash": self.http_headers_hash,
            "capture_tool": self.capture_tool,
            "collection_activity": self.collection_activity,
        }


def compute_hash(payload: bytes | str) -> str:
    """SHA-256 hex digest of bytes or UTF-8 string."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def hash_headers(headers: dict[str, str] | None) -> str | None:
    """SHA-256 of HTTP response headers serialised as sorted JSON.

    Sorting is required for determinism -- header order is not guaranteed
    by the HTTP spec. Returns None if no headers were captured.
    """
    if not headers:
        return None
    normalised = {k.lower(): v for k, v in headers.items()}
    canonical = json.dumps(normalised, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def attest(
    raw_url: str,
    payload: bytes | str,
    parser_version: str,
    captured_at: datetime | None = None,
    response_headers: dict[str, str] | None = None,
    collection_activity: str = "automated_scrape",
) -> ChainOfCustody:
    """Produce a Berkeley Protocol chain-of-custody record.

    Args:
        raw_url: The URL the content was fetched from (immutable).
        payload: Raw bytes or string content at capture time.
        parser_version: Connector parser version string.
        captured_at: UTC datetime of capture; defaults to now.
        response_headers: HTTP response headers from the fetch (optional).
        collection_activity: How this record entered the system.
    """
    if captured_at is None:
        captured_at = datetime.now(tz=UTC)
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    return ChainOfCustody(
        raw_url=raw_url,
        raw_content_hash=compute_hash(payload),
        captured_at=captured_at,
        parser_version=parser_version,
        http_headers_hash=hash_headers(response_headers),
        capture_tool=CAPTURE_TOOL,
        collection_activity=collection_activity,
    )
