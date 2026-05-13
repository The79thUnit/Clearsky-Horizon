-- HORIZON migration 007: incidents + authoritative counts + cross-source dedup.
--
-- Fixes the category error that made the dashboard say "96 cases" when in
-- reality 96 news articles were ingested describing a much smaller real
-- count of actual cases.
--
-- Concepts:
--   - case_reports = INGESTED ARTICLES from a source. NOT actual patients.
--   - incidents    = REAL OUTBREAK EVENTS (e.g. "MV Hondius cluster"). One
--                    entity per outbreak. The thing the public actually cares
--                    about.
--   - incident_authoritative_counts = the canonical case/death count for an
--                    incident at a point in time, attributed to a specific
--                    authoritative source (WHO DON, CDC HAN, PAHO alert).
--                    The UI shows the most-recent count from the highest-NATO
--                    source. New article from same source updates the count;
--                    new article from different source doesn't double-count.
--   - incident_countries = per-country breakdown of an incident's count.
--                    "UK", "England", "Britain" all resolve to one row keyed
--                    by GB; analyst-merged via country_iso2 PK.
--   - content_topic_hash on case_reports = blake2 hash of normalised title
--                    tokens, used as the dedup key for "same news event from
--                    multiple sources within a recent window".

\echo '==> HORIZON 007 incidents + dedup'

-- ----------------------------------------------------------------------------
-- INCIDENTS
-- ----------------------------------------------------------------------------

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,                          -- 'mv-hondius-2026'
    name TEXT NOT NULL,
    serotype_id UUID REFERENCES serotypes(id),
    started_at DATE,                                    -- first known case / exposure
    ended_at DATE,                                      -- NULL if still active
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','monitoring','closed')),
    summary TEXT,
    -- Primary spatial anchor
    primary_location_country_iso2 TEXT,
    primary_location_name TEXT,
    -- Optional vessel context (for cruise / cargo / research-ship outbreaks)
    primary_vessel_imo TEXT,
    primary_vessel_name TEXT,
    primary_vessel_mmsi TEXT,
    primary_vessel_flag TEXT,
    -- Bookkeeping
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_incidents_status ON incidents (status, started_at DESC);

-- ----------------------------------------------------------------------------
-- AUTHORITATIVE COUNTS  (the truth source for the case number)
-- ----------------------------------------------------------------------------

CREATE TABLE incident_authoritative_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    -- The numbers being claimed
    confirmed_cases INTEGER NOT NULL DEFAULT 0,
    suspected_cases INTEGER NOT NULL DEFAULT 0,
    deaths INTEGER NOT NULL DEFAULT 0,
    recovered INTEGER NOT NULL DEFAULT 0,
    -- Who is making the claim
    source_id UUID NOT NULL REFERENCES sources(id),
    article_id UUID REFERENCES case_reports(id) ON DELETE SET NULL,
    reported_at TIMESTAMPTZ NOT NULL,
    -- NATO Admiralty Scale rating of THIS count
    nato_reliability TEXT NOT NULL,
    nato_credibility INTEGER NOT NULL,
    src_citation TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (incident_id, source_id, reported_at)
);

CREATE INDEX idx_iac_incident_time ON incident_authoritative_counts (incident_id, reported_at DESC);
CREATE INDEX idx_iac_authority ON incident_authoritative_counts (incident_id, nato_reliability, nato_credibility, reported_at DESC);

-- ----------------------------------------------------------------------------
-- PER-COUNTRY BREAKDOWN
-- ----------------------------------------------------------------------------

CREATE TABLE incident_countries (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    country_iso2 TEXT NOT NULL,
    confirmed_count INTEGER NOT NULL DEFAULT 0,
    suspected_count INTEGER NOT NULL DEFAULT 0,
    deaths INTEGER NOT NULL DEFAULT 0,
    first_reported_at DATE,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (incident_id, country_iso2)
);

-- ----------------------------------------------------------------------------
-- LINK ARTICLES <-> INCIDENT  (a case_report can be EVIDENCE for an incident)
-- ----------------------------------------------------------------------------

ALTER TABLE case_reports
    ADD COLUMN incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL;

CREATE INDEX idx_case_reports_incident ON case_reports (incident_id, reported_date DESC NULLS LAST);

-- ----------------------------------------------------------------------------
-- CROSS-SOURCE DEDUP via topic hash
-- ----------------------------------------------------------------------------

ALTER TABLE case_reports
    ADD COLUMN content_topic_hash TEXT;

CREATE INDEX idx_case_reports_topic_hash ON case_reports (content_topic_hash, ingested_at DESC);

-- When N articles share the same topic_hash inside a 7-day window they are
-- the SAME news event. UI groups them as "Reported by N sources" rather than
-- N separate rows. Articles are still stored individually for chain-of-custody.

\echo '==> 007 done (incidents + counts + countries + topic hash column)'
