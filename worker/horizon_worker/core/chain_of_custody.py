"""Berkeley Protocol chain-of-custody for ingested records.

UN/UC Berkeley Human Rights Center Protocol on Digital Open Source Investigations
requires every collected item to have:
  - timestamp of capture (UTC)
  - URL of origin
  - integrity hash of original payload (SHA-256)
  - parser version (for forensic reproducibility)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ChainOfCustody:
    """Forensic provenance record for one ingested item."""

    raw_url: str
    raw_content_hash: str
    captured_at: datetime
    parser_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "raw_url": self.raw_url,
            "raw_content_hash": self.raw_content_hash,
            "captured_at": self.captured_at.isoformat(),
            "parser_version": self.parser_version,
        }


def compute_hash(payload: bytes | str) -> str:
    """SHA-256 hex digest of bytes or UTF-8 string."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def attest(
    raw_url: str,
    payload: bytes | str,
    parser_version: str,
    captured_at: datetime | None = None,
) -> ChainOfCustody:
    """Produce a chain-of-custody record. captured_at defaults to UTC now."""
    if captured_at is None:
        captured_at = datetime.now(tz=UTC)
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    return ChainOfCustody(
        raw_url=raw_url,
        raw_content_hash=compute_hash(payload),
        captured_at=captured_at,
        parser_version=parser_version,
    )
