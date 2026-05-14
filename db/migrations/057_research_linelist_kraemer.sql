-- HORIZON migration 057: add research-linelist provenance type, seed kraemer-oxford.
--
-- The Oxford Kraemer Lab (github.com/kraemer-lab/Hondius_hantavirus_h2026)
-- maintains an individual-level epidemiological line list for the 2026 ANDV
-- cluster aboard the MV Hondius. Contributors: Moritz Kraemer (Oxford),
-- Sam Scarpino, Andrew Rambaut (Edinburgh / Nextstrain). Licence: CC0 1.0.
--
-- This is different from all existing provenance types:
--   official-authority  → government/intergovernmental agencies
--   peer-reviewed       → journal publications
--   research-linelist   → living curated academic datasets (GitHub, figshare,
--                         Zenodo) that are NOT formal publications but have
--                         institutional authorship and cited sourcing.
--
-- The CHECK constraint on sources.provenance_type must be extended before
-- the INSERT. We locate the constraint by inspecting pg_constraint so the
-- migration is robust to whatever name PostgreSQL assigned at creation time.

\echo '==> HORIZON 057 research-linelist type + kraemer-oxford source'

DO $$
DECLARE
    cname text;
BEGIN
    SELECT c.conname INTO cname
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    WHERE t.relname = 'sources'
      AND c.contype = 'c'
      AND pg_get_constraintdef(c.oid) LIKE '%provenance_type%';

    IF cname IS NOT NULL THEN
        EXECUTE 'ALTER TABLE sources DROP CONSTRAINT ' || quote_ident(cname);
    END IF;
END $$;

ALTER TABLE sources
    ADD CONSTRAINT sources_provenance_type_check
    CHECK (provenance_type IN (
        'official-authority',
        'peer-reviewed',
        'aggregator',
        'media-confirmed',
        'media-unconfirmed',
        'social-rumour',
        'sequence-record',
        'ecological-indicator',
        'research-linelist'
    ));

-- Kraemer Lab / University of Oxford — MV Hondius line list.
-- Living CC0 dataset updated with each new confirmed case. Source is
-- individual-level (one row per person), which is the highest resolution
-- available for this outbreak. Cross-referenced against WHO DON600, CDC,
-- BBC, Guardian, APNews, and national health authority press releases.
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility,
                     fetch_interval_sec, enabled, notes)
VALUES (
    'kraemer-oxford',
    'Oxford Kraemer Lab — MV Hondius ANDV Line List (2026)',
    'https://github.com/kraemer-lab/Hondius_hantavirus_h2026',
    2,
    'research-linelist',
    'B',
    2,
    21600,  -- every 6h: updated at least daily during active outbreak
    TRUE,
    'Added 2026-05-14 (migration 057). Oxford Kraemer Lab / Sam Scarpino / '
    'Andrew Rambaut curated individual-level line list for the 2026 Andes '
    'orthohantavirus (ANDV) cluster aboard MV Hondius cruise ship. '
    '28-column schema: status, symptom_onset, outcome, nationality, '
    'treatment, travel, flight, Pathoplexus accession_id. CC0 licence. '
    'Raw CSV: github.com/kraemer-lab/Hondius_hantavirus_h2026/main/data/'
    'linelist/2026_hantavirus.csv. NATO B2: academic group '
    '(Oxford/Edinburgh), sources column cross-references WHO DON600 and '
    'national health authority press releases for every row. '
    'Beat: minute=13, hour=*/6 UTC.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    fetch_interval_sec = EXCLUDED.fetch_interval_sec,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

INSERT INTO schema_migrations (version) VALUES ('057_research_linelist_kraemer')
    ON CONFLICT DO NOTHING;

\echo '==> 057 done (research-linelist type added + kraemer-oxford seeded)'
