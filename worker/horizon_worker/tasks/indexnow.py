"""IndexNow auto-submission task.

IndexNow (https://www.indexnow.org) is a standardised crawler-notification
protocol jointly supported by Microsoft Bing, Yandex, Seznam, Naver, Yep,
and DuckDuckGo. A single POST tells every participating engine about new
or updated URLs and they re-crawl within hours rather than days.

Strategy: every 15 minutes, find URLs that became indexable since the
last submission and POST the batch to the IndexNow endpoint. The key
file at /59d765645bcc5c9d796c94bf59063fe5.txt proves we own the host.

We submit:
  * The homepage (always — it's a live feed)
  * /outbreaks/{code} for every incident with new articles in the window
  * /articles/{id} for every newly-ingested case_report
  * /countries/{iso} for any country that gained a new article
  * /news-sitemap.xml so Bing News re-pulls

We DON'T submit the topic-cluster pages (/hantavirus/symptoms etc.) —
those are content pages that change rarely, so let normal crawl handle them.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
import psycopg
from celery import shared_task

from ..celery_app import app  # noqa: F401 — registers task
from ..config import settings

log = logging.getLogger("horizon.indexnow")

# The same rotating key referenced in:
#   web/public/59d765645bcc5c9d796c94bf59063fe5.txt
#   index.html meta name="indexnow"
INDEXNOW_KEY = "59d765645bcc5c9d796c94bf59063fe5"
INDEXNOW_KEY_LOCATION = f"https://hantavirus.software/{INDEXNOW_KEY}.txt"

# IndexNow protocol endpoint. Bing is the canonical one — they propagate
# to all participating engines via the IndexNow federation.
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/IndexNow",       # Generic federation endpoint
    "https://www.bing.com/indexnow",            # Bing direct
    "https://yandex.com/indexnow",              # Yandex direct
]

HOST = "hantavirus.software"
BASE = f"https://{HOST}"

# How far back to look for URLs to submit. 20 min gives 5 min overlap
# vs the 15-min beat interval so we never miss anything if a tick is
# briefly delayed.
LOOKBACK_MINUTES = 20


# How many URLs to send per POST. IndexNow caps at 10,000 per request;
# we cap at 1000 for politeness and to keep the JSON small.
BATCH_SIZE = 1000


def _new_urls(conn: psycopg.Connection, since: datetime) -> list[str]:
    """Compute the list of URLs to submit to IndexNow.

    Always includes the homepage and the news sitemap (so the engines
    re-crawl fresh content). Then per-article + per-incident + per-country
    URLs for anything new since `since`.
    """
    urls: set[str] = {
        f"{BASE}/",
        f"{BASE}/news-sitemap.xml",
        f"{BASE}/sitemap.xml",
        f"{BASE}/rss.xml",
    }
    with conn.cursor() as cur:
        # Recently-ingested articles
        cur.execute(
            """
            SELECT id::text AS id, country_iso2, incident_id::text AS incident_id
            FROM case_reports
            WHERE ingested_at >= %s
            LIMIT %s
            """,
            (since, BATCH_SIZE),
        )
        rows = cur.fetchall()

    countries: set[str] = set()
    incident_ids: set[str] = set()
    for row in rows:
        urls.add(f"{BASE}/articles/{row['id']}")
        if row.get("country_iso2"):
            countries.add(row["country_iso2"].lower())
        if row.get("incident_id"):
            incident_ids.add(row["incident_id"])

    for iso in countries:
        urls.add(f"{BASE}/countries/{iso}")

    if incident_ids:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code FROM incidents WHERE id::text = ANY(%s::text[])",
                (list(incident_ids),),
            )
            for r in cur.fetchall():
                urls.add(f"{BASE}/outbreaks/{r['code']}")

    return sorted(urls)


def _submit_batch(urls: list[str], timeout_s: float = 15.0) -> dict[str, int]:
    """POST the URL list to IndexNow endpoints. Returns per-endpoint status."""
    if not urls:
        return {}
    payload = {
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_LOCATION,
        "urlList": urls,
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "HORIZON-IndexNow/1.0 (+https://hantavirus.software)",
    }
    results: dict[str, int] = {}
    for endpoint in INDEXNOW_ENDPOINTS:
        try:
            resp = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout_s)
            results[endpoint] = resp.status_code
            if resp.status_code >= 400:
                log.warning(
                    "IndexNow %s returned HTTP %d for %d URLs: %s",
                    endpoint, resp.status_code, len(urls), resp.text[:200],
                )
        except httpx.RequestError as exc:
            log.warning("IndexNow %s request failed: %s", endpoint, exc)
            results[endpoint] = -1
    return results


@shared_task(name="horizon_worker.tasks.indexnow.submit_recent")  # type: ignore[misc]
def submit_recent() -> dict:
    """Beat-scheduled every 15 min. Submit recently-changed URLs to IndexNow."""
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK_MINUTES)
    with psycopg.connect(
        settings.database_url, row_factory=psycopg.rows.dict_row
    ) as conn:
        urls = _new_urls(conn, since)

    if not urls:
        log.info("IndexNow: no URLs to submit")
        return {"submitted": 0, "results": {}}

    results = _submit_batch(urls)
    log.info(
        "IndexNow: submitted %d URLs -> %s",
        len(urls),
        ", ".join(f"{k.split('/')[2]}={v}" for k, v in results.items()),
    )
    return {"submitted": len(urls), "results": results, "urls_sample": urls[:5]}
