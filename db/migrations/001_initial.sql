-- HORIZON migration 001: initial schema
-- Runs automatically on first Postgres container start (mounted at /docker-entrypoint-initdb.d).
-- Idempotent: safe to re-run on a fresh DB.

\echo '==> HORIZON 001 initial schema'

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Source registry: the canonical list of all 45 ingestion sources.
-- NATO Admiralty defaults set per ICD 206 sourcing methodology.
CREATE TABLE sources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    url                 TEXT NOT NULL,
    tier                SMALLINT NOT NULL CHECK (tier BETWEEN 1 AND 7),
    provenance_type     TEXT NOT NULL CHECK (provenance_type IN (
        'official-authority',
        'peer-reviewed',
        'aggregator',
        'media-confirmed',
        'media-unconfirmed',
        'social-rumour',
        'sequence-record',
        'ecological-indicator'
    )),
    nato_reliability    CHAR(1) NOT NULL CHECK (nato_reliability IN ('A','B','C','D','E','F')),
    nato_credibility    SMALLINT NOT NULL CHECK (nato_credibility BETWEEN 1 AND 6),
    fetch_interval_sec  INTEGER NOT NULL DEFAULT 900,
    enabled             BOOLEAN NOT NULL DEFAULT FALSE,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sources_tier ON sources(tier);
CREATE INDEX idx_sources_enabled ON sources(enabled) WHERE enabled;

-- Per-fetch quality log: every connector run is recorded for the source quality dashboard.
CREATE TABLE source_quality_log (
    id                  BIGSERIAL PRIMARY KEY,
    source_id           UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    http_status         INTEGER,
    latency_ms          INTEGER,
    items_seen          INTEGER NOT NULL DEFAULT 0,
    items_ingested      INTEGER NOT NULL DEFAULT 0,
    items_duplicate     INTEGER NOT NULL DEFAULT 0,
    items_filtered      INTEGER NOT NULL DEFAULT 0,
    parser_version      TEXT NOT NULL,
    error               TEXT
);

CREATE INDEX idx_source_quality_log_source_time
    ON source_quality_log(source_id, fetched_at DESC);

-- Serotype reference table: orthohantaviruses we recognise and classify against.
CREATE TABLE serotypes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    genus               TEXT NOT NULL DEFAULT 'Orthohantavirus',
    syndrome            TEXT,
    geo_distribution    TEXT,
    cfr_estimate_pct    NUMERIC(4,1),
    notes               TEXT
);

-- Raw case reports as ingested from sources. Anonymised: no patient PII.
CREATE TABLE case_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id           UUID NOT NULL REFERENCES sources(id),
    external_id         TEXT NOT NULL,
    src_citation        TEXT NOT NULL,
    title               TEXT NOT NULL,
    summary             TEXT,
    country_iso2        CHAR(2),
    region              TEXT,
    lat                 NUMERIC(9,6),
    lng                 NUMERIC(9,6),
    serotype_id         UUID REFERENCES serotypes(id),
    serotype_text       TEXT,
    reported_date       DATE,
    case_count          INTEGER,
    death_count         INTEGER,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_url             TEXT NOT NULL,
    raw_content_hash    TEXT NOT NULL,
    parser_version      TEXT NOT NULL,
    UNIQUE (source_id, external_id)
);

CREATE INDEX idx_case_reports_country ON case_reports(country_iso2);
CREATE INDEX idx_case_reports_reported_date ON case_reports(reported_date DESC NULLS LAST);
CREATE INDEX idx_case_reports_ingested_at ON case_reports(ingested_at DESC);
CREATE INDEX idx_case_reports_serotype ON case_reports(serotype_id) WHERE serotype_id IS NOT NULL;

-- Dual confidence scoring per record.
-- pipeline_confidence: auto-calculated from NATO score + corroboration + recency.
-- analyst_confidence: human-set after review. Nullable until reviewed.
CREATE TABLE qualification_scores (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_report_id           UUID NOT NULL UNIQUE
                              REFERENCES case_reports(id) ON DELETE CASCADE,
    nato_reliability         CHAR(1) NOT NULL CHECK (nato_reliability IN ('A','B','C','D','E','F')),
    nato_credibility         SMALLINT NOT NULL CHECK (nato_credibility BETWEEN 1 AND 6),
    pipeline_confidence      NUMERIC(3,2) NOT NULL
                              CHECK (pipeline_confidence BETWEEN 0 AND 1),
    pipeline_factors         JSONB NOT NULL DEFAULT '{}'::jsonb,
    analyst_confidence       NUMERIC(3,2)
                              CHECK (analyst_confidence BETWEEN 0 AND 1),
    analyst_id               TEXT,
    analyst_at               TIMESTAMPTZ,
    analyst_notes            TEXT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_qualification_pipeline
    ON qualification_scores(pipeline_confidence DESC);
CREATE INDEX idx_qualification_analyst
    ON qualification_scores(analyst_confidence DESC)
    WHERE analyst_confidence IS NOT NULL;

-- Deduplicated outbreak clusters.
CREATE TABLE clusters (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    country_iso2        CHAR(2),
    region              TEXT,
    serotype_id         UUID REFERENCES serotypes(id),
    started_at          DATE,
    ended_at            DATE,
    status              TEXT NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'closed', 'historical')),
    case_count          INTEGER NOT NULL DEFAULT 0,
    death_count         INTEGER NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE case_to_cluster (
    case_report_id      UUID NOT NULL REFERENCES case_reports(id) ON DELETE CASCADE,
    cluster_id          UUID NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    confidence          NUMERIC(3,2),
    linked_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (case_report_id, cluster_id)
);

-- Generic updated_at trigger.
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sources_touch_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE TRIGGER qualification_scores_touch_updated_at
    BEFORE UPDATE ON qualification_scores
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE TRIGGER clusters_touch_updated_at
    BEFORE UPDATE ON clusters
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Schema version marker.
CREATE TABLE schema_migrations (
    version             TEXT PRIMARY KEY,
    applied_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version) VALUES ('001_initial');

\echo '==> 001 done'
