"""Dual confidence model.

pipeline_confidence: auto-calculated from NATO score + corroboration + recency.
                     Bounded [0.0, 0.99]. Never 1.0 without analyst review.

analyst_confidence:  set by human analyst after review.
                     Stored separately. UI surfaces both side by side.

This is HORIZON's primary differentiator. Every change requires a new ADR
and Phoenix sign-off (see docs/adr/0002-qualification-model.md).

The pipeline_factors JSONB column carries a structured decomposition of every
score, including an Analysis of Competing Hypotheses (ACH) section. ACH is
standard practice in intelligence analysis (Richards Heuer, 1999) and directly
maps to outbreak surveillance: the leading hypothesis for any signal is
'legitimate_outbreak', but the pipeline also scores three competing hypotheses
using rule-based priors. Analysts see both the score and the ACH breakdown,
which prevents confirmation bias on high-confidence automated outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    # ACH contextual hints (optional -- all existing callers work with defaults)
    is_peak_season: bool = False       # True when report date is in known seasonal peak
    round_number_count: bool = False   # True when case_count is a suspiciously round number


@dataclass(frozen=True, slots=True)
class QualificationResult:
    nato: NATOScore
    pipeline_confidence: float
    factors: dict[str, Any]


def calculate(inputs: QualificationInputs) -> QualificationResult:
    """Compute pipeline confidence + ACH hypothesis factors.

    Pure, deterministic, no side effects.

    The returned `factors` dict has two sections:
    - Classic scoring: nato_code, base_confidence, corroboration, recency decay
    - ACH hypotheses: per-hypothesis consistency scores + leading hypothesis

    ACH priors are rule-based (not ML). They give structure to the output from
    day one; a Phase 4+ ML layer can replace the priors with trained weights
    without changing the schema or the API contract.
    """
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

    # ACH hypothesis priors
    # -----------------------------------------------------------------------
    # 'legitimate_outbreak': primary hypothesis. Scored equal to the adjusted
    #   pipeline confidence.
    # 'reporting_artefact': elevated when source is old (high age_days) or
    #   corroboration is zero from a non-Tier-1 source (implied by low base).
    # 'seasonal_normal': elevated when the report falls within known peak season
    #   for the serotype+region combination (caller must set is_peak_season).
    # 'data_entry_error': elevated when case_count is a suspiciously round number.
    h_legitimate = round(min(PIPELINE_CONFIDENCE_CAP, confidence), 4)
    h_artefact = round(min(0.50, (decay_days * 0.002) + (0.08 if base < 0.60 else 0.03)), 4)
    h_seasonal = round(0.25 if inputs.is_peak_season else 0.07, 4)
    h_entry_error = round(0.10 if inputs.round_number_count else 0.03, 4)

    _hyp = {
        "legitimate_outbreak": h_legitimate,
        "reporting_artefact": h_artefact,
        "seasonal_normal": h_seasonal,
        "data_entry_error": h_entry_error,
    }
    leading_hypothesis = max(_hyp, key=lambda k: _hyp[k])

    factors: dict[str, Any] = {
        # Classic scoring (retained for backwards compatibility)
        "nato_code": inputs.nato.code,
        "base_confidence": round(base, 4),
        "corroboration_count": inputs.corroboration_count,
        "corroboration_boost": round(corroboration_boost, 4),
        "age_days": inputs.age_days,
        "recency_decay": round(recency_decay, 4),
        "raw": round(raw, 4),
        "cap": PIPELINE_CONFIDENCE_CAP,
        "final": round(confidence, 4),
        # ACH hypothesis section (Pass 3)
        "hypotheses": _hyp,
        "leading_hypothesis": leading_hypothesis,
    }

    return QualificationResult(
        nato=inputs.nato,
        pipeline_confidence=round(confidence, 2),
        factors=factors,
    )
