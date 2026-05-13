"""Cluster auto-detection.

A cluster is N>=2 case_reports sharing:
  - country_iso2 (not NULL)
  - serotype (text code; None grouped together as 'unknown serotype')
  - reported_date within CLUSTER_WINDOW_DAYS of the cluster's first case

Starter heuristic. Phase 3+ may upgrade to proper outbreak-detection
(SaTScan, EARS-X, CUSUM, etc).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

CLUSTER_WINDOW_DAYS: Final[int] = 14
MIN_CASES_FOR_CLUSTER: Final[int] = 2


@dataclass(frozen=True, slots=True)
class CaseFingerprint:
    """Minimal case info needed for clustering. Decoupled from DB ORM."""

    case_id: str
    country_iso2: str | None
    serotype_text: str | None
    reported_date: date | None


@dataclass(frozen=True, slots=True)
class DetectedCluster:
    """A cluster derived from a group of cases. Ready to upsert."""

    country_iso2: str
    serotype_code: str | None
    case_ids: tuple[str, ...]
    started_at: date
    ended_at: date
    name: str

    @property
    def case_count(self) -> int:
        return len(self.case_ids)


def _cluster_key(case: CaseFingerprint) -> tuple[str, str | None] | None:
    """Return clustering key, or None if case is not clusterable."""
    if not case.country_iso2 or case.reported_date is None:
        return None
    return (case.country_iso2, case.serotype_text)


def _make_cluster(
    country: str,
    serotype: str | None,
    cases: list[CaseFingerprint],
) -> DetectedCluster:
    dates = [c.reported_date for c in cases if c.reported_date is not None]
    started = min(dates)
    ended = max(dates)
    label = f"{country} {serotype or 'hantavirus'} cluster {started.isoformat()}"
    return DetectedCluster(
        country_iso2=country,
        serotype_code=serotype,
        case_ids=tuple(c.case_id for c in cases),
        started_at=started,
        ended_at=ended,
        name=label,
    )


def detect_clusters(
    cases: list[CaseFingerprint],
    *,
    window_days: int = CLUSTER_WINDOW_DAYS,
    min_cases: int = MIN_CASES_FOR_CLUSTER,
) -> list[DetectedCluster]:
    """Group cases by (country, serotype) then split into time-windowed clusters.

    Pure function. No DB calls. Deterministic for any given input ordering of
    `cases` (internal sort makes output order-independent).
    """
    if window_days < 1:
        raise ValueError("window_days must be >= 1")
    if min_cases < 2:
        raise ValueError("min_cases must be >= 2")

    groups: dict[tuple[str, str | None], list[CaseFingerprint]] = {}
    for case in cases:
        key = _cluster_key(case)
        if key is None:
            continue
        groups.setdefault(key, []).append(case)

    clusters: list[DetectedCluster] = []
    for (country, serotype), group in groups.items():
        # All cases in this group are guaranteed by _cluster_key to have a
        # non-None reported_date and country_iso2. We re-check for the type
        # checker rather than asserting (bandit B101).
        sorted_cases = sorted(group, key=lambda c: (c.reported_date, c.case_id))

        current: list[CaseFingerprint] = []
        for case in sorted_cases:
            case_date = case.reported_date
            if case_date is None:
                continue
            if not current:
                current.append(case)
                continue
            window_start = current[0].reported_date
            if window_start is None:
                continue
            if (case_date - window_start).days <= window_days:
                current.append(case)
            else:
                if len(current) >= min_cases:
                    clusters.append(_make_cluster(country, serotype, current))
                current = [case]
        if len(current) >= min_cases:
            clusters.append(_make_cluster(country, serotype, current))

    return clusters
