"""Tests for ICD 206 SRC formatting."""

from datetime import date

from horizon_worker.core.nato import NATOScore
from horizon_worker.core.src_citation import SRCCitation


def test_format_with_date() -> None:
    citation = SRCCitation(
        source_code="promed-rss",
        source_name="ProMED-mail RSS",
        nato_score=NATOScore.parse("B2"),
        title="Hantavirus, Argentina (Chubut)",
        issued_on=date(2026, 5, 4),
    )
    rendered = str(citation)
    assert "[PUBLIC]" in rendered
    assert "promed-rss" in rendered
    assert "(B2)" in rendered
    assert "Hantavirus, Argentina (Chubut)" in rendered
    assert "2026-05-04" in rendered


def test_format_without_date() -> None:
    citation = SRCCitation(
        source_code="cdc-han",
        source_name="CDC HAN",
        nato_score=NATOScore.parse("A1"),
        title="MV Hondius cluster",
        issued_on=None,
    )
    assert "undated" in str(citation)


def test_custom_classification() -> None:
    citation = SRCCitation(
        source_code="internal-note",
        source_name="Analyst desk note",
        nato_score=NATOScore.parse("C3"),
        title="working hypothesis",
        issued_on=date(2026, 5, 11),
        classification="INTERNAL",
    )
    assert "[INTERNAL]" in str(citation)
