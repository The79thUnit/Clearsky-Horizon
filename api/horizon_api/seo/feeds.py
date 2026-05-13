"""RSS 2.0, Atom 1.0, and JSON Feed 1.1 builders.

Three feed formats covers every conceivable subscriber:
  * RSS 2.0  — universal compatibility (Feedly, Inoreader, Old Reader,
               Google Currents legacy, all RSS apps).
  * Atom 1.0 — strict XML schema, preferred by some news aggregators.
  * JSON Feed 1.1 — modern feed format (https://jsonfeed.org).

All three are linked from the SEO HTML <head> via <link rel="alternate">
so feed-readers and Google News auto-discover them.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from xml.sax.saxutils import escape as xescape

from .common import BASE_URL, iso_dt, rfc2822


def render_rss(events: list[dict[str, Any]], now: datetime) -> str:
    """RSS 2.0 — events are dicts with id, title, summary, url, occurred_at,
    country_iso2, serotype_code, source_code.
    """
    items_xml: list[str] = []
    for ev in events:
        ts: datetime = ev.get("occurred_at") or now
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        link = f"{BASE_URL}/articles/{ev['id']}"
        category_parts: list[str] = ["hantavirus"]
        if ev.get("serotype_code"):
            category_parts.append(ev["serotype_code"])
        if ev.get("country_iso2"):
            category_parts.append(ev["country_iso2"])
        categories = "".join(
            f'      <category>{xescape(c)}</category>\n' for c in category_parts
        )
        items_xml.append(
            '    <item>\n'
            f'      <title>{xescape(str(ev["title"]))}</title>\n'
            f'      <link>{xescape(link)}</link>\n'
            f'      <guid isPermaLink="true">{xescape(link)}</guid>\n'
            f'      <pubDate>{rfc2822(ts) if isinstance(ts, datetime) else ts}</pubDate>\n'
            f'      <description><![CDATA[{ev.get("summary") or ev["title"]}]]></description>\n'
            f'{categories}'
            f'      <source url="{xescape(ev.get("source_url") or link)}">'
            f'{xescape(ev.get("source_code") or "horizon")}</source>\n'
            '    </item>\n'
        )
    items_block = "".join(items_xml)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '  <channel>\n'
        '    <title>HORIZON — Live Hantavirus Outbreak Tracker</title>\n'
        f'    <link>{BASE_URL}/</link>\n'
        f'    <atom:link href="{BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />\n'
        # WebSub hub declaration — pubsubhubbub-aware clients receive push notifications
        f'    <atom:link rel="hub" href="https://pubsubhubbub.appspot.com/" />\n'
        '    <description>Live hantavirus outbreak surveillance with audit-grade source provenance — WHO, CDC, ECDC, PAHO, ProMED, and peer-reviewed literature.</description>\n'
        '    <language>en-GB</language>\n'
        '    <copyright>CC BY 4.0 — 79th Unit Limited</copyright>\n'
        '    <managingEditor>security@79thunit.co.uk (79th Unit Limited)</managingEditor>\n'
        '    <generator>HORIZON</generator>\n'
        '    <ttl>15</ttl>\n'
        f'    <lastBuildDate>{rfc2822(now)}</lastBuildDate>\n'
        f'    <image>\n'
        f'      <url>{BASE_URL}/og-image.png</url>\n'
        '      <title>HORIZON</title>\n'
        f'      <link>{BASE_URL}/</link>\n'
        '      <width>1200</width>\n'
        '      <height>630</height>\n'
        '    </image>\n'
        f'{items_block}'
        '  </channel>\n'
        '</rss>\n'
    )


def render_atom(events: list[dict[str, Any]], now: datetime) -> str:
    entries: list[str] = []
    for ev in events:
        ts: datetime = ev.get("occurred_at") or now
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        link = f"{BASE_URL}/articles/{ev['id']}"
        entries.append(
            '  <entry>\n'
            f'    <title>{xescape(str(ev["title"]))}</title>\n'
            f'    <id>{xescape(link)}</id>\n'
            f'    <link rel="alternate" type="text/html" href="{xescape(link)}" />\n'
            f'    <published>{iso_dt(ts) if isinstance(ts, datetime) else ts}</published>\n'
            f'    <updated>{iso_dt(ts) if isinstance(ts, datetime) else ts}</updated>\n'
            f'    <summary type="html">{xescape(ev.get("summary") or ev["title"])}</summary>\n'
            '    <author><name>79th Unit Limited</name></author>\n'
            '  </entry>\n'
        )
    entries_block = "".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        '  <title>HORIZON — Live Hantavirus Outbreak Tracker</title>\n'
        f'  <link rel="self" type="application/atom+xml" href="{BASE_URL}/atom.xml" />\n'
        f'  <link rel="alternate" type="text/html" href="{BASE_URL}/" />\n'
        '  <link rel="hub" href="https://pubsubhubbub.appspot.com/" />\n'
        f'  <id>{BASE_URL}/atom.xml</id>\n'
        f'  <updated>{iso_dt(now)}</updated>\n'
        '  <author><name>79th Unit Limited</name></author>\n'
        '  <rights>CC BY 4.0</rights>\n'
        '  <generator uri="https://hantavirus.software/">HORIZON</generator>\n'
        '  <subtitle>Live hantavirus outbreak surveillance with audit-grade source provenance.</subtitle>\n'
        f'  <icon>{BASE_URL}/favicon-192.png</icon>\n'
        f'  <logo>{BASE_URL}/og-image.png</logo>\n'
        f'{entries_block}'
        '</feed>\n'
    )


def render_json_feed(events: list[dict[str, Any]], now: datetime) -> str:
    items: list[dict[str, Any]] = []
    for ev in events:
        ts: datetime = ev.get("occurred_at") or now
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        link = f"{BASE_URL}/articles/{ev['id']}"
        item = {
            "id": link,
            "url": link,
            "title": ev["title"],
            "content_text": ev.get("summary") or ev["title"],
            "date_published": iso_dt(ts) if isinstance(ts, datetime) else str(ts),
            "tags": list(filter(None, [
                "hantavirus",
                ev.get("serotype_code"),
                ev.get("country_iso2"),
                ev.get("source_code"),
            ])),
            "external_url": ev.get("source_url"),
        }
        items.append(item)
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "HORIZON — Live Hantavirus Outbreak Tracker",
        "home_page_url": f"{BASE_URL}/",
        "feed_url": f"{BASE_URL}/feed.json",
        "description": "Live hantavirus outbreak surveillance with audit-grade source provenance.",
        "user_comment": "Open data under CC BY 4.0. Operated by 79th Unit Limited (UK CRN 17133814).",
        "icon": f"{BASE_URL}/og-image.png",
        "favicon": f"{BASE_URL}/favicon-192.png",
        "language": "en-GB",
        "authors": [
            {"name": "79th Unit Limited", "url": "https://79thunit.co.uk"}
        ],
        "items": items,
    }
    return json.dumps(feed, ensure_ascii=False, indent=2)
