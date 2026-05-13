"""Tests for cluster auto-detection."""

from datetime import date, timedelta

import pytest
from horizon_worker.core.clustering import (
    CLUSTER_WINDOW_DAYS,
    MIN_CASES_FOR_CLUSTER,
    CaseFingerprint,
    detect_clusters,
)

BASE_DATE = date(2026, 5, 1)


def _case(
    case_id: str,
    country: str | None,
    serotype: str | None,
    day_offset: int | None,
) -> CaseFingerprint:
    """Create a fingerprint. `day_offset` is days from BASE_DATE; None = no date."""
    return CaseFingerprint(
        case_id=case_id,
        country_iso2=country,
        serotype_text=serotype,
        reported_date=(BASE_DATE + timedelta(days=day_offset - 1))
        if day_offset is not None
        else None,
    )


class TestBasicGrouping:
    def test_two_cases_same_country_same_serotype_within_window(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 8),
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 1
        cluster = clusters[0]
        assert cluster.country_iso2 == "AR"
        assert cluster.serotype_code == "ANDV"
        assert set(cluster.case_ids) == {"a", "b"}
        assert cluster.case_count == 2
        assert cluster.started_at == date(2026, 5, 1)
        assert cluster.ended_at == date(2026, 5, 8)
        assert "AR ANDV cluster 2026-05-01" in cluster.name

    def test_single_case_not_a_cluster(self) -> None:
        assert detect_clusters([_case("a", "AR", "ANDV", 1)]) == []

    def test_three_cases_same_window(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 5),
            _case("c", "AR", "ANDV", 10),
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 1
        assert clusters[0].case_count == 3


class TestWindowing:
    def test_outside_window_splits_into_two_clusters(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 8),
            _case("c", "AR", "ANDV", 30),
            _case("d", "AR", "ANDV", 35),
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 2
        first = next(c for c in clusters if c.started_at == date(2026, 5, 1))
        second = next(c for c in clusters if c.started_at == date(2026, 5, 30))
        assert set(first.case_ids) == {"a", "b"}
        assert set(second.case_ids) == {"c", "d"}

    def test_exactly_at_window_boundary_included(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 1 + CLUSTER_WINDOW_DAYS),
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 1
        assert clusters[0].case_count == 2

    def test_one_day_past_window_breaks_cluster(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 2 + CLUSTER_WINDOW_DAYS),
        ]
        assert detect_clusters(cases) == []


class TestKeyDifferences:
    def test_different_countries_dont_cluster(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "CL", "ANDV", 2),
        ]
        assert detect_clusters(cases) == []

    def test_different_serotypes_dont_cluster(self) -> None:
        cases = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "SNV", 2),
        ]
        assert detect_clusters(cases) == []

    def test_unknown_serotype_clusters_together(self) -> None:
        cases = [
            _case("a", "AR", None, 1),
            _case("b", "AR", None, 5),
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 1
        assert clusters[0].serotype_code is None
        assert "hantavirus" in clusters[0].name


class TestExclusions:
    def test_no_country_excluded(self) -> None:
        cases = [
            _case("a", None, "ANDV", 1),
            _case("b", None, "ANDV", 2),
        ]
        assert detect_clusters(cases) == []

    def test_no_date_excluded(self) -> None:
        # Two cases but one missing date -> only one valid -> no cluster
        cases = [
            _case("a", "AR", "ANDV", None),
            _case("b", "AR", "ANDV", 1),
        ]
        assert detect_clusters(cases) == []

    def test_mixed_valid_and_excluded(self) -> None:
        cases = [
            _case("a", None, "ANDV", 1),  # excluded
            _case("b", "AR", "ANDV", 2),  # valid
            _case("c", "AR", "ANDV", 3),  # valid
            _case("d", "AR", "ANDV", None),  # excluded
        ]
        clusters = detect_clusters(cases)
        assert len(clusters) == 1
        assert set(clusters[0].case_ids) == {"b", "c"}


class TestOrderIndependence:
    def test_input_order_does_not_affect_output(self) -> None:
        forward = [
            _case("a", "AR", "ANDV", 1),
            _case("b", "AR", "ANDV", 5),
            _case("c", "AR", "ANDV", 10),
        ]
        reverse = list(reversed(forward))
        c1 = detect_clusters(forward)
        c2 = detect_clusters(reverse)
        assert len(c1) == len(c2) == 1
        assert set(c1[0].case_ids) == set(c2[0].case_ids)
        assert c1[0].started_at == c2[0].started_at == date(2026, 5, 1)
        assert c1[0].ended_at == c2[0].ended_at == date(2026, 5, 10)


class TestValidation:
    def test_invalid_window_days(self) -> None:
        with pytest.raises(ValueError, match="window_days"):
            detect_clusters([], window_days=0)

    def test_invalid_min_cases(self) -> None:
        with pytest.raises(ValueError, match="min_cases"):
            detect_clusters([], min_cases=1)


class TestConstantsSanity:
    def test_window_days_positive(self) -> None:
        assert CLUSTER_WINDOW_DAYS >= 1

    def test_min_cases_at_least_two(self) -> None:
        assert MIN_CASES_FOR_CLUSTER >= 2
