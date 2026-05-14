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

Independence principle (STANAG 2511 §4): reliability and credibility MUST be
assessed independently. A completely reliable source (A) can produce improbable
information (A5). An unreliable source (E) can produce confirmed information (E1).
Never anchor the credibility score to the reliability grade.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final


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

# Maximum total adjustment that multipliers can apply to the base confidence.
# This prevents compounding factors from producing absurd results while still
# making the decomposition meaningful.
_MAX_ADJUSTMENT: Final[float] = 0.15


def adjusted_confidence(
    base: float,
    *,
    lag_hours: float = 0.0,
    corroboration_count: int = 0,
    fetch_completeness: float = 1.0,
    is_peak_season: bool = False,
    round_number_count: bool = False,
) -> tuple[float, dict[str, Any]]:
    """Apply epidemiological multipliers to the base NATO confidence score.

    Returns (adjusted_confidence, pipeline_factors_dict) where the dict
    implements a lightweight Analysis of Competing Hypotheses (ACH) structure.
    The leading hypothesis is the one with the highest consistency score.

    Args:
        base: Base confidence from BASE_CONFIDENCE[rel][cred].
        lag_hours: Hours between reported_date and ingest time. Older signals
            are less operationally relevant; confidence is penalised beyond 72h.
        corroboration_count: Number of additional independent sources reporting
            the same signal. Each adds a small corroboration bonus.
        fetch_completeness: Source fetch completeness ratio (0-1) over the last
            7 days. Sources below 90% completeness receive a small penalty.
        is_peak_season: True when the report date falls within the known seasonal
            peak for the detected serotype+region combination.
        round_number_count: True when case_count is a suspiciously round number
            (100, 500, 1000, etc.), raising the data-entry-error prior.
    """
    # Temporal lag penalty: -0.01 per 24h beyond 72h, capped at -0.10.
    lag_penalty = 0.0
    if lag_hours > 72:
        lag_penalty = min(0.10, (lag_hours - 72) / 24 * 0.01)

    # Corroboration bonus: +0.02 per additional confirming source, cap +0.08.
    corroboration_bonus = min(0.08, corroboration_count * 0.02)

    # Source completeness penalty: if <90% of expected fetches succeeded.
    completeness_penalty = 0.05 if fetch_completeness < 0.90 else 0.0

    total_adjustment = corroboration_bonus - lag_penalty - completeness_penalty
    # Clamp adjustment to the allowed window
    total_adjustment = max(-_MAX_ADJUSTMENT, min(_MAX_ADJUSTMENT, total_adjustment))
    adjusted = round(max(0.0, min(1.0, base + total_adjustment)), 4)

    # ACH hypothesis priors -- rule-based, not ML. A Phase 4+ layer can
    # replace these priors with trained weights without changing the schema.
    h_legitimate = round(adjusted, 4)
    # Reporting artefact is more likely when there is high lag or low source completeness
    h_artefact = round(min(0.50, (lag_penalty * 4) + (completeness_penalty * 2) + 0.05), 4)
    # Seasonal variation is more likely when we are in the known peak season
    h_seasonal = round(0.20 if is_peak_season else 0.07, 4)
    # Data entry error prior rises for suspiciously round case counts
    h_entry_error = round(0.08 if round_number_count else 0.03, 4)

    # Normalise so that hypotheses are relative probabilities (not required to
    # sum to 1 -- they represent independent consistency scores, not a partition).
    leading = max(
        {"legitimate_outbreak": h_legitimate, "reporting_artefact": h_artefact,
         "seasonal_normal": h_seasonal, "data_entry_error": h_entry_error},
        key=lambda k: {"legitimate_outbreak": h_legitimate, "reporting_artefact": h_artefact,
                       "seasonal_normal": h_seasonal, "data_entry_error": h_entry_error}[k],
    )

    factors: dict[str, Any] = {
        "hypotheses": {
            "legitimate_outbreak": h_legitimate,
            "reporting_artefact": h_artefact,
            "seasonal_normal": h_seasonal,
            "data_entry_error": h_entry_error,
        },
        "leading_hypothesis": leading,
        "base_nato_confidence": round(base, 4),
        "lag_penalty": round(lag_penalty, 4),
        "corroboration_bonus": round(corroboration_bonus, 4),
        "completeness_penalty": round(completeness_penalty, 4),
        "adjusted_confidence": adjusted,
    }
    return adjusted, factors


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
