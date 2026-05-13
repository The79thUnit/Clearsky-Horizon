-- migration 040 — Annotate the 8 sources disabled in migration 032 with
-- recovery notes, and confirm they remain enabled=FALSE.
--
-- The corresponding celery_app.py beat-schedule entries were COMMENTED OUT
-- in the same commit that adds this migration (previously they were live in
-- the schedule but the DB had enabled=FALSE — beat fired every cycle and
-- logged a 404 to source_quality_log with zero ingestion value).
--
-- Recovery guidance per source:
--   who-euro   : WHO CMS migration removed regional RSS. Re-enable when WHO
--                publishes replacement feed under who.int/europe or euro.who.int.
--   who-searo  : Same cause as who-euro. SEARO content covered by who-don.
--   who-wpro   : Same cause. wpro.who.int has no A record as of 2026-05-13.
--   hpsc       : HPSC Ireland retired RSS. Recoverable via HTMLScraperBase
--                against /news/. Low priority — no endemic hantavirus in IE.
--   phs        : Public Health Scotland retired RSS. UKHSA (enabled) covers UK.
--   japan-niid : NIID retired English RSS ~2025. google-news covers outbreak alerts.
--   china-cdc  : weekly.chinacdc.cn RSS 404; /en/rss 403 (WAF). PubMed has it.
--   argentina-msal: salud/noticias.xml 404. HIGHEST-PRIORITY re-enable target.
--                Recovery path: HTMLScraperBase against BEN bulletin index at
--                argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026.
--                Argentina is the global ANDV heartland. Mitigated by google-news
--                Spanish-language coverage until HTMLScraperBase connector built.

BEGIN;

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): WHO CMS migration decommissioned all '
            'who.int/{region}/rss-feeds/news feeds. Legacy euro.who.int subdomain '
            'points to UAT environment; no A record on wpro.who.int. Coverage '
            'maintained by who-don (A1) + google-news. Re-enable if WHO publishes '
            'replacement regional RSS.',
    updated_at = NOW()
WHERE code IN ('who-euro', 'who-searo', 'who-wpro');

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): HPSC Ireland retired RSS. '
            'Recovery path: HTMLScraperBase against /news/. Low priority — '
            'no endemic hantavirus in Ireland.',
    updated_at = NOW()
WHERE code = 'hpsc';

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): Public Health Scotland retired '
            'RSS (/all-news/rss.xml, /news/rss.xml both 404). UKHSA (enabled, A1) '
            'covers UK signal adequately.',
    updated_at = NOW()
WHERE code = 'phs';

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): NIID retired English RSS ~2025. '
            'Japanese-language path also 404. google-news catches cluster alerts. '
            'Recovery: HTMLScraperBase against NIID English news page.',
    updated_at = NOW()
WHERE code = 'japan-niid';

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): weekly.chinacdc.cn RSS 404; '
            '/en/rss 403 (WAF-blocked from OVH IP). China CDC Weekly articles '
            'covered by pubmed connector (enabled, A1).',
    updated_at = NOW()
WHERE code = 'china-cdc';

UPDATE sources
SET notes = 'DISABLED 2026-05-13 (migration 032): salud/noticias.xml 404. '
            'HIGHEST-PRIORITY re-enable target — Argentina is the global ANDV '
            'heartland. Recovery: HTMLScraperBase against BEN bulletin index at '
            'argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026. '
            'Interim: google-news Spanish-language coverage active.',
    updated_at = NOW()
WHERE code = 'argentina-msal';

COMMIT;
