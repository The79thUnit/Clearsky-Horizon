-- migration 024 — extraction_proposals: structured facts pulled out of
-- ingested news/bulletin articles. Closes the loop between the
-- already-live article ingestion (cases table) and the incident ontology
-- (incident_countries, entities, relationships) so that the map updates
-- as new WHO DON / ECDC / CDC HAN bulletins land.
--
-- Audit-trail design: every proposal stores WHICH article (case_id),
-- WHAT was claimed (fact_type, value), WHO said it (source_code, nato_score),
-- and whether it was auto-applied or queued for analyst review.
--
-- Auto-apply policy (enforced by the worker, not the DB):
--   - NATO score in {A1, A2, B1, B2} → auto-apply if ≥1 corroborating
--     source within 48h
--   - All other tiers → leave applied=false, surface in Reports view

BEGIN;

CREATE TABLE IF NOT EXISTS extraction_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Provenance
    case_id UUID NOT NULL REFERENCES case_reports(id) ON DELETE CASCADE,
    incident_code TEXT NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    extractor_version TEXT NOT NULL,

    -- What was claimed
    fact_type TEXT NOT NULL CHECK (fact_type IN (
        'death_count',          -- "X dead/deaths/fatalities"
        'confirmed_count',      -- "X confirmed cases"
        'suspected_count',      -- "X probable / suspected"
        'port_call',            -- ship docked at <port> on <date>
        'death_event',          -- specific death (date, location)
        'evacuation_event',     -- N evacuated from port on date
        'flight_route'          -- repatriation flight from→to
    )),
    country_iso2 TEXT,
    value_numeric INTEGER,
    value_date DATE,
    value_text TEXT,             -- port name, city, free-text fact
    value_lat DOUBLE PRECISION,  -- when fact_type involves a location
    value_lng DOUBLE PRECISION,

    -- Source quality (NATO Admiralty Scale)
    source_code TEXT NOT NULL,           -- 'who-don', 'ecdc-tessy', etc.
    source_url TEXT NOT NULL,
    nato_reliability CHAR(1)
        CHECK (nato_reliability IS NULL OR nato_reliability IN ('A','B','C','D','E','F')),
    nato_credibility CHAR(1)
        CHECK (nato_credibility IS NULL OR nato_credibility IN ('1','2','3','4','5','6')),
    extractor_confidence REAL,           -- 0..1

    -- Application status
    applied BOOLEAN NOT NULL DEFAULT false,
    applied_at TIMESTAMPTZ,
    applied_target TEXT,                 -- "incident_countries.NL.confirmed_count" etc.
    rejected BOOLEAN NOT NULL DEFAULT false,
    rejected_reason TEXT,

    -- Idempotency
    fingerprint TEXT NOT NULL,           -- hash of (case_id, fact_type, country, value)
    notes TEXT,

    CONSTRAINT extraction_proposals_fingerprint_unique UNIQUE (fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_extraction_proposals_incident
    ON extraction_proposals (incident_code, extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_extraction_proposals_case
    ON extraction_proposals (case_id);
CREATE INDEX IF NOT EXISTS idx_extraction_proposals_applied
    ON extraction_proposals (applied, fact_type)
    WHERE applied = false AND rejected = false;

COMMENT ON TABLE extraction_proposals IS
'Structured facts pulled out of ingested articles by the rule-based '
'extractor. Auto-applies high-confidence facts to incident_countries / '
'entities / relationships; leaves the rest for analyst review.';

COMMIT;
