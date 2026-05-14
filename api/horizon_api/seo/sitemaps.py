"""Sitemap XML builders — sitemap-index plus per-type sub-sitemaps.

Two layers of indirection:

  /sitemap.xml              → <sitemapindex> pointing at sub-sitemaps
  /sitemap-main.xml         → static topic clusters (homepage, hubs, glossary)
  /sitemap-serotypes.xml    → one URL per orthohantavirus serotype
  /sitemap-countries.xml    → one URL per country with at least one case
  /sitemap-incidents.xml    → one URL per active or monitoring incident
  /sitemap-articles.xml     → one URL per ingested case_report (capped at 50k)
  /news-sitemap.xml         → Google News format, articles from last 48h

Why split: Google enforces 50k URLs per sitemap file, and the news sitemap
has a different schema (`<news:news>` blocks per URL) that mustn't be mixed
with the regular sitemap entries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape as xescape

from .common import BASE_URL, COUNTRY_NAMES, SEROTYPES, iso_dt


_HEAD_INDEX = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
)
_TAIL_INDEX = '</sitemapindex>\n'

_HEAD_URLSET = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    '        xmlns:xhtml="http://www.w3.org/1999/xhtml"\n'
    '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
)
_TAIL_URLSET = '</urlset>\n'

_HEAD_NEWS_URLSET = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"\n'
    '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
)


def render_sitemap_index(now: datetime) -> str:
    """Top-level sitemap index pointing to sub-sitemaps."""
    lm = iso_dt(now)
    sub = [
        ("sitemap-main.xml", lm),
        ("sitemap-serotypes.xml", lm),
        ("sitemap-countries.xml", lm),
        ("sitemap-incidents.xml", lm),
        ("sitemap-articles.xml", lm),
        ("news-sitemap.xml", lm),
    ]
    parts = [_HEAD_INDEX]
    for path, mod in sub:
        parts.append(
            f'  <sitemap>\n'
            f'    <loc>{BASE_URL}/{path}</loc>\n'
            f'    <lastmod>{mod}</lastmod>\n'
            f'  </sitemap>\n'
        )
    parts.append(_TAIL_INDEX)
    return "".join(parts)


def _url_entry(
    loc: str,
    lastmod: str | None = None,
    changefreq: str | None = None,
    priority: float | None = None,
    hreflang: bool = True,
    image_loc: str | None = None,
    image_title: str | None = None,
) -> str:
    parts = [f'  <url>\n    <loc>{xescape(loc)}</loc>\n']
    if lastmod:
        parts.append(f'    <lastmod>{lastmod}</lastmod>\n')
    if changefreq:
        parts.append(f'    <changefreq>{changefreq}</changefreq>\n')
    if priority is not None:
        parts.append(f'    <priority>{priority:.1f}</priority>\n')
    if hreflang:
        parts.append(
            f'    <xhtml:link rel="alternate" hreflang="en-GB" href="{xescape(loc)}" />\n'
            f'    <xhtml:link rel="alternate" hreflang="en" href="{xescape(loc)}" />\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{xescape(loc)}" />\n'
        )
    if image_loc:
        parts.append(
            f'    <image:image>\n'
            f'      <image:loc>{xescape(image_loc)}</image:loc>\n'
        )
        if image_title:
            parts.append(f'      <image:title>{xescape(image_title)}</image:title>\n')
        parts.append('    </image:image>\n')
    parts.append('  </url>\n')
    return "".join(parts)


def render_main_sitemap(now: datetime) -> str:
    """Static topic-cluster URLs."""
    lm = iso_dt(now)
    static_urls: list[tuple[str, str, float]] = [
        ("/", "hourly", 1.0),
        ("/hantavirus", "weekly", 0.95),
        ("/hantavirus/symptoms", "weekly", 0.85),
        ("/hantavirus/transmission", "weekly", 0.85),
        ("/hantavirus/prevention", "weekly", 0.85),
        ("/hantavirus/treatment", "weekly", 0.85),
        ("/hantavirus/2026", "daily", 0.95),
        ("/outbreaks", "hourly", 0.95),
        ("/countries", "daily", 0.9),
        ("/articles", "hourly", 0.85),
        ("/chronology", "hourly", 0.85),
        ("/compare", "weekly", 0.75),
        ("/compare/andes-vs-sin-nombre", "monthly", 0.7),
        ("/compare/hantavirus-vs-influenza", "monthly", 0.7),
        ("/compare/hantavirus-vs-covid", "monthly", 0.7),
        ("/compare/hps-vs-hfrs", "monthly", 0.7),
        ("/compare/hantavirus-live-trackers", "monthly", 0.8),
        ("/timeline", "daily", 0.85),
        ("/data", "daily", 0.8),
        ("/sources", "daily", 0.75),
        ("/methodology", "monthly", 0.7),
        ("/glossary", "weekly", 0.7),
        ("/faq", "weekly", 0.7),
        ("/widgets", "monthly", 0.6),
        ("/about", "monthly", 0.6),
        ("/contact", "monthly", 0.55),
        ("/editorial-standards", "monthly", 0.55),
        ("/corrections", "weekly", 0.55),
        ("/terms-of-service", "yearly", 0.4),
        ("/privacy", "yearly", 0.4),
        # Spanish surface
        ("/es/", "hourly", 0.95),
        ("/es/hantavirus", "weekly", 0.85),
        ("/es/hantavirus/sintomas", "weekly", 0.8),
        ("/es/hantavirus/transmision", "weekly", 0.8),
        ("/es/hantavirus/prevencion", "weekly", 0.8),
        ("/es/hantavirus/tratamiento", "weekly", 0.8),
        ("/es/hantavirus/virus-de-los-andes", "weekly", 0.8),
        ("/es/hantavirus/sin-nombre", "weekly", 0.75),
        ("/es/hantavirus/puumala", "weekly", 0.75),
        ("/es/hantavirus/hantaan", "weekly", 0.75),
        ("/es/hantavirus/seoul", "weekly", 0.75),
        ("/es/hantavirus/dobrava-belgrado", "weekly", 0.75),
        ("/es/preguntas-frecuentes", "weekly", 0.7),
        ("/es/brotes/mv-hondius-2026", "hourly", 0.9),
        # Portuguese (pt-BR) surface — Brazil has endemic hantavirus
        # (Juquitiba, Araraquara) and the highest search volume for
        # "hantavirose" in Latin America.
        ("/pt-br", "hourly", 0.95),
        ("/pt-br/hantavirus", "weekly", 0.85),
        ("/pt-br/hantavirus/sintomas", "weekly", 0.8),
        ("/pt-br/hantavirus/transmissao", "weekly", 0.8),
        ("/pt-br/hantavirus/prevencao", "weekly", 0.8),
        ("/pt-br/hantavirus/andv", "weekly", 0.8),
        ("/pt-br/hantavirus/snv", "weekly", 0.75),
        ("/pt-br/hantavirus/puuv", "weekly", 0.75),
        ("/pt-br/perguntas-frequentes", "weekly", 0.7),
        ("/pt-br/surtos/mv-hondius-2026", "hourly", 0.9),
        # English MV Hondius outbreak detail page (high-traffic event)
        ("/outbreaks/mv-hondius-2026", "hourly", 0.9),
    ]
    parts = [_HEAD_URLSET]
    for path, freq, pri in static_urls:
        parts.append(
            _url_entry(
                f"{BASE_URL}{path}",
                lastmod=lm,
                changefreq=freq,
                priority=pri,
                image_loc=f"{BASE_URL}/og-image.png",
                image_title="HORIZON Hantavirus Outbreak Tracker",
            )
        )
    parts.append(_TAIL_URLSET)
    return "".join(parts)


def render_serotypes_sitemap(now: datetime) -> str:
    lm = iso_dt(now)
    parts = [_HEAD_URLSET]
    for s in SEROTYPES:
        parts.append(
            _url_entry(
                f"{BASE_URL}/hantavirus/{s['slug']}",
                lastmod=lm,
                changefreq="weekly",
                priority=0.8,
                image_loc=f"{BASE_URL}/og-image.png",
                image_title=s["name"],
            )
        )
    parts.append(_TAIL_URLSET)
    return "".join(parts)


def render_countries_sitemap(country_isos: list[str], now: datetime) -> str:
    lm = iso_dt(now)
    parts = [_HEAD_URLSET]
    for iso in country_isos:
        parts.append(
            _url_entry(
                f"{BASE_URL}/countries/{iso.lower()}",
                lastmod=lm,
                changefreq="daily",
                priority=0.65,
            )
        )
    parts.append(_TAIL_URLSET)
    return "".join(parts)


def render_incidents_sitemap(incidents: list[dict], now: datetime) -> str:
    """Sub-sitemap for one URL per incident.

    Each `incidents` row must have keys: `code` (str), `lastmod` (datetime).
    """
    parts = [_HEAD_URLSET]
    for inc in incidents:
        lm = iso_dt(inc.get("lastmod") or now)
        parts.append(
            _url_entry(
                f"{BASE_URL}/outbreaks/{inc['code']}",
                lastmod=lm,
                changefreq="hourly",
                priority=0.95,
                image_loc=f"{BASE_URL}/og-image.png",
                image_title=inc.get("name", inc["code"]),
            )
        )
    parts.append(_TAIL_URLSET)
    return "".join(parts)


def render_articles_sitemap(articles: list[dict], now: datetime) -> str:
    """Sub-sitemap for case_report URLs.

    Each `articles` row must have keys: `id`, `lastmod` (datetime), `title`.
    """
    parts = [_HEAD_URLSET]
    for a in articles:
        lm = iso_dt(a.get("lastmod") or now)
        parts.append(
            _url_entry(
                f"{BASE_URL}/articles/{a['id']}",
                lastmod=lm,
                changefreq="weekly",
                priority=0.55,
            )
        )
    parts.append(_TAIL_URLSET)
    return "".join(parts)


def render_news_sitemap(articles: list[dict], now: datetime) -> str:
    """Google News sitemap — articles from last 48h only.

    Each `articles` row must have keys: `id`, `title`, `published`
    (datetime), `keywords` (str).
    """
    parts = [_HEAD_NEWS_URLSET]
    cutoff = now - timedelta(hours=48)
    for a in articles:
        pub: datetime = a["published"]
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        if pub < cutoff:
            continue
        loc = f"{BASE_URL}/articles/{a['id']}"
        parts.append(
            '  <url>\n'
            f'    <loc>{xescape(loc)}</loc>\n'
            f'    <news:news>\n'
            f'      <news:publication>\n'
            f'        <news:name>HORIZON Hantavirus Surveillance</news:name>\n'
            f'        <news:language>en</news:language>\n'
            f'      </news:publication>\n'
            f'      <news:publication_date>{iso_dt(pub)}</news:publication_date>\n'
            f'      <news:title>{xescape(a["title"][:140])}</news:title>\n'
            f'      <news:keywords>{xescape(a.get("keywords", ""))}</news:keywords>\n'
            f'    </news:news>\n'
            '  </url>\n'
        )
    parts.append('</urlset>\n')
    return "".join(parts)
