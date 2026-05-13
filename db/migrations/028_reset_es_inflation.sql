-- migration 028 — reset Spain (ES) counts inflated by v1.6 corroboration path.
--
-- Root cause: v1.6 Path B (corroboration) took MAX(value_numeric) across
-- articles that mentioned Spain + cluster-total counts ("confirmed infections
-- grow to 9", "cases rise to 11 as Spanish passenger falls ill"). MAX=11
-- exceeded the WHO-confirmed total of 7 but was still applied.
--
-- Fix in extraction.py: Path A and Path B now reject proposals whose
-- value_numeric >= global_cap_confirmed (7 from WHO DON 600).
--
-- Correct authoritative value per migration 011: ES=0 confirmed.
-- (Tenerife is the evacuation port; the Spanish passenger case mentioned
-- in media was a one-off report — authoritative sources do not confirm
-- a Spanish-national case in their per-country breakdown.)

BEGIN;

-- Reset ES confirmed_count to authoritative 0.
UPDATE incident_countries
SET confirmed_count = 0,
    last_updated_at = now()
WHERE incident_id = (SELECT id FROM incidents WHERE code = 'mv-hondius-2026')
  AND country_iso2 = 'ES';

-- Mark offending v1.6 ES proposals as rejected so they are not re-applied.
UPDATE extraction_proposals
SET rejected        = true,
    rejected_reason = 'migration-028: value >= global_cap_confirmed (cluster-total misattribution, ES corroboration path)',
    notes           = COALESCE(notes, '') ||
                      E'\n[auto-rejected: migration 028 — global cap filter]'
WHERE incident_code  = 'mv-hondius-2026'
  AND country_iso2   = 'ES'
  AND fact_type      = 'confirmed_count'
  AND value_numeric  >= 7   -- global confirmed cap from WHO DON 600
  AND extractor_version IN ('hondius-v1.5', 'hondius-v1.6')
  AND rejected = false;

COMMIT;
