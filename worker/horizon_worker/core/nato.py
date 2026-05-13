"""NATO Admiralty Scale (STANAG 2511) for source reliability and credibility.

Reliability:
    A - Completely reliable
    B - Usually reliable
    C - Fairly reliable
    D - Not usually reliable
    E - Unreliable
    F - Reliability cannot be judged

Credibility:
    1 - Confirmed by other independent sources
    2 - Probably true
    3 - Possibly true
    4 - Doubtful
    5 - Improbable
    6 - Truth cannot be judged

ICD 206 (2023) Source Reference Citation descriptors map directly to these scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class Reliability(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class Credibility(int, Enum):
    CONFIRMED = 1
    PROBABLY_TRUE = 2
    POSSIBLY_TRUE = 3
    DOUBTFUL = 4
    IMPROBABLE = 5
    UNJUDGED = 6


# Base pipeline confidence per NATO score.
# Calibrated against ICD 206 examples and Bellingcat verification-handbook 5-step.
# A1 (most reliable) = 0.95. F6 (least judgeable) = 0.25.
# Never reaches 1.0 from automation alone. Human analyst review is required for that.
BASE_CONFIDENCE: Final[dict[str, dict[int, float]]] = {
    "A": {1: 0.95, 2: 0.88, 3: 0.78, 4: 0.55, 5: 0.35, 6: 0.50},
    "B": {1: 0.88, 2: 0.82, 3: 0.72, 4: 0.50, 5: 0.32, 6: 0.45},
    "C": {1: 0.78, 2: 0.72, 3: 0.62, 4: 0.45, 5: 0.28, 6: 0.40},
    "D": {1: 0.55, 2: 0.50, 3: 0.45, 4: 0.35, 5: 0.22, 6: 0.30},
    "E": {1: 0.35, 2: 0.32, 3: 0.28, 4: 0.22, 5: 0.15, 6: 0.20},
    "F": {1: 0.50, 2: 0.45, 3: 0.40, 4: 0.30, 5: 0.20, 6: 0.25},
}


@dataclass(frozen=True, slots=True)
class NATOScore:
    """A NATO Admiralty Scale rating."""

    reliability: Reliability
    credibility: Credibility

    @classmethod
    def parse(cls, code: str) -> NATOScore:
        if not isinstance(code, str) or len(code) != 2:
            raise ValueError(f"NATO code must be 2 chars (e.g. 'A1'), got {code!r}")
        try:
            rel = Reliability(code[0].upper())
        except ValueError as exc:
            raise ValueError(f"Reliability must be A-F, got {code[0]!r}") from exc
        try:
            cred = Credibility(int(code[1]))
        except (ValueError, KeyError) as exc:
            raise ValueError(f"Credibility must be 1-6, got {code[1]!r}") from exc
        return cls(rel, cred)

    @property
    def code(self) -> str:
        return f"{self.reliability.value}{self.credibility.value}"

    @property
    def base_confidence(self) -> float:
        return BASE_CONFIDENCE[self.reliability.value][self.credibility.value]

    def __str__(self) -> str:
        return self.code
