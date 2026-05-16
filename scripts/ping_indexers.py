#!/usr/bin/env python3
"""Ping search-engine indexers for fresh content.

What this script does
=====================
1. **IndexNow** — submits an explicit URL list to api.indexnow.org. This
   federates to Bing, Yandex, Naver, and Seznam in one POST. Modern, fast
   (typically indexed within hours).
2. **Google sitemap ping** — fires the legacy `google.com/ping?sitemap=`
   endpoint. Officially deprecated since June 2023, but Google's crawler
   still respects it as a hint. Costs nothing to try.

Usage
=====
    python scripts/ping_indexers.py               # pings the homepage + key SEO pages
    python scripts/ping_indexers.py --all         # pings every URL from sitemap-main.xml
    python scripts/ping_indexers.py --url <url>   # pings a single URL

Requires only the standard library. Safe to run from cron.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable

HOST = "hantavirus.software"
BASE_URL = f"https://{HOST}"
INDEXNOW_KEY = "59d765645bcc5c9d796c94bf59063fe5"
INDEXNOW_KEY_LOCATION = f"{BASE_URL}/indexnow-keyfile"

# Curated high-priority URLs. Submit these on every run regardless of mode.
KEY_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/hantavirus",
    f"{BASE_URL}/hantavirus/2026",
    f"{BASE_URL}/hantavirus/andes-virus",
    f"{BASE_URL}/hantavirus/symptoms",
    f"{BASE_URL}/hantavirus/transmission",
    f"{BASE_URL}/hantavirus/prevention",
    f"{BASE_URL}/hantavirus/treatment",
    f"{BASE_URL}/outbreaks",
    f"{BASE_URL}/outbreaks/mv-hondius-2026",
    f"{BASE_URL}/countries",
    f"{BASE_URL}/timeline",
    f"{BASE_URL}/chronology",
    f"{BASE_URL}/faq",
    f"{BASE_URL}/data",
    f"{BASE_URL}/methodology",
]

# Sitemap URLs to ping at Google (covers everything reachable from the index).
SITEMAPS = [
    f"{BASE_URL}/sitemap.xml",
    f"{BASE_URL}/sitemap-main.xml",
    f"{BASE_URL}/sitemap-incidents.xml",
    f"{BASE_URL}/sitemap-countries.xml",
    f"{BASE_URL}/sitemap-serotypes.xml",
    f"{BASE_URL}/sitemap-articles.xml",
    f"{BASE_URL}/news-sitemap.xml",
]


def _ping_google_sitemap(sitemap_url: str) -> tuple[bool, str]:
    """Deprecated but still-honoured Google sitemap ping."""
    target = (
        "https://www.google.com/ping?sitemap="
        + urllib.parse.quote(sitemap_url, safe="")
    )
    try:
        with urllib.request.urlopen(target, timeout=20) as resp:
            return resp.status == 200, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTPError {e.code}"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, f"URLError {e}"


def _submit_indexnow(urls: list[str]) -> tuple[bool, str]:
    """POST a URL list to the IndexNow federation.

    The api.indexnow.org endpoint forwards to Bing, Yandex, Naver, Seznam.
    A 200 or 202 response means accepted; the actual crawl happens
    asynchronously over the following hours.
    """
    if not urls:
        return False, "no URLs to submit"

    payload = {
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_LOCATION,
        "urlList": urls,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Host": "api.indexnow.org",
            "User-Agent": "HORIZON-indexer-ping/1.0 (https://hantavirus.software)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 202), f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTPError {e.code}: {e.read()[:200].decode('utf-8', 'replace')}"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, f"URLError {e}"


def _fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    """Parse <loc> entries from a sitemap XML. Best-effort, no external deps."""
    import re

    try:
        with urllib.request.urlopen(sitemap_url, timeout=20) as resp:
            xml = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return []
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def _expand_all_urls() -> list[str]:
    """Pull every URL listed in the main sitemap. Cap at IndexNow's 10k limit."""
    urls: list[str] = []
    for sm in SITEMAPS:
        urls.extend(_fetch_sitemap_urls(sm))
    # Dedup while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered[:10000]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Submit every URL from sitemap")
    parser.add_argument("--url", action="append", help="Submit a single URL (repeatable)")
    parser.add_argument("--skip-google", action="store_true", help="Skip Google sitemap ping")
    parser.add_argument("--skip-indexnow", action="store_true", help="Skip IndexNow submission")
    args = parser.parse_args()

    if args.url:
        urls = args.url
    elif args.all:
        urls = _expand_all_urls()
        print(f"Discovered {len(urls)} URLs from sitemaps")
    else:
        urls = KEY_URLS

    rc = 0

    if not args.skip_indexnow:
        print(f"\nIndexNow: submitting {len(urls)} URL(s) to api.indexnow.org ...")
        ok, msg = _submit_indexnow(urls)
        print(f"  {'OK' if ok else 'FAIL'}: {msg}")
        if not ok:
            rc = 1

    if not args.skip_google:
        print("\nGoogle: pinging sitemap URLs (deprecated but still respected) ...")
        for sm in SITEMAPS:
            ok, msg = _ping_google_sitemap(sm)
            print(f"  {'OK' if ok else '??'}: {sm}  ({msg})")
            # Google ping deprecation means errors here are not fatal.

    print(
        "\nDone. For Google Search Console URL Inspection (the modern path "
        "to request indexing), see docs/seo-checklist.md."
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
