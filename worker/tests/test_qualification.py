"""Tests for the dual confidence qualification module.

These tests defend the differentiator. Treat any failure here as a release blocker.
"""

import pytest
from horizon_worker.core.nato import Credibility, NATOScore, Reliability
from horizon_worker.core.qualification import (
    CORROBORATION_MAX_BOOST,
    PIPELINE_CONFIDENCE_CAP,
    RECENCY_GRACE_DAYS,
    RECENCY_MAX_DECAY,
    QualificationInputs,
    calculate,
)


class TestNATOScore:
    @pytest.mark.parametrize(
        ("code", "expected_rel", "expected_cred"),
        [
            ("A1", Reliability.A, Credibility.CONFIRMED),
            ("B2", Reliability.B, Credibility.PROBABLY_TRUE),
            ("F6", Reliability.F, Credibility.UNJUDGED),
        ],
    )
    def test_parse_valid(
        self, code: str, expected_rel: Reliability, expected_cred: Credibility
    ) -> None:
        score = NATOScore.parse(code)
        assert score.reliability == expected_rel
        assert score.credibility == expected_cred
        assert score.code == code
        assert str(score) == code

    def test_parse_lowercase_normalises(self) -> None:
        assert NATOScore.parse("a1").code == "A1"

    @pytest.mark.parametrize("bad", ["", "A", "A12", "Z1", "A0", "A7", "AA", "11"])
    def test_parse_invalid_raises(self, bad: str) -> None:
        with pytest.raises(ValueError):
            NATOScore.parse(bad)

    def test_base_confidence_descends_with_reliability(self) -> None:
        # A > B > C > D > E for credibility = 1
        confidences = [NATOScore.parse(f"{r}1").base_confidence for r in "ABCDE"]
        assert confidences == sorted(confidences, reverse=True)

    def test_base_confidence_descends_with_credibility(self) -> None:
        # 1 > 2 > 3 > 4 > 5 for reliability = A
        confidences = [NATOScore.parse(f"A{c}").base_confidence for c in range(1, 6)]
        assert confidences == sorted(confidences, reverse=True)


class TestCalculate:
    def test_a1_no_corroboration_recent(self) -> None:
        result = calculate(QualificationInputs(nato=NATOScore.parse("A1")))
        assert result.pipeline_confidence == 0.95
        assert result.factors["nato_code"] == "A1"
        assert result.factors["corroboration_boost"] == 0
        assert result.factors["recency_decay"] == 0

    def test_corroboration_boost_bounded(self) -> None:
        score = NATOScore.parse("B2")
        result = calculate(QualificationInputs(nato=score, corroboration_count=100))
        expected = min(
            score.base_confidence + CORROBORATION_MAX_BOOST,
            PIPELINE_CONFIDENCE_CAP,
        )
        assert result.pipeline_confidence == round(expected, 2)
        assert result.factors["corroboration_boost"] == CORROBORATION_MAX_BOOST

    def test_recency_grace_window(self) -> None:
        for age in range(RECENCY_GRACE_DAYS + 1):
            result = calculate(QualificationInputs(nato=NATOScore.parse("A1"), age_days=age))
            assert result.factors["recency_decay"] == 0

    def test_recency_decay_kicks_in_after_grace(self) -> None:
        result = calculate(
            QualificationInputs(
                nato=NATOScore.parse("A1"),
                age_days=RECENCY_GRACE_DAYS + 10,
            )
        )
        assert result.factors["recency_decay"] < 0

    def test_recency_decay_bounded(self) -> None:
        result = calculate(QualificationInputs(nato=NATOScore.parse("A1"), age_days=10_000))
        assert result.factors["recency_decay"] == -RECENCY_MAX_DECAY

    def test_never_reaches_one_from_automation(self) -> None:
        result = calculate(
            QualificationInputs(
                nato=NATOScore.parse("A1"),
                corroboration_count=1000,
                age_days=0,
            )
        )
        assert result.pipeline_confidence <= PIPELINE_CONFIDENCE_CAP

    def test_never_negative(self) -> None:
        result = calculate(QualificationInputs(nato=NATOScore.parse("F6"), age_days=100_000))
        assert result.pipeline_confidence >= 0.0

    def test_invalid_corroboration_count(self) -> None:
        with pytest.raises(ValueError, match="corroboration_count"):
            calculate(QualificationInputs(nato=NATOScore.parse("A1"), corroboration_count=-1))

    def test_invalid_age_days(self) -> None:
        with pytest.raises(ValueError, match="age_days"):
            calculate(QualificationInputs(nato=NATOScore.parse("A1"), age_days=-1))

    def test_factors_contain_full_trace(self) -> None:
        result = calculate(
            QualificationInputs(
                nato=NATOScore.parse("C3"),
                corroboration_count=2,
                age_days=14,
            )
        )
        expected_keys = {
            "nato_code",
            "base_confidence",
            "corroboration_count",
            "corroboration_boost",
            "age_days",
            "recency_decay",
            "raw",
            "cap",
            "final",
        }
        assert set(result.factors.keys()) == expected_keys
