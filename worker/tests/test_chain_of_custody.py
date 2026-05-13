"""Tests for Berkeley Protocol chain-of-custody attestation."""

from datetime import UTC, datetime

import pytest
from horizon_worker.core.chain_of_custody import (
    attest,
    compute_hash,
)


class TestComputeHash:
    def test_bytes_deterministic(self) -> None:
        assert compute_hash(b"hello world") == compute_hash(b"hello world")

    def test_str_same_as_bytes_utf8(self) -> None:
        assert compute_hash("hello") == compute_hash(b"hello")

    def test_different_payloads_different_hashes(self) -> None:
        assert compute_hash("a") != compute_hash("b")

    def test_hash_is_sha256_hex_length(self) -> None:
        assert len(compute_hash("anything")) == 64

    def test_empty_payload(self) -> None:
        # Empty SHA-256 is a well-known digest
        assert compute_hash(b"") == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )


class TestAttest:
    def test_defaults_to_utc_now(self) -> None:
        record = attest(
            raw_url="https://example.com/x",
            payload=b"<rss/>",
            parser_version="0.1.0",
        )
        assert record.captured_at.tzinfo == UTC

    def test_explicit_captured_at(self) -> None:
        ts = datetime(2026, 5, 11, 12, 0, 0, tzinfo=UTC)
        record = attest(
            raw_url="https://example.com/x",
            payload=b"<rss/>",
            parser_version="0.1.0",
            captured_at=ts,
        )
        assert record.captured_at == ts

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            attest(
                raw_url="https://example.com",
                payload=b"<rss/>",
                parser_version="0.1.0",
                captured_at=datetime(2026, 5, 11, 12, 0, 0),  # noqa: DTZ001
            )

    def test_round_trip_to_dict(self) -> None:
        record = attest(
            raw_url="https://example.com",
            payload="hello",
            parser_version="0.1.0",
        )
        d = record.to_dict()
        assert d["raw_url"] == "https://example.com"
        assert d["raw_content_hash"] == compute_hash("hello")
        assert d["parser_version"] == "0.1.0"
        assert "captured_at" in d
