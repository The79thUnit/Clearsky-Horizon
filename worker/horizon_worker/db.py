"""Sync Postgres connection helpers for the worker."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .config import settings

# Type alias for a dict-row Postgres connection. Use everywhere we pass a
# connection around so mypy sees `row["column_name"]` access as valid.
DBConn = psycopg.Connection[dict[str, Any]]


def get_conn() -> DBConn:
    """Open a new sync Postgres connection. Caller manages lifecycle (use `with`)."""
    return psycopg.connect(settings.database_url, row_factory=dict_row)
