"""HORIZON SEO package.

Server-rendered SEO surface: sitemap-index + sub-sitemaps, RSS/Atom/JSON-Feed,
and static-flavored HTML pages for crawler-indexable topic clusters
(per-incident, per-serotype, per-country, per-article, glossary, methodology,
sources, FAQ).

These pages exist so search engines see fully-populated HTML on first paint
instead of an empty React-SPA shell — the React app continues to handle the
interactive map and timeline at `/`.

Outbound URLs follow path-based slugs (not hash routes) so PageRank flows
between them. Each page carries its own JSON-LD graph keyed off the shared
Organization/WebSite identities defined in index.html.
"""
