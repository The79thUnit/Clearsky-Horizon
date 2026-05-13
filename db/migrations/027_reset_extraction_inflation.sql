-- migration 027 — reset per-country counts inflated by the v1.5 extractor.
--
-- Root cause: hondius-v1.5 used article-origin country_iso2 as a fallback
-- (Pass 3) when no country was found near a count. US news articles (NBC,
-- CNN, AP, Reuters) reporting the cluster total got their country_iso2='US'
-- applied to every "11 confirmed / 3 deaths" mention → US counts ballooned.
--
-- Fix in hondius-v1.6: Pass 3 removed. Only explicit in-text attribution
-- (Pass 1/2) produces country-attributed proposals.
--
-- This migration restores the WHO DON 600 / ECDC authoritative baseline
-- from migration 011 for the two inflated countries (US: 11conf 3deaths;
-- ES: 1conf 0deaths vs authoritative US: 1/0, ES: 0/0).
--
-- The extraction_proposals rows remain in the DB (for audit); they are
-- marked rejected=true so the auto-applier will not re-apply them.
-- A fresh run of backfill_hondius_extraction will produce new v1.6
-- proposals with the correct attribution.

BEGIN;

-- ── 1. Reset inflated incident_countries rows ─────────────────────────────

UPDATE incident_countries
SET confirmed_count  = 1,
    suspected_count  = 0,
    deaths           = 0,
    last_updated_at  = now()
WHERE incident_id = (SELECT id FROM incidents WHERE code = 'mv-hondius-2026')
  AND country_iso2 = 'US';

UPDATE incident_countries
SET confirmed_count  = 0,
    suspected_count  = 0,
    deaths           = 0,
    last_updated_at  = now()
WHERE incident_id = (SELECT id FROM incidents WHERE code = 'mv-hondius-2026')
  AND country_iso2 = 'ES';

-- ── 2. Reject the offending extraction proposals ──────────────────────────
-- Only reject v1.5 proposals where the extractor confidence < 0.65 (i.e.,
-- the ones whose country attribution came from article metadata fallback).
-- Pass-1 / Pass-2 proposals (confidence >= 0.65) may have been valid; leave
-- them as-is — they were at most capped by GREATEST anyway.

UPDATE extraction_proposals
SET rejected        = true,
    rejected_reason = 'migration-027: country attributed via article metadata fallback (Pass 3), removed in v1.6',
    notes           = COALESCE(notes, '') ||
                      E'\n[auto-rejected: migration 027 — country attributed via '
                      'article metadata fallback (Pass 3) which was removed in v1.6]'
WHERE incident_code    = 'mv-hondius-2026'
  AND extractor_version = 'hondius-v1.5'
  AND country_iso2      IN ('US', 'ES')
  AND fact_type         IN ('confirmed_count', 'suspected_count', 'death_count')
  AND extractor_confidence < 0.65
  AND rejected = false;

COMMIT;
