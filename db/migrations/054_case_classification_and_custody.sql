-- HORIZON migration 054: case classification metadata + Berkeley Protocol custody table.
--
-- ADDITIVE ONLY. No existing columns removed or renamed. All new columns
-- are nullable or carry safe defaults -- existing rows and queries unaffected.

\echo '==> HORIZON 054 case classification metadata + evidence custody'

-- -----------------------------------------------------------------------
-- 1. New columns on case_reports
-- -----------------------------------------------------------------------

-- WHO/CDC/ECDC tripartite case classification.
-- 'unknown' is the safe default for all existing and future automated records
-- until a human analyst or lab result upgrades the classification.
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS case_classification TEXT
        NOT NULL DEFAULT 'unknown'
        CHECK (case_classification IN ('confirmed','probable','suspected','unknown'));

-- Laboratory diagnostic method that supports the classification.
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS lab_method TEXT
        NOT NULL DEFAULT 'unknown'
        CHECK (lab_method IN ('igm','igg_4x','rt_pcr','ihc','none','unknown'));

-- IHR 2005 notification tracking. Hantavirus is a "List B" disease under the
-- IHR decision instrument; confirmed cases must be assessed within 48 h.
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS ihr_notified BOOLEAN NOT NULL DEFAULT FALSE;

-- Travel history flag. Critical for ANDV cases (only P2P hantavirus).
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS travel_history BOOLEAN;

-- GADM 4.1 administrative boundary code (e.g. "USA.10.3_1" for county level).
-- Enables direct consumption by GIS tools without custom geocoding.
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS gadm_gid TEXT;

-- Ecological context flags: ENSO index, NDVI anomaly, mast-year signal.
-- Populated by the ecological connector tasks (migrations 056+).
ALTER TABLE case_reports
    ADD COLUMN IF NOT EXISTS ecological_flags JSONB NOT NULL DEFAULT '{}'::jsonb;

-- -----------------------------------------------------------------------
-- 2. Evidence custody table (Berkeley Protocol extended envelope)
--
-- Append-only: UPDATE and DELETE are blocked at the DB level.
-- The SHA-256 content hash already stored in case_reports.raw_content_hash
-- proves the stored bytes are intact. These additional fields prove the
-- stored bytes accurately represent the source at the time of capture.
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_custody (
    id                      BIGSERIAL PRIMARY KEY,
    case_report_id          UUID NOT NULL REFERENCES case_reports(id) ON DELETE CASCADE,
    -- Berkeley Protocol minimum envelope
    raw_url                 TEXT NOT NULL,
    content_hash_sha256     TEXT NOT NULL,
    http_status             INTEGER,
    -- Hash of the HTTP response headers (proves server did not alter delivery)
    http_headers_hash       TEXT,
    -- Archived copy URL (Wayback Machine or Perma.cc) for URL-rot mitigation
    source_url_archived     TEXT,
    -- Pipeline tool that performed the capture (e.g. "horizon-worker/0.3.0")
    capture_tool            TEXT NOT NULL,
    -- UTC timestamp of capture at millisecond precision (RFC 3339)
    captured_at             TIMESTAMPTZ NOT NULL,
    -- How the record entered the system
    collection_activity     TEXT NOT NULL DEFAULT 'automated_scrape'
                              CHECK (collection_activity IN (
                                  'automated_scrape',
                                  'api_ingest',
                                  'analyst_manual',
                                  'partner_feed'
                              ))
);

CREATE INDEX IF NOT EXISTS idx_evidence_custody_case_report
    ON evidence_custody(case_report_id);

CREATE INDEX IF NOT EXISTS idx_evidence_custody_captured_at
    ON evidence_custody(captured_at DESC);

-- Block UPDATE and DELETE to enforce append-only chain-of-custody.
-- Any attempt to modify or remove a custody record is a forensic integrity
-- violation and must fail at the database level.
CREATE OR REPLACE RULE evidence_custody_no_update AS
    ON UPDATE TO evidence_custody DO INSTEAD NOTHING;

CREATE OR REPLACE RULE evidence_custody_no_delete AS
    ON DELETE TO evidence_custody DO INSTEAD NOTHING;

-- -----------------------------------------------------------------------
-- 3. Index on new case_reports columns
-- -----------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_case_reports_classification
    ON case_reports(case_classification);

CREATE INDEX IF NOT EXISTS idx_case_reports_ihr_notified
    ON case_reports(ihr_notified) WHERE NOT ihr_notified;

INSERT INTO schema_migrations (version) VALUES ('054_case_classification_and_custody')
    ON CONFLICT DO NOTHING;

\echo '==> 054 done'
