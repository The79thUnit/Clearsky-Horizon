"""Unit tests for cluster persistence in tasks/ingest.

DB-bound integration testing is deferred to Phase 4 when testcontainers
gets wired up. These tests use mocks to verify the SQL paths and the
recompute orchestration call sequence.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

from horizon_worker.core.clustering import DetectedCluster
from horizon_worker.tasks.ingest import (
    CASE_TO_CLUSTER_DEFAULT_CONFIDENCE,
    CLUSTER_LOOKBACK_DAYS,
    _fetch_fingerprints,
    _upsert_cluster,
    recompute_clusters_for_keys,
)


def _mock_conn_with_cursor() -> tuple[MagicMock, MagicMock]:
    """Return (conn, cur) with the standard psycopg context-manager wiring."""
    cur = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False
    return conn, cur


class TestFetchFingerprints:
    def test_serotype_known_uses_equality_filter(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchall.return_value = []

        _fetch_fingerprints(conn, "AR", "ANDV")

        sql = cur.execute.call_args[0][0]
        params: tuple[Any, ...] = cur.execute.call_args[0][1]
        assert "serotype_text = %s" in sql
        assert "AR" in params
        assert "ANDV" in params
        assert CLUSTER_LOOKBACK_DAYS in params

    def test_serotype_none_uses_is_null(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchall.return_value = []

        _fetch_fingerprints(conn, "AR", None)

        sql = cur.execute.call_args[0][0]
        params: tuple[Any, ...] = cur.execute.call_args[0][1]
        assert "serotype_text IS NULL" in sql
        assert "AR" in params
        # The serotype value is NOT in the params (NULL branch)
        assert "ANDV" not in params

    def test_returns_fingerprints_from_rows(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchall.return_value = [
            {
                "id": "case-1",
                "country_iso2": "AR",
                "serotype_text": "ANDV",
                "reported_date": date(2026, 5, 1),
            },
            {
                "id": "case-2",
                "country_iso2": "AR",
                "serotype_text": "ANDV",
                "reported_date": date(2026, 5, 8),
            },
        ]

        fingerprints = _fetch_fingerprints(conn, "AR", "ANDV")

        assert len(fingerprints) == 2
        assert fingerprints[0].case_id == "case-1"
        assert fingerprints[1].case_id == "case-2"


class TestUpsertCluster:
    def _make_cluster(self, with_serotype: str | None = "ANDV") -> DetectedCluster:
        return DetectedCluster(
            country_iso2="AR",
            serotype_code=with_serotype,
            case_ids=("c1", "c2"),
            started_at=date(2026, 5, 1),
            ended_at=date(2026, 5, 8),
            name="AR ANDV cluster 2026-05-01",
        )

    def test_creates_new_cluster_when_not_found(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchone.side_effect = [
            {"id": "serotype-uuid"},  # serotype lookup
            None,  # find existing -> not found
            {"id": "new-cluster-uuid"},  # INSERT RETURNING
        ]

        cluster_id = _upsert_cluster(conn, self._make_cluster())

        assert cluster_id == "new-cluster-uuid"
        sqls = [str(c.args[0]) for c in cur.execute.call_args_list]
        assert any("INSERT INTO clusters" in s for s in sqls)
        # case_to_cluster called once per case (2 cases)
        case_to_cluster_calls = [s for s in sqls if "case_to_cluster" in s]
        assert len(case_to_cluster_calls) == 2

    def test_updates_existing_cluster(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchone.side_effect = [
            {"id": "serotype-uuid"},  # serotype lookup
            {"id": "existing-cluster-uuid"},  # find existing -> found
        ]

        cluster_id = _upsert_cluster(conn, self._make_cluster())

        assert cluster_id == "existing-cluster-uuid"
        sqls = [str(c.args[0]) for c in cur.execute.call_args_list]
        assert any("UPDATE clusters" in s for s in sqls)
        assert not any("INSERT INTO clusters" in s for s in sqls)

    def test_handles_null_serotype(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchone.side_effect = [
            None,  # find existing -> not found
            {"id": "new-cluster-uuid"},  # INSERT RETURNING
        ]
        # No serotype lookup happens because serotype_code is None
        cluster_id = _upsert_cluster(conn, self._make_cluster(with_serotype=None))

        assert cluster_id == "new-cluster-uuid"
        # 2 main SQL calls (find + insert) + 2 case-to-cluster = 4 total
        assert cur.execute.call_count == 4

    def test_case_to_cluster_uses_default_confidence(self) -> None:
        conn, cur = _mock_conn_with_cursor()
        cur.fetchone.side_effect = [
            {"id": "serotype-uuid"},
            None,
            {"id": "new-cluster-uuid"},
        ]

        _upsert_cluster(conn, self._make_cluster())

        # Find the case_to_cluster INSERT calls and check confidence param
        for call in cur.execute.call_args_list:
            sql = str(call.args[0])
            if "case_to_cluster" in sql:
                params = call.args[1]
                assert params[2] == CASE_TO_CLUSTER_DEFAULT_CONFIDENCE


class TestRecomputeClustersForKeys:
    def test_empty_keys_no_action(self) -> None:
        conn = MagicMock()
        summary = recompute_clusters_for_keys(conn, [])
        assert summary == {"upserted": 0}
        conn.cursor.assert_not_called()

    def test_summary_counts_upserts(self) -> None:
        # Two keys, each yielding fingerprints that produce 1 cluster.
        conn, cur = _mock_conn_with_cursor()

        # Both fingerprint fetches return 2 cases that should cluster
        cur.fetchall.side_effect = [
            # First key (AR, ANDV): 2 cases within 7 days
            [
                {
                    "id": "c1",
                    "country_iso2": "AR",
                    "serotype_text": "ANDV",
                    "reported_date": date(2026, 5, 1),
                },
                {
                    "id": "c2",
                    "country_iso2": "AR",
                    "serotype_text": "ANDV",
                    "reported_date": date(2026, 5, 5),
                },
            ],
            # Second key (CL, ANDV): 2 cases within 7 days
            [
                {
                    "id": "c3",
                    "country_iso2": "CL",
                    "serotype_text": "ANDV",
                    "reported_date": date(2026, 5, 2),
                },
                {
                    "id": "c4",
                    "country_iso2": "CL",
                    "serotype_text": "ANDV",
                    "reported_date": date(2026, 5, 6),
                },
            ],
        ]
        # For each cluster: serotype lookup + find existing (None) + INSERT
        # Each cluster also does 2 case_to_cluster INSERTs but fetchone is not
        # called for those.
        cur.fetchone.side_effect = [
            # Cluster 1 (AR ANDV)
            {"id": "serotype-andv-uuid"},  # serotype lookup
            None,  # find existing -> not found
            {"id": "cluster-ar-uuid"},  # INSERT RETURNING
            # Cluster 2 (CL ANDV)
            {"id": "serotype-andv-uuid"},
            None,
            {"id": "cluster-cl-uuid"},
        ]

        summary = recompute_clusters_for_keys(
            conn,
            [("AR", "ANDV"), ("CL", "ANDV")],
        )

        assert summary == {"upserted": 2}
