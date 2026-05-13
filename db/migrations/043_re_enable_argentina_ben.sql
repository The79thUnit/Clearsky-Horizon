-- migration 043 — Re-enable argentina-msal with HTMLScraperBase BEN connector.
--
-- BACKGROUND:
--   argentina-msal was disabled 2026-05-13 (migration 032): the RSS feed at
--   salud/noticias.xml returned 404 (feed retired, no announced replacement).
--   Migration 040 added notes marking it the highest-priority re-enable target.
--
-- NEW APPROACH (0.2.0):
--   HTMLScraperBase connector targets the 2026 BEN bulletin index directly:
--     https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026
--   Page confirmed 200 at 40 KB from OVH VPS on 2026-05-13.
--   Parser reads <h4> bulletin headers (e.g. "BEN 807 SE 17 (26 de abril al 2
--   de Mayo 2026)"), collects <li> disease topics per bulletin, and yields one
--   ParsedItem per bulletin whose topic list includes hantavirus-related terms.
--
-- COVERAGE RATIONALE:
--   Argentina is the global ANDV epicentre. Patagonia has documented human
--   person-to-person transmission. The BEN is the Ministerio de Salud's
--   canonical weekly epidemiological bulletin — primary-source, NATO A1.
--
-- BEAT SCHEDULE: uncommented in celery_app.py (minute=44, hourly).
--
-- MAINTENANCE NOTE: LISTING_URL is year-specific (/boletines-2026).
--   Update ArgentinaMSALConnector.LISTING_URL when the calendar year rolls over.

BEGIN;

UPDATE sources
SET enabled = TRUE,
    url     = 'https://www.argentina.gob.ar'
              '/salud/boletin-epidemiologico-nacional/boletines-2026',
    notes   = 'URL updated 2026-05-13 (migration 043): salud/noticias.xml RSS '
              'retired; no RSS replacement. HTMLScraperBase 0.2.0 targets the '
              '2026 BEN bulletin index (confirmed 200, 40 KB). Parses <h4> '
              'bulletin headers + <li> disease topics; one item per hantavirus '
              'bulletin. Update LISTING_URL annually (/boletines-YYYY).',
    updated_at = NOW()
WHERE code = 'argentina-msal';

COMMIT;
