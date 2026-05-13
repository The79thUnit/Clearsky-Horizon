-- migration 032 — Item 4 of the 13 May 2026 audit: 9 dead-URL sources.
--
-- METHODOLOGY: each candidate replacement URL was probed server-side
-- (curl -sIL) before any change was committed here. Probes recorded in
-- the session log on 2026-05-13 09:10-09:20 UTC. No URL is changed in
-- the registry without a verified HTTP 200 + valid Content-Type.
--
-- RESULTS:
--
-- ✓ cidrap-news: REPLACEMENT FOUND.
--     old: https://www.cidrap.umn.edu/news-perspective/feed  → 404
--     new: https://www.cidrap.umn.edu/rss.xml                 → 200
--          application/rss+xml; ~85 KB; fresh items present.
--     Connector PARSER_VERSION bumped to 0.2.0.
--
-- ✗ who-euro / who-searo / who-wpro: NO PUBLIC RSS.
--     WHO restructured its public website in 2024-25 and decommissioned
--     regional-office RSS in favour of unified topic feeds under
--     /news/feed?theme-publication-type=... Probes of every plausible
--     URL on both the new (who.int/europe etc.) and legacy domains
--     (euro.who.int, searo.who.int, wpro.who.int, www2.wpro.who.int)
--     return 404, 503, or connection refused. The legacy domains have
--     either been retired or DNS-blackholed.
--     COVERAGE LOSS: minimal — the unified WHO DON (who-don, already in
--     registry, NATO A1) covers global outbreak news that previously
--     showed in regional feeds; google-news fills the syndication gap.
--
-- ✗ hpsc: HPSC Ireland retired RSS.
--     Probes of /news/RSS/, /RSS/, /news/rss.xml, /news/news.rss,
--     /news/feeds/rss/ all 404. The /news/ page itself returns HTML
--     (20 KB) but it's not parseable as a feed. Re-enabling would
--     require an HTMLScraperBase connector — deferred.
--     COVERAGE LOSS: Ireland has no endemic hantavirus; imported cases
--     are vanishingly rare. Acceptable to defer.
--
-- ✗ phs: Public Health Scotland retired RSS.
--     /all-news/rss.xml and /news/rss.xml both 404. /news/ returns
--     122 KB HTML — recoverable as HTML-scraper, deferred.
--     COVERAGE LOSS: Scotland's PHS news has limited hantavirus signal;
--     UKHSA (already in registry, A1, working) covers UK signal.
--
-- ✗ japan-niid: NIID retired the English RSS.
--     /niid/en/rss/whatsnew-en.xml and /niid/en/whatsnew/whatsnew-rss.xml
--     both 404. The Japanese-language /ja path also 404s. The current
--     NIID English news page exists but only as HTML.
--     COVERAGE LOSS: Japan has imported HFRS cases from pet rats but
--     they're rare; google-news catches the cluster announcements.
--
-- ✗ china-cdc: weekly.chinacdc.cn/rss/Article.htm now 404.
--     /en/rss returns 403 (likely WAF-blocked). China CDC Weekly is
--     also available as a peer-reviewed journal indexed in PubMed
--     (already in registry as `pubmed`, working) — that path picks
--     up the same articles.
--     COVERAGE LOSS: minimal because PubMed has it.
--
-- ✗ argentina-msal: salud/noticias.xml now 404.
--     HOWEVER the canonical bulletin index lives at:
--       https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026
--     Returns HTTP 200 + 40 KB of HTML listing the weekly Boletín
--     Epidemiológico Nacional. RECOVERABLE via a future HTMLScraperBase
--     connector. Disabling for now with a clear note for the next pass.
--     COVERAGE LOSS: high — Argentina is the global ANDV heartland.
--     Mitigated by google-news Spanish-language coverage in the
--     interim. Marked as the highest-value re-enable target.
--
-- All disabled connectors keep their Python source files in place under
-- worker/horizon_worker/connectors/ so that re-enabling later is a
-- single UPDATE in the registry.

BEGIN;

-- 1) cidrap-news URL update (registry mirrors the connector class)
UPDATE sources
SET url = 'https://www.cidrap.umn.edu/rss.xml',
    updated_at = NOW()
WHERE code = 'cidrap-news';

-- 2) Disable the 8 sources with no replacement found.
UPDATE sources
SET enabled = FALSE,
    updated_at = NOW()
WHERE code IN (
    'who-euro',
    'who-searo',
    'who-wpro',
    'hpsc',
    'phs',
    'japan-niid',
    'china-cdc',
    'argentina-msal'
);

COMMIT;
