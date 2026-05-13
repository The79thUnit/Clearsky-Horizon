"""ICD 206 (2023) Source Reference Citation format.

A complete SRC must include:
  - unambiguous source identifier
  - source descriptor (quality/credibility factors via NATO score)
  - title of intelligence report
  - date of issuance
  - classification

For public-health surveillance, classification is always 'PUBLIC'.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .nato import NATOScore


@dataclass(frozen=True, slots=True)
class SRCCitation:
    """ICD 206 Source Reference Citation."""

    source_code: str
    source_name: str
    nato_score: NATOScore
    title: str
    issued_on: date | None
    classification: str = "PUBLIC"

    def format(self) -> str:
        date_str = self.issued_on.isoformat() if self.issued_on else "undated"
        return (
            f"[{self.classification}] "
            f"{self.source_code} ({self.nato_score.code}) "
            f'"{self.title}" '
            f"{self.source_name}, {date_str}"
        )

    def __str__(self) -> str:
        return self.format()
