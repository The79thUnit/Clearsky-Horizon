"""HTML shell for server-rendered SEO pages.

Every SEO page goes through `render_page()` which produces a complete,
crawler-friendly HTML document with:

  * Full `<head>` meta-tag suite (title, description, OG, Twitter, Dublin
    Core, citation_, news_keywords, canonical, hreflang).
  * Per-page JSON-LD graph keyed off the shared Organization + WebSite
    nodes (matches the identifiers used in /index.html).
  * Embedded breadcrumb trail (HTML + BreadcrumbList JSON-LD).
  * A visible content body (real prose, real links) so search engines
    index real content rather than an empty SPA shell.
  * A subtle prompt to open the live interactive map at /.

The pages are designed for:
  - Google Search & Google News (NewsArticle / MedicalCondition / FAQPage)
  - Bing Webmaster Tools (full meta suite + IndexNow)
  - DuckDuckGo / Brave / Yandex / Naver (standards-compliant markup)
  - Academic indexers (Dublin Core + citation_ meta)
  - AI search (Perplexity, ChatGPT search, Claude, Gemini Live) — explicit
    in /robots.txt and reinforced here via clean prose answers
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .common import BASE_URL, esc


@dataclass(slots=True)
class Breadcrumb:
    name: str
    url: str  # absolute URL


@dataclass(slots=True)
class PageSpec:
    """Minimal description of an SEO HTML page.

    `jsonld_nodes` is a list of @graph entries to splice in alongside the
    shared Organization, WebSite, and BreadcrumbList nodes. They should
    have @id values to be referenceable across the graph.
    """

    path: str  # leading-slash path, e.g. "/hantavirus/andes-virus"
    title: str  # <title> + og:title
    description: str  # meta description (160 chars target)
    h1: str
    body_html: str  # body content (rendered inside <main>)
    breadcrumbs: list[Breadcrumb] = field(default_factory=list)
    jsonld_nodes: list[dict[str, Any]] = field(default_factory=list)
    keywords: str = ""  # comma-separated
    news_keywords: str = ""  # comma-separated, Google News
    og_type: str = "article"  # "article" | "website"
    og_image: str = f"{BASE_URL}/og-image.png"
    article_published_time: str | None = None  # ISO-8601
    article_modified_time: str | None = None  # ISO-8601
    article_section: str | None = None
    article_authors: list[str] = field(default_factory=lambda: ["79th Unit Limited"])
    robots: str = "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"
    # Locale: "en-GB" (default) or "es-ES". Controls UI strings, hreflang, and og:locale.
    locale: str = "en-GB"
    # Path that hreflang variants should point at (i.e., the path AFTER any
    # locale prefix). If None, derived from `path` by stripping /es prefix.
    hreflang_path: str | None = None


# Shared CSS — kept tiny so the SEO page is fast even on dial-up. Uses
# system fonts and a black-on-cream palette that matches the main app.
_CSS = """
:root{--bg:#f1efe9;--ink:#111114;--muted:#5a5a60;--accent:#c2542a;--rule:#22221e;--card:#fff;--code:#1a1a1d}
*{box-sizing:border-box}
html{font-size:17px;-webkit-text-size-adjust:100%}
body{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55;font-feature-settings:'ss01','cv11'}
header.site{border-bottom:1px solid var(--rule);background:var(--bg);position:sticky;top:0;z-index:10}
header.site .wrap{max-width:1120px;margin:0 auto;padding:14px 22px;display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap}
header.site .brand{font-weight:800;letter-spacing:-0.02em;font-size:18px;text-decoration:none;color:var(--ink)}
header.site .brand b{color:var(--accent)}
header.site nav{display:flex;gap:18px;flex-wrap:wrap;font-size:14.5px}
header.site nav a{color:var(--ink);text-decoration:none;opacity:.78;font-weight:500}
header.site nav a:hover{opacity:1;text-decoration:underline}
main{max-width:1120px;margin:0 auto;padding:32px 22px 56px}
nav.breadcrumb{font-size:13.5px;color:var(--muted);margin-bottom:14px}
nav.breadcrumb a{color:var(--muted);text-decoration:none}
nav.breadcrumb a:hover{color:var(--ink);text-decoration:underline}
nav.breadcrumb span.sep{margin:0 6px}
h1{font-size:clamp(28px,4vw,42px);line-height:1.12;letter-spacing:-0.025em;margin:.3em 0 .35em;font-weight:800}
h2{font-size:clamp(22px,2.4vw,30px);line-height:1.18;letter-spacing:-0.02em;margin:1.6em 0 .35em;font-weight:700;border-top:1px solid var(--rule);padding-top:1em}
h3{font-size:clamp(18px,1.7vw,21px);margin:1.4em 0 .25em;font-weight:700;letter-spacing:-0.012em}
p,ul,ol,blockquote,table{font-size:16.5px;color:#1d1d22}
ul,ol{padding-left:1.5em}
li{margin:.25em 0}
a{color:var(--accent);text-decoration:underline;text-underline-offset:2px;text-decoration-thickness:1.5px}
a:hover{color:var(--ink)}
blockquote{margin:1.2em 0;padding:1em 1.2em;border-left:3px solid var(--accent);background:rgba(194,84,42,.05);font-style:normal;color:#1a1a1f}
.lead{font-size:clamp(18px,1.4vw,21px);color:#26262b;line-height:1.5;max-width:64ch}
.cta{display:inline-block;margin-top:1.2em;padding:.7em 1.2em;background:var(--ink);color:var(--bg);text-decoration:none;border-radius:2px;font-weight:600;font-size:15px}
.cta:hover{background:var(--accent);color:#fff}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:1.5em 0}
.card{background:var(--card);border:1px solid var(--rule);padding:18px 18px 16px;border-radius:3px}
.card h3{margin-top:0}
.card p{margin:.4em 0;font-size:15px;color:#3a3a40}
.card a.more{display:inline-block;margin-top:.5em;font-size:13.5px;font-weight:600}
table.facts{width:100%;border-collapse:collapse;margin:1.2em 0;font-size:15.5px}
table.facts th,table.facts td{text-align:left;padding:.65em .9em;border-top:1px solid var(--rule);vertical-align:top}
table.facts th{font-weight:600;width:30%;color:var(--muted);background:transparent}
.kv{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13.5px;color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:1.3em 0}
.stat{background:#fff;border:1px solid var(--rule);padding:14px 16px;border-radius:3px}
.stat .n{font-size:30px;font-weight:800;letter-spacing:-0.022em;color:var(--ink)}
.stat .l{font-size:11.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:2px}
.tag{display:inline-block;padding:.18em .5em;background:#e8e6df;color:#3a3a40;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;margin-right:.3em;border-radius:2px;font-weight:600}
.tag.alert{background:var(--accent);color:#fff}
footer.site{border-top:1px solid var(--rule);margin-top:48px;background:#ecebe5;color:#3a3a40;font-size:13.5px}
footer.site .wrap{max-width:1120px;margin:0 auto;padding:24px 22px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:18px}
footer.site nav{display:flex;gap:14px;flex-wrap:wrap}
footer.site a{color:#3a3a40;text-decoration:none}
footer.site a:hover{color:var(--ink);text-decoration:underline}
.callout{padding:1em 1.2em;background:#fff;border:1px solid var(--rule);border-left:3px solid var(--ink);margin:1.4em 0;font-size:15.5px}
.muted{color:var(--muted)}
.facts-row{display:flex;flex-wrap:wrap;gap:1em;margin:.5em 0 1em}
.facts-row .fact{background:#fff;border:1px solid var(--rule);padding:.5em .9em;border-radius:2px;font-size:14px}
@media (max-width:600px){header.site nav{display:none}h1{font-size:30px}main{padding:22px 16px 40px}}
"""


_HEADERS_BY_LOCALE = {
    "en-GB": """<header class="site"><div class="wrap">
<a class="brand" href="/" rel="home">HORIZON <b>·</b> Hantavirus Tracker</a>
<nav aria-label="Primary">
<a href="/">Live Map</a>
<a href="/hantavirus">Hantavirus</a>
<a href="/outbreaks">Outbreaks</a>
<a href="/countries">Countries</a>
<a href="/sources">Sources</a>
<a href="/methodology">Methodology</a>
<a href="/glossary">Glossary</a>
<a href="/faq">FAQ</a>
<a href="/es/" rel="alternate" hreflang="es" lang="es">ES</a>
</nav>
</div></header>""",
    "es-ES": """<header class="site"><div class="wrap">
<a class="brand" href="/es/" rel="home">HORIZON <b>·</b> Rastreador de Hantavirus</a>
<nav aria-label="Principal">
<a href="/">Mapa en vivo</a>
<a href="/es/hantavirus">Hantavirus</a>
<a href="/es/brotes">Brotes</a>
<a href="/es/paises">Países</a>
<a href="/es/fuentes">Fuentes</a>
<a href="/es/metodologia">Metodología</a>
<a href="/es/glosario">Glosario</a>
<a href="/es/preguntas-frecuentes">FAQ</a>
<a href="/" rel="alternate" hreflang="en" lang="en">EN</a>
<a href="/pt-br/" rel="alternate" hreflang="pt" lang="pt">PT</a>
</nav>
</div></header>""",
    "pt-BR": """<header class="site"><div class="wrap">
<a class="brand" href="/pt-br/" rel="home">HORIZON <b>·</b> Rastreador de Hantavírus</a>
<nav aria-label="Principal">
<a href="/">Mapa em tempo real</a>
<a href="/pt-br/hantavirus">Hantavírus</a>
<a href="/pt-br/surtos">Surtos</a>
<a href="/pt-br/paises">Países</a>
<a href="/pt-br/perguntas-frequentes">FAQ</a>
<a href="/" rel="alternate" hreflang="en" lang="en">EN</a>
<a href="/es/" rel="alternate" hreflang="es" lang="es">ES</a>
</nav>
</div></header>""",
}


_FOOTERS_BY_LOCALE = {
    "en-GB": """<footer class="site"><div class="wrap">
<div>
HORIZON · operated by <a href="https://79thunit.co.uk" rel="external">79th Unit Limited</a> (UK CRN 17133814).<br>
Open data under <a rel="license noopener" href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Not medical advice.
</div>
<nav aria-label="Footer">
<a href="/about">About</a>
<a href="/contact">Contact</a>
<a href="/editorial-standards">Editorial standards</a>
<a href="/terms-of-service">Terms</a>
<a href="/privacy">Privacy</a>
<a href="/corrections">Corrections</a>
<a href="/sitemap.xml">Sitemap</a>
<a href="/rss.xml">RSS</a>
<a href="/widgets">Widgets</a>
<a href="/api/openapi.json">OpenAPI</a>
</nav>
</div></footer>""",
    "es-ES": """<footer class="site"><div class="wrap">
<div>
HORIZON · operado por <a href="https://79thunit.co.uk" rel="external">79th Unit Limited</a> (Reino Unido, CRN 17133814).<br>
Datos abiertos bajo <a rel="license noopener" href="https://creativecommons.org/licenses/by/4.0/deed.es">CC BY 4.0</a>. Esto no es asesoramiento médico.
</div>
<nav aria-label="Pie">
<a href="/about">Acerca de</a>
<a href="/contact">Contacto</a>
<a href="/terms-of-service">Términos</a>
<a href="/privacy">Privacidad</a>
<a href="/corrections">Correcciones</a>
<a href="/sitemap.xml">Sitemap</a>
<a href="/rss.xml">RSS</a>
<a href="/widgets">Widgets</a>
<a href="/api/openapi.json">OpenAPI</a>
</nav>
</div></footer>""",
    "pt-BR": """<footer class="site"><div class="wrap">
<div>
HORIZON · operado pela <a href="https://79thunit.co.uk" rel="external">79th Unit Limited</a> (Reino Unido, CRN 17133814).<br>
Dados abertos sob <a rel="license noopener" href="https://creativecommons.org/licenses/by/4.0/deed.pt_BR">CC BY 4.0</a>. Isto não é orientação médica.
</div>
<nav aria-label="Rodapé">
<a href="/about">Sobre</a>
<a href="/contact">Contato</a>
<a href="/terms-of-service">Termos</a>
<a href="/privacy">Privacidade</a>
<a href="/corrections">Correções</a>
<a href="/sitemap.xml">Sitemap</a>
<a href="/rss.xml">RSS</a>
<a href="/widgets">Widgets</a>
<a href="/api/openapi.json">OpenAPI</a>
</nav>
</div></footer>""",
}


def _jsonld_graph(spec: PageSpec, mod_time: datetime) -> str:
    canonical = f"{BASE_URL}{spec.path}"
    bc_list = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "name": b.name,
            "item": b.url,
        }
        for i, b in enumerate(spec.breadcrumbs)
    ]
    graph: list[dict[str, Any]] = [
        {
            "@type": ["Organization", "NewsMediaOrganization"],
            "@id": f"{BASE_URL}/#org",
            "name": "79th Unit Limited",
            "url": "https://79thunit.co.uk",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/og-image.png",
                "width": 1200,
                "height": 630,
            },
            "identifier": "17133814",
            "address": {"@type": "PostalAddress", "addressCountry": "GB"},
            "ethicsPolicy": f"{BASE_URL}/editorial-standards",
            "correctionsPolicy": f"{BASE_URL}/corrections",
            "verificationFactCheckingPolicy": f"{BASE_URL}/methodology",
            "knowsAbout": [
                {"@id": f"{BASE_URL}/hantavirus#condition"},
                "Open-source intelligence",
                "Public health surveillance",
                "Outbreak epidemiology",
            ],
            "areaServed": "Worldwide",
            "sameAs": ["https://79thunit.co.uk", "https://hantavirus.software"],
        },
        {
            "@type": "Organization",
            "@id": f"{BASE_URL}/#editorial-team",
            "name": "HORIZON editorial team",
            "url": f"{BASE_URL}/about",
            "parentOrganization": {"@id": f"{BASE_URL}/#org"},
            "memberOf": {"@id": f"{BASE_URL}/#org"},
            "description": (
                "Editorial team operating HORIZON hantavirus surveillance. "
                "OSINT analysts producing audit-grade source qualification "
                "under NATO Admiralty Scale, ICD 206, and Berkeley Protocol."
            ),
        },
        {
            "@type": "WebSite",
            "@id": f"{BASE_URL}/#site",
            "url": f"{BASE_URL}/",
            "name": "HORIZON — Hantavirus Outbreak Surveillance",
            "description": (
                "Live hantavirus outbreak surveillance with audit-grade source "
                "provenance, aggregating WHO, CDC, ECDC, PAHO, ProMED and "
                "peer-reviewed literature."
            ),
            "inLanguage": "en-GB",
            "publisher": {"@id": f"{BASE_URL}/#org"},
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": f"{BASE_URL}/?q={{search_term_string}}",
                },
                "query-input": "required name=search_term_string",
            },
        },
    ]
    if bc_list:
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumbs",
            "itemListElement": bc_list,
        })
    graph.append({
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": spec.title,
        "description": spec.description,
        "isPartOf": {"@id": f"{BASE_URL}/#site"},
        "primaryImageOfPage": spec.og_image,
        "datePublished": spec.article_published_time or "2026-05-13",
        "dateModified": spec.article_modified_time or mod_time.strftime("%Y-%m-%d"),
        "inLanguage": "en-GB",
        "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".lead"]},
        "breadcrumb": {"@id": f"{canonical}#breadcrumbs"} if bc_list else None,
    })
    graph.extend(spec.jsonld_nodes)
    # Drop None values that we may have inserted optimistically
    graph = [_strip_nones(node) for node in graph]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def _strip_nones(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_nones(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_nones(v) for v in obj if v is not None]
    return obj


def _render_breadcrumb_html(crumbs: list[Breadcrumb]) -> str:
    if not crumbs:
        return ""
    parts: list[str] = ['<nav class="breadcrumb" aria-label="Breadcrumb">']
    for i, c in enumerate(crumbs):
        if i:
            parts.append('<span class="sep">›</span>')
        if i == len(crumbs) - 1:
            parts.append(f'<span aria-current="page">{esc(c.name)}</span>')
        else:
            parts.append(f'<a href="{esc(c.url)}">{esc(c.name)}</a>')
    parts.append("</nav>")
    return "".join(parts)


def _hreflang_block(spec: PageSpec) -> str:
    """Emit <link rel="alternate" hreflang="..."> tags for the spec.

    Derives the language-neutral path by stripping any locale prefix from
    `spec.path` (or uses spec.hreflang_path if set).
    """
    base_path = spec.hreflang_path
    if base_path is None:
        for prefix in ("/pt-br", "/es"):
            if spec.path.startswith(prefix):
                base_path = spec.path[len(prefix):] or "/"
                break
        else:
            base_path = spec.path
    if not base_path.startswith("/"):
        base_path = "/" + base_path
    en_url = f"{BASE_URL}{base_path}"
    es_url = f"{BASE_URL}/es{base_path}"
    pt_url = f"{BASE_URL}/pt-br{base_path}"
    return (
        f'<link rel="alternate" hreflang="en-GB" href="{esc(en_url)}" />\n'
        f'<link rel="alternate" hreflang="en" href="{esc(en_url)}" />\n'
        f'<link rel="alternate" hreflang="es-ES" href="{esc(es_url)}" />\n'
        f'<link rel="alternate" hreflang="es-AR" href="{esc(es_url)}" />\n'
        f'<link rel="alternate" hreflang="es-CL" href="{esc(es_url)}" />\n'
        f'<link rel="alternate" hreflang="es-MX" href="{esc(es_url)}" />\n'
        f'<link rel="alternate" hreflang="es" href="{esc(es_url)}" />\n'
        f'<link rel="alternate" hreflang="pt-BR" href="{esc(pt_url)}" />\n'
        f'<link rel="alternate" hreflang="pt-PT" href="{esc(pt_url)}" />\n'
        f'<link rel="alternate" hreflang="pt" href="{esc(pt_url)}" />\n'
        f'<link rel="alternate" hreflang="x-default" href="{esc(en_url)}" />\n'
    )


def render_page(spec: PageSpec) -> str:
    """Render a full HTML5 document for the given page spec."""
    now = datetime.now(timezone.utc)
    mod = spec.article_modified_time or now.strftime("%Y-%m-%d")
    canonical = f"{BASE_URL}{spec.path}"
    jsonld = _jsonld_graph(spec, now)

    lang_attr = spec.locale.split("-")[0]
    if spec.locale.startswith("es"):
        og_locale = "es_ES"
    elif spec.locale.startswith("pt"):
        og_locale = "pt_BR"
    else:
        og_locale = "en_GB"
    header_html = _HEADERS_BY_LOCALE.get(spec.locale, _HEADERS_BY_LOCALE["en-GB"])
    footer_html = _FOOTERS_BY_LOCALE.get(spec.locale, _FOOTERS_BY_LOCALE["en-GB"])
    hreflang = _hreflang_block(spec)

    # Article-specific meta (only emitted for og:type=article)
    article_meta = ""
    if spec.og_type == "article":
        if spec.article_published_time:
            article_meta += f'<meta property="article:published_time" content="{esc(spec.article_published_time)}" />\n'
        if spec.article_modified_time:
            article_meta += f'<meta property="article:modified_time" content="{esc(spec.article_modified_time)}" />\n'
        if spec.article_section:
            article_meta += f'<meta property="article:section" content="{esc(spec.article_section)}" />\n'
        for author in spec.article_authors:
            article_meta += f'<meta property="article:author" content="{esc(author)}" />\n'

    return (
        '<!doctype html>\n'
        f'<html lang="{esc(spec.locale)}">\n'
        '<head>\n'
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />\n'
        '<meta name="theme-color" content="#f1efe9" />\n'
        '<meta name="color-scheme" content="light" />\n'
        f'<title>{esc(spec.title)}</title>\n'
        f'<meta name="description" content="{esc(spec.description)}" />\n'
        f'<meta name="keywords" content="{esc(spec.keywords)}" />\n'
        f'<meta name="news_keywords" content="{esc(spec.news_keywords or spec.keywords)}" />\n'
        '<meta name="author" content="79th Unit Limited" />\n'
        '<meta name="publisher" content="79th Unit Limited" />\n'
        f'<meta name="robots" content="{esc(spec.robots)}" />\n'
        f'<meta name="googlebot" content="{esc(spec.robots)}" />\n'
        '<meta name="referrer" content="strict-origin-when-cross-origin" />\n'
        '<meta name="format-detection" content="telephone=no" />\n'
        f'<link rel="canonical" href="{esc(canonical)}" />\n'
        f'{hreflang}'

        # Dublin Core + citation_ for academic discovery
        f'<meta name="DC.title" content="{esc(spec.title)}" />\n'
        f'<meta name="DC.description" content="{esc(spec.description)}" />\n'
        '<meta name="DC.creator" content="79th Unit Limited" />\n'
        '<meta name="DC.publisher" content="79th Unit Limited" />\n'
        f'<meta name="DC.date" content="{esc(mod)}" />\n'
        '<meta name="DC.type" content="Text" />\n'
        '<meta name="DC.format" content="text/html" />\n'
        f'<meta name="DC.identifier" content="{esc(canonical)}" />\n'
        '<meta name="DC.language" content="en-GB" />\n'
        '<meta name="DC.rights" content="CC BY 4.0" />\n'
        f'<meta name="citation_title" content="{esc(spec.title)}" />\n'
        '<meta name="citation_author" content="79th Unit Limited" />\n'
        f'<meta name="citation_publication_date" content="{esc(mod)}" />\n'
        '<meta name="citation_publisher" content="79th Unit Limited" />\n'
        '<meta name="citation_language" content="en" />\n'

        # IndexNow rotating key (matches /59d765645bcc5c9d796c94bf59063fe5.txt)
        '<meta name="indexnow" content="59d765645bcc5c9d796c94bf59063fe5" />\n'

        # Open Graph
        f'<meta property="og:type" content="{esc(spec.og_type)}" />\n'
        '<meta property="og:site_name" content="HORIZON" />\n'
        f'<meta property="og:title" content="{esc(spec.title)}" />\n'
        f'<meta property="og:description" content="{esc(spec.description)}" />\n'
        f'<meta property="og:url" content="{esc(canonical)}" />\n'
        f'<meta property="og:image" content="{esc(spec.og_image)}" />\n'
        '<meta property="og:image:width" content="1200" />\n'
        '<meta property="og:image:height" content="630" />\n'
        '<meta property="og:image:alt" content="HORIZON live hantavirus outbreak tracker map" />\n'
        f'<meta property="og:locale" content="{esc(og_locale)}" />\n'
        f'<meta property="og:locale:alternate" content="{("es_ES" if og_locale == "en_GB" else "en_GB")}" />\n'
        f'{article_meta}'

        # Twitter
        '<meta name="twitter:card" content="summary_large_image" />\n'
        '<meta name="twitter:site" content="@79thunit" />\n'
        '<meta name="twitter:creator" content="@79thunit" />\n'
        f'<meta name="twitter:title" content="{esc(spec.title)}" />\n'
        f'<meta name="twitter:description" content="{esc(spec.description)}" />\n'
        f'<meta name="twitter:image" content="{esc(spec.og_image)}" />\n'
        '<meta name="twitter:image:alt" content="HORIZON hantavirus outbreak map" />\n'

        # Icons + manifest
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />\n'
        '<link rel="alternate icon" type="image/png" href="/favicon-32.png" />\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />\n'
        '<link rel="manifest" href="/manifest.json" />\n'

        # Feeds (declare so RSS/Atom auto-discovery works for Google + Bing)
        '<link rel="alternate" type="application/rss+xml" title="HORIZON updates (RSS)" href="/rss.xml" />\n'
        '<link rel="alternate" type="application/atom+xml" title="HORIZON updates (Atom)" href="/atom.xml" />\n'
        '<link rel="alternate" type="application/feed+json" title="HORIZON updates (JSON Feed)" href="/feed.json" />\n'

        # Google News / Subscribe with Google (Publisher Center: openaccess).
        # The loader + same-origin init script (no inline JS, CSP-clean).
        '<script async type="application/javascript" '
        'src="https://news.google.com/swg/js/v1/swg-basic.js"></script>\n'
        '<script async type="application/javascript" src="/swg-init.js"></script>\n'

        f'<style>{_CSS}</style>\n'

        f'<script type="application/ld+json">{jsonld}</script>\n'
        '</head>\n'
        f'<body>{header_html}\n'
        '<main>\n'
        f'{_render_breadcrumb_html(spec.breadcrumbs)}\n'
        f'<h1>{esc(spec.h1)}</h1>\n'
        f'{spec.body_html}\n'
        '</main>\n'
        f'{footer_html}\n'
        '</body></html>\n'
    )
