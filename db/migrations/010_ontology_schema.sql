-- HORIZON migration 010: ontology schema.
--
-- Adds entities + relationships + vessel_track_points so we can model:
--   - Vessel (MV Hondius)
--   - Port (Ushuaia, Saint Helena, Cape Town, Tenerife)
--   - Excursion (Ushuaia landfill bird-watching site)
--   - Person (opaque UUID; public-label only; no names per CLAUDE.md rule 3)
--   - Voyage (vessel leg, with embark + disembark ports)
--   - Country (ISO2; nationality vs death-location distinction)
--
-- Typed edges between entities carry confidence + ICD-206 SRC citation.

\echo '==> HORIZON 010 ontology schema'

CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'vessel','port','excursion','country','voyage','port_call','person','incident'
    )),
    public_label TEXT,   -- public-facing label only; NULL for sensitive person entities
    properties JSONB NOT NULL DEFAULT '{}',
    -- Soft FK to the incident this entity is bound to (NULL = global entity).
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_entities_type ON entities (entity_type);
CREATE INDEX idx_entities_incident ON entities (incident_id) WHERE incident_id IS NOT NULL;
CREATE INDEX idx_entities_label ON entities (public_label) WHERE public_label IS NOT NULL;


CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    src_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    dst_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    rel_type TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    confidence NUMERIC(3,2) NOT NULL DEFAULT 0.85 CHECK (confidence BETWEEN 0 AND 1),
    src_citation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (src_id, dst_id, rel_type)
);

CREATE INDEX idx_relationships_src ON relationships (src_id, rel_type);
CREATE INDEX idx_relationships_dst ON relationships (dst_id, rel_type);


CREATE TABLE vessel_track_points (
    id BIGSERIAL PRIMARY KEY,
    vessel_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    lat NUMERIC(10,7) NOT NULL,
    lng NUMERIC(10,7) NOT NULL,
    speed_knots NUMERIC(5,2),
    heading NUMERIC(4,1),
    accuracy_m INTEGER,
    source TEXT NOT NULL CHECK (source IN ('aisstream','marinetraffic','port_call','manual')),
    src_citation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vtp_vessel_ts ON vessel_track_points (vessel_entity_id, ts DESC);

-- View for the live vessel feed (last 90 days, decimated for UI).
CREATE OR REPLACE VIEW v_vessel_track_recent AS
SELECT
    vessel_entity_id,
    ts, lat, lng, speed_knots, heading, source
FROM vessel_track_points
WHERE ts >= NOW() - INTERVAL '90 days'
ORDER BY ts ASC;

\echo '==> 010 done (entities + relationships + vessel_track_points)'
