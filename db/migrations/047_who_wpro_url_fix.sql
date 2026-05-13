-- migration 047 — Fix who-wpro: replace dead regional RSS with global WHO news feed.
--
-- Investigation (2026-05-13):
--   https://www.who.int/westernpacific/rss-feeds/news → HTTP 404
--   WHO retired ALL regional-office RSS feeds on who.int in 2024-2025
--   site restructure. All regional /rss-feeds/news paths return 404:
--     who-wpro:  https://www.who.int/westernpacific/rss-feeds/news  → 404
--     who-euro:  https://www.who.int/europe/rss-feeds/news          → 404 (separate fix)
--     who-searo: https://www.who.int/southeastasia/rss-feeds/news   → 404 (separate fix)
--     who-emro:  https://www.emro.who.int/rss-feeds/whoemro-rss.xml → 302→404 (separate fix)
--   who-afro is unaffected (uses afro.who.int/rss.xml, different domain).
--
-- Replacement:
--   URL:   https://www.who.int/rss-feeds/news-english.xml
--   200 OK, application/rss+xml, 25 items, confirmed 2026-05-13.
--   Global WHO English news — superset of all regional content.
--   Top two items on confirmation date were directly hantavirus-related:
--     "Message by the WHO Director-General to the people of Tenerife
--      regarding the hantavirus response"
--     "WHO's response to hantavirus cases linked to a cruise ship"
--   Source code and DB row retained as 'who-wpro' to preserve history.

BEGIN;

UPDATE sources
SET
    url        = 'https://www.who.int/rss-feeds/news-english.xml',
    name       = 'WHO News RSS (global English feed — via who-wpro)',
    notes      = 'Updated 2026-05-13 (migration 047). Original URL '
                 '(https://www.who.int/westernpacific/rss-feeds/news) '
                 'returned 404 — WHO retired all regional /rss-feeds/news '
                 'paths in 2024-2025. Replaced with global WHO English news '
                 'RSS (rss-feeds/news-english.xml), confirmed 200, 25 items. '
                 'Superset of all regional content; top items on 2026-05-13 '
                 'were WHO DG hantavirus messages re MV Hondius cluster. '
                 'Source code retained as who-wpro for history continuity.',
    updated_at = NOW()
WHERE code = 'who-wpro';

COMMIT;
