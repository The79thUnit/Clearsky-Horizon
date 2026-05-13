-- migration 041 — Fix two dead feed URLs discovered 2026-05-13.
--
-- PROBES (server-side curl from OVH VPS, 2026-05-13):
--
-- cdc-eid
--   old: https://wwwnc.cdc.gov/eid/rss/current.xml  → 404 (CDC retired ~2025)
--   new: https://wwwnc.cdc.gov/eid/rss/ahead-of-print.xml → 200, 4 KB, fresh EID items
--   note: cdc-eid-ahead already uses upcoming.xml; ahead-of-print overlaps but is the
--         canonical pre-publication feed listed on the CDC EID RSS feeds page.
--         content_topic_hash cross-source dedup links duplicate entries.
--   PARSER_VERSION: 0.1.0 → 0.2.0
--
-- ecdc-cdtr
--   old: https://www.ecdc.europa.eu/en/publications-data/rss.xml → 404
--        (ECDC CMS migration removed generic publications feed)
--   new: https://www.ecdc.europa.eu/en/taxonomy/term/1244/feed → 200, 8 KB
--        ECDC "Scientific and technical publications" taxonomy feed.
--        Contains CDTR week 19 (2-8 May 2026) AND the MV Hondius Rapid
--        Scientific Advice published 2026-05-13.
--   PARSER_VERSION: 0.1.0 → 0.2.0

BEGIN;

UPDATE sources
SET url = 'https://wwwnc.cdc.gov/eid/rss/ahead-of-print.xml',
    notes = 'URL updated 2026-05-13: CDC retired current.xml; ahead-of-print.xml '
            'is the active pre-publication EID feed (confirmed 200).',
    updated_at = NOW()
WHERE code = 'cdc-eid';

UPDATE sources
SET url = 'https://www.ecdc.europa.eu/en/taxonomy/term/1244/feed',
    notes = 'URL updated 2026-05-13: ECDC CMS migration killed publications-data/rss.xml. '
            'Taxonomy/1244 is "Scientific and technical publications" — includes CDTR '
            '(weekly), Rapid Risk Assessments, and outbreak scientific advisories. '
            'Confirmed 200 + contains MV Hondius RSA issued same day.',
    updated_at = NOW()
WHERE code = 'ecdc-cdtr';

COMMIT;
