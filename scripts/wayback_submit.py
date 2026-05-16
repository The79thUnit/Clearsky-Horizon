#!/usr/bin/env python3
"""Submit HORIZON pages to the Internet Archive Wayback Machine.

What this script does
=====================
Hits the Wayback Machine's "Save Page Now" endpoint for each priority URL.
This creates a permanent archival snapshot at web.archive.org with a
publicly resolvable URL like
`https://web.archive.org/web/<timestamp>/https://hantavirus.software/`.

Why this matters for SEO
========================
1. The Internet Archive is one of the most-referenced authority domains on
   the web. Each snapshot creates a public archival URL pointing at the
   live page, which Google treats as an external citation.
2. Wikipedia and academic citations frequently use archive.org links for
   stability — being archived makes us a more attractive citation target.
3. The Wayback Machine itself is crawled by Google and indexed; snapshots
   appear in SERP for some queries.

The Save Page Now API
=====================
Public endpoint: GET https://web.archive.org/save/<URL>
- No authentication required.
- Returns 200/302 on success with a location header to the archived URL.
- Rate-limited; we sleep between submissions.
- Sometimes 429 if hit too fast; the script retries with backoff.

Usage
=====
    python scripts/wayback_submit.py            # priority URLs (~30)
    python scripts/wayback_submit.py --all      # every URL in sitemap (capped)
    python scripts/wayback_submit.py --url <url>  # single URL

Standard library only. Safe to run from cron weekly or after major content
updates.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable

BASE_URL = "https://hantavirus.software"
SAVE_ENDPOINT = "https://web.archive.org/save/"
RATE_DELAY_SECONDS = 8  # Wayback Save Page Now is rate-limited; be polite

# Priority URLs — submitted on every run. Covers every meaningful landing
# page on HORIZON. Adjust as new pages are added.
PRIORITY_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/hantavirus",
    f"{BASE_URL}/hantavirus/2026",
    f"{BASE_URL}/hantavirus/symptoms",
    f"{BASE_URL}/hantavirus/transmission",
    f"{BASE_URL}/hantavirus/prevention",
    f"{BASE_URL}/hantavirus/treatment",
    f"{BASE_URL}/hantavirus/vaccine",
    f"{BASE_URL}/hantavirus/is-it-contagious",
    f"{BASE_URL}/hantavirus/death-rate",
    f"{BASE_URL}/hantavirus/incubation-period",
    f"{BASE_URL}/hantavirus/vs/covid",
    f"{BASE_URL}/hantavirus/vs/flu",
    f"{BASE_URL}/hantavirus/vs/pneumonia",
    f"{BASE_URL}/hantavirus/andes-virus",
    f"{BASE_URL}/hantavirus/sin-nombre-virus",
    f"{BASE_URL}/hantavirus/puumala-virus",
    f"{BASE_URL}/hantavirus/hantaan-virus",
    f"{BASE_URL}/hantavirus/seoul-virus",
    f"{BASE_URL}/outbreaks",
    f"{BASE_URL}/outbreaks/mv-hondius-2026",
    f"{BASE_URL}/countries",
    f"{BASE_URL}/timeline",
    f"{BASE_URL}/chronology",
    f"{BASE_URL}/faq",
    f"{BASE_URL}/data",
    f"{BASE_URL}/sources",
    f"{BASE_URL}/methodology",
    f"{BASE_URL}/glossary",
    f"{BASE_URL}/compare/hantavirus-live-trackers",
]


def _save_url(url: str, max_attempts: int = 3) -> tuple[bool, str]:
    """Submit a URL to Save Page Now. Returns (ok, info)."""
    target = SAVE_ENDPOINT + url
    req = urllib.request.Request(
        target,
        headers={
            "User-Agent": "HORIZON-wayback-submitter/1.0 (https://hantavirus.software)",
            "Accept": "text/html, application/xhtml+xml, */*",
        },
    )
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                final_url = resp.url
                # Look for the archive URL in the Location/final URL or body
                if "web.archive.org/web/" in final_url:
                    return True, f"archived: {final_url}"
                if status in (200, 302):
                    body = resp.read(2048).decode("utf-8", "replace")
                    archived = re.search(r"https?://web\.archive\.org/web/\d+/[^\s\"<]+", body)
                    if archived:
                        return True, f"archived: {archived.group(0)}"
                    return True, f"HTTP {status} (queued)"
                return False, f"HTTP {status}"
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_attempts:
                wait = 15 * attempt
                print(f"  rate-limited (attempt {attempt}), backing off {wait}s ...")
                time.sleep(wait)
                continue
            return False, f"HTTPError {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < max_attempts:
                time.sleep(5 * attempt)
                continue
            return False, f"URLError {e}"
    return False, "max attempts exceeded"


def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    """Pull <loc> entries from a sitemap XML."""
    try:
        with urllib.request.urlopen(sitemap_url, timeout=20) as resp:
            xml = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return []
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def _all_sitemap_urls() -> list[str]:
    """Expand the sitemap index to a flat URL list, capped + deduped."""
    sitemaps = [
        f"{BASE_URL}/sitemap-main.xml",
        f"{BASE_URL}/sitemap-incidents.xml",
        f"{BASE_URL}/sitemap-countries.xml",
        f"{BASE_URL}/sitemap-serotypes.xml",
    ]
    urls: list[str] = []
    for sm in sitemaps:
        urls.extend(_fetch_sitemap_urls(sm))
    seen: set[str] = set()
    ordered: list[str] = []
    for u in urls:
        if u not in seen and u.startswith(BASE_URL):
            seen.add(u)
            ordered.append(u)
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Submit every URL from the sitemaps")
    parser.add_argument("--url", action="append", help="Submit a single URL (repeatable)")
    parser.add_argument("--limit", type=int, default=200, help="Cap total submissions (default 200)")
    parser.add_argument("--delay", type=float, default=RATE_DELAY_SECONDS, help="Seconds between submissions (default 8)")
    args = parser.parse_args()

    if args.url:
        urls = args.url
    elif args.all:
        urls = _all_sitemap_urls()[:args.limit]
        print(f"Discovered {len(urls)} URLs from sitemaps (capped at --limit={args.limit})")
    else:
        urls = PRIORITY_URLS

    print(f"\nSubmitting {len(urls)} URL(s) to Wayback Machine (delay {args.delay}s between)...\n")

    successes = 0
    failures = 0
    for i, url in enumerate(urls, 1):
        ok, msg = _save_url(url)
        prefix = "OK  " if ok else "FAIL"
        print(f"[{i:>3}/{len(urls)}] {prefix} {url}")
        if msg.startswith("archived:"):
            print(f"           {msg}")
        elif not ok:
            print(f"           {msg}")
        if ok:
            successes += 1
        else:
            failures += 1
        if i < len(urls):
            time.sleep(args.delay)

    print(f"\nDone. {successes} succeeded, {failures} failed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
