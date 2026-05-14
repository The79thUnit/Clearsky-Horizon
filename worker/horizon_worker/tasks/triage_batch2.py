"""Probe round 2: all the connectors fixed/rebuilt today."""

from __future__ import annotations

import json

from .triage_silent_sources import triage_one

CODES = [
    "phac",
    "cnn",
    "phs",
    "hpsc",
    "eurosurveillance",
    "mbio",
    "jvi-asm",
]


def main() -> None:
    for code in CODES:
        print(f"--- {code} ---", flush=True)
        r = triage_one(code)
        print(json.dumps(r, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
