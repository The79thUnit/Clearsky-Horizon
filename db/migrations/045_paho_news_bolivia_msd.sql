-- migration 045 — Tier-2 batch 3: PAHO general news RSS + Bolivia MSD RSS.
--
-- PAHO NEWS (paho-news):
--   URL: https://www.paho.org/en/rss.xml
--   Confirmed 200, 8276 bytes, 10 items on 2026-05-13.
--   Third item: "PAHO held Q&A session on hantavirus after outbreak on
--   cruise ship" (MV Hondius). application/rss+xml; charset=utf-8.
--   Complements paho-alerts (A1, hantavirus topic page) by catching
--   cross-disease items that mention hantavirus in the general PAHO news
--   stream before the topic page is updated.
--   NATO B2: PAHO = WHO regional office for the Americas; news RSS is a
--   secondary feed (general news, not primary source outbreak docs).
--   Beat: hourly, minute=25 (5 min after paho-alerts at minute=20).
--
-- BOLIVIA MSD (bolivia-msd):
--   URL: https://www.minsalud.gob.bo/?format=feed&type=rss
--   Confirmed 200 on 2026-05-13. Joomla 3.x RSS 2.0. Spanish-language.
--   Bolivia is endemic for ANDV; primary case geography is Beni and
--   Pando departments (Amazon basin). Bolivia is significantly
--   under-reported in international databases — this feed closes a
--   gap in ANDV-region Latin American coverage alongside argentina-msal
--   and brazil-ms.
--   NATO B2: official Bolivian government source. Reporting quality
--   and cadence are variable.
--   Beat: hourly, minute=46 (in the Latin America block, between
--   argentina-msal at 44 and the disabled chile-deis slot at 49).

BEGIN;

-- PAHO general news RSS
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'paho-news',
    'PAHO News RSS — Pan American Health Organization general news feed',
    'https://www.paho.org/en/rss.xml',
    2,
    'official-authority',
    'B',
    2,
    TRUE,
    'Added 2026-05-13 (migration 045). Complements paho-alerts (A1, hantavirus '
    'topic page). General PAHO news RSS; catches hantavirus items before topic '
    'page updates. Beat: hourly minute=25.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

-- Bolivia Ministerio de Salud y Deportes RSS
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'bolivia-msd',
    'Bolivia MSD — Ministerio de Salud y Deportes RSS (Joomla)',
    'https://www.minsalud.gob.bo/?format=feed&type=rss',
    2,
    'official-authority',
    'B',
    2,
    TRUE,
    'Added 2026-05-13 (migration 045). Bolivia is endemic for ANDV; primary '
    'case geography is Beni and Pando departments. Closes ANDV-region gap '
    'alongside argentina-msal and brazil-ms. Spanish-language Joomla RSS. '
    'Beat: hourly minute=46.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

COMMIT;
