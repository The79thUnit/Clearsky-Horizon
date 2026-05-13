"""Dual confidence model.

pipeline_confidence: auto-calculated from NATO score + corroboration + recency.
                     Bounded [0.0, 0.99]. Never 1.0 without analyst review.

analyst_confidence:  set by human analyst after review.
                     Stored separately. UI surfaces both side by side.

This is HORIZON's primary differentiator. Every change requires a new ADR
and Phoenix sign-off (see docs/adr/0002-qualification-model.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from .nato import NATOScore

PIPELINE_CONFIDENCE_CAP: Final[float] = 0.99

CORROBORATION_PER_SOURCE: Final[float] = 0.02
CORROBORATION_MAX_BOOST: Final[float] = 0.10

RECENCY_GRACE_DAYS: Final[int] = 7
RECENCY_DECAY_PER_DAY: Final[float] = 0.001
RECENCY_MAX_DECAY: Final[float] = 0.05


@dataclass(frozen=True, slots=True)
class QualificationInputs:
    nato: NATOScore
    corroboration_count: int = 0
    age_days: int = 0


@dataclass(frozen=True, slots=True)
class QualificationResult:
    nato: NATOScore
    pipeline_confidence: float
    factors: dict[str, Any]


def calculate(inputs: QualificationInputs) -> QualificationResult:
    """Compute pipeline confidence. Pure, deterministic, no side effects."""
    if inputs.corroboration_count < 0:
        raise ValueError("corroboration_count must be >= 0")
    if inputs.age_days < 0:
        raise ValueError("age_days must be >= 0")

    base = inputs.nato.base_confidence

    corroboration_boost = min(
        inputs.corroboration_count * CORROBORATION_PER_SOURCE,
        CORROBORATION_MAX_BOOST,
    )

    decay_days = max(0, inputs.age_days - RECENCY_GRACE_DAYS)
    recency_decay = -min(decay_days * RECENCY_DECAY_PER_DAY, RECENCY_MAX_DECAY)

    raw = base + corroboration_boost + recency_decay
    confidence = max(0.0, min(PIPELINE_CONFIDENCE_CAP, raw))

    factors: dict[str, Any] = {
        "nato_code": inputs.nato.code,
        "base_confidence": round(base, 4),
        "corroboration_count": inputs.corroboration_count,
        "corroboration_boost": round(corroboration_boost, 4),
        "age_days": inputs.age_days,
        "recency_decay": round(recency_decay, 4),
        "raw": round(raw, 4),
        "cap": PIPELINE_CONFIDENCE_CAP,
        "final": round(confidence, 4),
    }

    return QualificationResult(
        nato=inputs.nato,
        pipeline_confidence=round(confidence, 2),
        factors=factors,
    )
