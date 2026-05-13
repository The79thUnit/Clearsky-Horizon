-- migration 048 — Tier-2 batch 4: Venezuela MPPS + Peru MINSA LatAm expansion.
--
-- VENEZUELA MPPS (venezuela-mpps):
--   URL: https://mpps.gob.ve/feed/
--   Confirmed 200, application/rss+xml; charset=UTF-8, 10 items on 2026-05-13.
--   WordPress RSS 2.0. Spanish-language. ANDV-endemic country (Orinoco basin,
--   Mérida, Barinas, Trujillo states). Significantly under-reported in
--   international databases. Closes a major LatAm ANDV gap.
--   NATO B2: official Venezuelan government source. Variable cadence.
--   Beat: hourly, minute=48 (LatAm block, between bolivia-msd=46 and
--   disabled chile-deis=49).
--
-- PERU MINSA (peru-minsa):
--   URL: https://www.gob.pe/institucion/minsa/noticias.json
--   Confirmed 200, application/json, 9 items on 2026-05-13.
--   JSON API on gob.pe government portal. Date field is Spanish long-form
--   ("17 de marzo de 2026"). ANDV-endemic (Amazonas, Loreto, Ucayali
--   departments). minsa.gob.pe returns 403; gob.pe is the accessible path.
--   NATO B2: official Peruvian government source.
--   Beat: hourly, minute=52 (LatAm block, after brazil-ms=54 offset by 2).
--
-- Ecuador MSP (salud.gob.ec): SKIPPED — entire domain is offline/unreachable
--   across all URL variants as of 2026-05-13 probe. No accessible path.
--   Re-assess in a future audit.

BEGIN;

-- Venezuela Ministerio del Poder Popular para la Salud (WordPress RSS)
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'venezuela-mpps',
    'Venezuela MPPS — Ministerio del Poder Popular para la Salud RSS (WordPress)',
    'https://mpps.gob.ve/feed/',
    2,
    'official-authority',
    'B',
    2,
    TRUE,
    'Added 2026-05-13 (migration 048). Venezuela is ANDV-endemic (Orinoco '
    'basin, Mérida, Barinas, Trujillo). WordPress RSS, 10 items on add date. '
    'Significantly under-reported in international databases. Closes ANDV-region '
    'gap alongside argentina-msal, brazil-ms, bolivia-msd. Spanish-language. '
    'Beat: hourly minute=48.'
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

-- Peru Ministerio de Salud (MINSA) gob.pe JSON API
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'peru-minsa',
    'Peru MINSA — Ministerio de Salud JSON API (gob.pe)',
    'https://www.gob.pe/institucion/minsa/noticias.json',
    2,
    'official-authority',
    'B',
    2,
    TRUE,
    'Added 2026-05-13 (migration 048). Peru is ANDV-endemic (Amazonas, Loreto, '
    'Ucayali departments, upper Amazon basin). JSON API on gob.pe portal; direct '
    'minsa.gob.pe returns 403. Spanish long-form date ("17 de marzo de 2026") '
    'parsed by connector. 9 items on add date. Closes ANDV-region gap. '
    'Beat: hourly minute=52.'
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
