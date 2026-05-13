-- migration 033 — Tier-1 audit follow-on: add RIVM source.
--
-- RIVM (Rijksinstituut voor Volksgezondheid en Milieu) is the Dutch
-- national institute for public health and the environment. It's the
-- equivalent of UKHSA, US CDC, German RKI, French Santé publique. For
-- HORIZON it's critical because:
--
--   * MV Hondius is Netherlands-flagged (operator Oceanwide
--     Expeditions, headquartered in Vlissingen). RIVM is the
--     home-country authority — when the ship docks in Rotterdam on
--     17 May 2026, RIVM coordinates the disinfection and quarantine.
--   * The Dutch index couple (70M deceased aboard 2026-04-11; 69F
--     PCR-confirmed deceased in South Africa 2026-04-26) are the
--     laboratory anchors of the entire cluster.
--   * Verified 2026-05-13 09:35 UTC: the RIVM /en/news index already
--     carries direct MV Hondius coverage:
--       /en/news/hantavirus-cruise-ship-passengers-have-arrived-by-plane-start-of-quarantine-period
--       /en/news/update-hantavirus
--
-- RIVM does NOT publish a public RSS feed (probes of /en/rss.xml,
-- /rss.xml, /news/rss, /en/news.xml, /en/feed all return HTTP 404).
-- The /en/news page is server-side-rendered HTML, ~116 KB, ~10
-- <article> blocks per page. Scraped via HTMLScraperBase.
--
-- NATO rating A1: top-tier authoritative national public-health
-- institute (same tier as UKHSA, RKI, CDC HAN, ECDC, WHO DON).

BEGIN;

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'rivm',
    'RIVM — Rijksinstituut voor Volksgezondheid en Milieu (Netherlands)',
    'https://www.rivm.nl/en/news',
    1,
    'official-authority',
    'A',
    1,
    TRUE
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled;

COMMIT;
