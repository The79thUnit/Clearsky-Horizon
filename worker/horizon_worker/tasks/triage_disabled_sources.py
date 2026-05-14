"""Triage DISABLED sources that the 14 May audit flagged as gold-tier.

These are sources currently set enabled=false in the DB. Before flipping
them on we run each connector once to confirm:
  - The upstream URL is alive
  - Auth/cookie/anti-bot works
  - The parser still extracts items
  - Items pass the hantavirus keyword filter

Use the same verdict taxonomy as triage_silent_sources.
"""

from __future__ import annotations

import json
import logging

from .triage_silent_sources import triage_one

logger = logging.getLogger(__name__)

DISABLED_SOURCES = [
    # Tier 2 — outbreak intelligence
    "promed-rss",       # ProMED-mail — canonical outbreak intel feed
    # Tier 1 — official authorities (national)
    "japan-niid",
    "china-cdc",
    "chile-deis",
    "nz-moh",
    "phs",              # Public Health Scotland
    "hpsc",             # Ireland Health Protection Surveillance Centre
    "kdca",             # Korea Disease Control Agency
    "thl-finland",      # Finnish THL (highest hantavirus rate in EU)
    "nmh-data",         # New Mexico Department of Health
    # Tier 1 — WHO regional offices
    "who-euro",
    "who-searo",
    "who-emro",
    # Tier 4 — peer-reviewed (high impact)
    "eurosurveillance",
    "mbio",
    "jvi-asm",
    "viruses-mdpi",
    # Other
    "cnn",
]


def main() -> None:
    results = []
    for code in DISABLED_SOURCES:
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
