"""Triage silent-zero connectors.

Some sources are enabled in the DB but have never produced a record. This
diagnostic runs each named connector synchronously and reports what it actually
sees from the upstream (items_seen, http_status, latency, error). Distinguishes:

    - Network/DNS errors        (likely external)
    - HTTP 4xx/5xx              (upstream blocked us or service down)
    - 200 but items_seen == 0   (selector/parser drift — feed schema changed)
    - 200 + items_seen > 0
      but items_ingested == 0   (every item is being filtered, e.g. by topic
                                 filter or external_id collision)

Run from the worker container:
    docker compose -f docker-compose.prod.yml exec worker \\
        python -m horizon_worker.tasks.triage_silent_sources
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import traceback
from typing import Any

from ..config import settings
from ..tasks.ingest import CONNECTORS

logger = logging.getLogger(__name__)

# Sources that the 14 May audit found enabled-but-empty.
SILENT_SOURCES = [
    "phac",
    "brazil-ms",
    "rki",
    "cdc-han",
    "australia-health",
    "ecdc-updates",
    "norway-fhi",
    "who-afro",
    "sweden-fhm",
    "ecdc-risk",
    "cdc-hantanet-ref",
    "kraemer-oxford",
    "cidrap-news",
    "healthmap",
    "outbreak-news-today",
    "mercopress",
    "gdelt",
    "cdc-eid",
    "cdc-eid-ahead",
    "lancet-id",
    "plos-pathogens",
    "europe-pmc",
    "elife",
    "biorxiv",
    "medrxiv",
]


def triage_one(code: str) -> dict[str, Any]:
    cls = CONNECTORS.get(code)
    if cls is None:
        return {"code": code, "verdict": "MISSING_FROM_CONNECTOR_REGISTRY"}

    started = time.monotonic()
    try:
        connector = cls(user_agent=settings.user_agent)
        result = asyncio.run(connector.run())
        elapsed_ms = int((time.monotonic() - started) * 1000)
    except Exception as exc:  # noqa: BLE001  diagnostic only
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "code": code,
            "verdict": "EXCEPTION",
            "elapsed_ms": elapsed_ms,
            "exception_type": type(exc).__name__,
            "exception_msg": str(exc)[:300],
            "traceback_tail": traceback.format_exc().splitlines()[-5:],
        }

    # Categorise the FetchResult
    if result.http_status is None:
        verdict = "NO_HTTP_RESPONSE"
    elif result.http_status >= 500:
        verdict = "UPSTREAM_5XX"
    elif result.http_status >= 400:
        verdict = "UPSTREAM_4XX"
    elif result.items_seen == 0:
        verdict = "EMPTY_FEED_OR_PARSER_DRIFT"
    elif result.items_seen > 0 and result.items_filtered == result.items_seen:
        verdict = "ALL_FILTERED_BY_KEYWORD"
    else:
        verdict = "OK"

    return {
        "code": code,
        "verdict": verdict,
        "http_status": result.http_status,
        "items_seen": result.items_seen,
        "items_filtered": result.items_filtered,
        "latency_ms": result.latency_ms,
        "elapsed_ms": elapsed_ms,
        "parser_version": result.parser_version,
        "error": (result.error[:200] if result.error else None),
        "sample_title": (result.items[0].title[:120] if result.items else None),
    }


def main() -> None:
    results: list[dict[str, Any]] = []
    for code in SILENT_SOURCES:
        print(f"--- {code} ---", flush=True)
        r = triage_one(code)
        results.append(r)
        print(json.dumps(r, indent=2, default=str), flush=True)

    by_verdict: dict[str, list[str]] = {}
    for r in results:
        by_verdict.setdefault(r["verdict"], []).append(r["code"])

    print("\n=== SUMMARY ===")
    for v, codes in sorted(by_verdict.items(), key=lambda kv: -len(kv[1])):
        print(f"  {v:30s} {len(codes):>2d}  {' '.join(codes)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    main()
