"""Probe the newly-built/fixed connectors after deploy."""

from __future__ import annotations

import json

from .triage_silent_sources import triage_one

CODES = [
    "kraemer-oxford",
    "cdc-hantanet-ref",
    "cnn",
    "kdca",
    "phac",
    "gdelt",
]


def main() -> None:
    for code in CODES:
        print(f"--- {code} ---", flush=True)
        r = triage_one(code)
        print(json.dumps(r, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
