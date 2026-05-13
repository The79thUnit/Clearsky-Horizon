-- migration 020 — MV Hondius cluster full timeline enrichment
--
-- Source: CNN graphic "Route of the MV Hondius and where passengers
-- disembarked" published 2026-05-08
-- (https://edition.cnn.com/2026/05/08/health/hantavirus-by-the-numbers).
-- Cross-corroborated against existing DB seed (migration 012), WHO DON
-- 600, ECDC update 2026-05-11.
--
-- Adds:
--   - 4 new port entities (Tristan da Cunha, Ascension Island,
--     Praia Cape Verde, Rotterdam)
--   - 3 death event entities (victim 1 at sea, wife in ZA, victim 3 at sea)
--   - Enriched port_call relationships with disembark/evacuation counts
--   - Initial vessel passenger count + projected Rotterdam ETA
--   - vessel_track_points entries for the new ports (port_call source)
--
-- Confidence per relationship is stored in `confidence` column (0..1).
-- Citation goes in `src_citation` for chain-of-custody.

BEGIN;

-- ----------------------------------------------------------------------
-- A. Update existing vessel entity with the initial passenger count
--    and the projected Rotterdam disembark.
-- ----------------------------------------------------------------------

UPDATE entities
SET properties = properties
  || jsonb_build_object(
       'initial_pax_count', 175,
       'voyage_status', 'underway',
       'projected_final_port', 'Rotterdam',
       'projected_final_eta', '2026-05-17',
       'projected_action', 'decontamination + remaining crew disembark'
     )
WHERE entity_type = 'vessel' AND public_label = 'MV Hondius';

-- ----------------------------------------------------------------------
-- B. New port entities (only if not present).
-- ----------------------------------------------------------------------

INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'port',
       'Tristan da Cunha (Edinburgh of the Seven Seas)',
       jsonb_build_object(
         'lat', -37.0676,
         'lng', -12.3107,
         'unlocode', 'SHEDS',
         'country_iso2', 'SH'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE public_label LIKE 'Tristan da Cunha%'
);

INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'port',
       'Georgetown (Ascension Island)',
       jsonb_build_object(
         'lat', -7.9286,
         'lng', -14.4146,
         'unlocode', 'SHASI',
         'country_iso2', 'SH'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE public_label LIKE 'Georgetown%' OR public_label LIKE '%Ascension%'
);

INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'port',
       'Praia (Cape Verde)',
       jsonb_build_object(
         'lat', 14.9177,
         'lng', -23.5092,
         'unlocode', 'CVRAI',
         'country_iso2', 'CV'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE public_label LIKE 'Praia%'
);

INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'port',
       'Rotterdam',
       jsonb_build_object(
         'lat', 51.9244,
         'lng', 4.4777,
         'unlocode', 'NLRTM',
         'country_iso2', 'NL',
         'projected', true
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE public_label = 'Rotterdam'
);

-- ----------------------------------------------------------------------
-- C. Death event entities. New entity_type required — bump the CHECK
--    constraint via ALTER if needed (idempotent).
-- ----------------------------------------------------------------------

DO $$
BEGIN
  -- Drop the old entity_type CHECK and add a wider one that includes death_event
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'entities_entity_type_check'
  ) THEN
    ALTER TABLE entities DROP CONSTRAINT entities_entity_type_check;
  END IF;
  ALTER TABLE entities ADD CONSTRAINT entities_entity_type_check CHECK (
    entity_type IN (
      'vessel','port','excursion','country','voyage','port_call',
      'person','incident','death_event','planned_event'
    )
  );
END $$;

-- Death 1: victim 1 (probable index, Dutch male, 70yo) — 11 April 2026, at sea
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'death_event',
       'Death — victim 1 (index case)',
       jsonb_build_object(
         'lat', -32.0,                 -- approximate at-sea position between Tristan da Cunha and St Helena
         'lng', -10.0,
         'occurred_at', '2026-04-11',
         'subject', 'probable index case (M, 70, NL)',
         'location_type', 'at_sea',
         'pcr_confirmed', false,
         'confidence', 1.0,
         'source', 'CNN 2026-05-08; corroborated by DB seed migration 012'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities
  WHERE entity_type = 'death_event' AND public_label LIKE '%victim 1%'
);

-- Death 2: wife of victim 1 (confirmed index, F, 69, NL) — 26 April, South Africa
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'death_event',
       'Death — victim 2 (wife of index, cluster anchor)',
       jsonb_build_object(
         'lat', -33.9249,
         'lng', 18.4241,                 -- Cape Town (medevac destination)
         'occurred_at', '2026-04-26',
         'subject', 'PCR-confirmed case spouse (F, 69, NL)',
         'location_type', 'hospital',
         'pcr_confirmed', true,
         'confidence', 1.0,
         'source', 'CNN 2026-05-08; WHO DON 600; corroborated by DB seed'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities
  WHERE entity_type = 'death_event' AND public_label LIKE '%victim 2%'
);

-- Death 3: third victim — 2 May 2026, at sea between Ascension and Cape Verde
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(),
       (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'death_event',
       'Death — victim 3',
       jsonb_build_object(
         'lat', 4.0,                    -- approximate at-sea between Ascension and Cape Verde
         'lng', -19.0,
         'occurred_at', '2026-05-02',
         'subject', 'third fatality (identity not public)',
         'location_type', 'at_sea',
         'pcr_confirmed', null,
         'confidence', 0.95,
         'source', 'CNN 2026-05-08'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities
  WHERE entity_type = 'death_event' AND public_label LIKE '%victim 3%'
);

-- ----------------------------------------------------------------------
-- D. Port-call relationships enriched with disembark / evacuation counts.
--    Drop old port-call rows for known ports, re-insert with full props.
-- ----------------------------------------------------------------------

-- Get IDs we just inserted
WITH vessel AS (
  SELECT id FROM entities WHERE entity_type = 'vessel' AND public_label = 'MV Hondius'
),
incident AS (
  SELECT id FROM incidents WHERE code = 'mv-hondius-2026'
),
trc AS (SELECT id FROM entities WHERE public_label LIKE 'Tristan da Cunha%' LIMIT 1),
asc_ AS (SELECT id FROM entities WHERE public_label LIKE 'Georgetown%' OR public_label LIKE '%Ascension%' LIMIT 1),
cpv AS (SELECT id FROM entities WHERE public_label LIKE 'Praia%' LIMIT 1),
rot AS (SELECT id FROM entities WHERE public_label = 'Rotterdam' LIMIT 1)

INSERT INTO relationships (id, src_id, dst_id, rel_type, properties, confidence, src_citation)
SELECT gen_random_uuid(), vessel.id, trc.id, 'port_called',
       jsonb_build_object(
         'at', '2026-04-13',
         'departed_at', '2026-04-16',
         'disembarked', 1,
         'evacuated', 0,
         'note', 'one passenger disembarked; first time off ship since Ushuaia'
       ),
       1.0,
       'CNN 2026-05-08 graphic'
FROM vessel, trc
WHERE NOT EXISTS (
  SELECT 1 FROM relationships r
  WHERE r.src_id = vessel.id AND r.dst_id = trc.id AND r.rel_type = 'port_called'
)
UNION ALL
SELECT gen_random_uuid(), vessel.id, asc_.id, 'port_called',
       jsonb_build_object(
         'at', '2026-04-27',
         'disembarked', 0,
         'evacuated', 2,
         'evac_pcr_positive', 1,
         'note', 'two passengers evacuated; one later PCR-confirmed hantavirus'
       ),
       1.0,
       'CNN 2026-05-08 graphic'
FROM vessel, asc_
WHERE NOT EXISTS (
  SELECT 1 FROM relationships r
  WHERE r.src_id = vessel.id AND r.dst_id = asc_.id AND r.rel_type = 'port_called'
)
UNION ALL
SELECT gen_random_uuid(), vessel.id, cpv.id, 'port_called',
       jsonb_build_object(
         'at', '2026-05-06',
         'disembarked', 0,
         'evacuated', 3,
         'note', 'three evacuations; symptomatic / contact-traced'
       ),
       1.0,
       'CNN 2026-05-08 graphic'
FROM vessel, cpv
WHERE NOT EXISTS (
  SELECT 1 FROM relationships r
  WHERE r.src_id = vessel.id AND r.dst_id = cpv.id AND r.rel_type = 'port_called'
)
UNION ALL
SELECT gen_random_uuid(), vessel.id, rot.id, 'planned_arrival',
       jsonb_build_object(
         'at', '2026-05-17',
         'projected', true,
         'note', 'remaining crew + medical staff to disembark; ship to be decontaminated'
       ),
       0.7,
       'CNN 2026-05-08 (estimated)'
FROM vessel, rot
WHERE NOT EXISTS (
  SELECT 1 FROM relationships r
  WHERE r.src_id = vessel.id AND r.dst_id = rot.id AND r.rel_type = 'planned_arrival'
);

-- Bump existing St Helena port_call with the disembark count of 32 (was just medevac note)
UPDATE relationships
SET properties = properties
  || jsonb_build_object(
       'disembarked', 32,
       'includes_body', true,
       'note', '32 disembark, including body of victim 1 + symptomatic wife; CNN-corroborated'
     )
WHERE rel_type = 'port_called'
  AND dst_id = (SELECT id FROM entities WHERE public_label = 'Saint Helena');

-- Tenerife — add full evacuation count
UPDATE relationships
SET properties = properties
  || jsonb_build_object(
       'evacuated', 122,
       'flown_home', true,
       'note', '122 crew + passengers evacuated and flown home from TFN-S'
     )
WHERE rel_type IN ('arrived_at', 'port_called')
  AND dst_id = (SELECT id FROM entities WHERE public_label = 'Tenerife (Santa Cruz)');

-- ----------------------------------------------------------------------
-- E. vessel_track_points for the new ports so the polyline draws cleanly.
-- ----------------------------------------------------------------------

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-04-13 12:00:00+00', -37.0676, -12.3107, 'port_call',
       'CNN 2026-05-08 graphic — Tristan da Cunha disembark Apr 13-16'
FROM entities v WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-04-27 10:00:00+00', -7.9286, -14.4146, 'port_call',
       'CNN 2026-05-08 graphic — Ascension Island Apr 27 (2 evac, 1 PCR+)'
FROM entities v WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-05-06 09:00:00+00', 14.9177, -23.5092, 'port_call',
       'CNN 2026-05-08 graphic — Praia Cape Verde May 6 (3 evac)'
FROM entities v WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

-- Projected next leg — Rotterdam (planned, future ts)
INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-05-17 12:00:00+00', 51.9244, 4.4777, 'port_call',
       'CNN 2026-05-08 graphic — Rotterdam projected May 17 (decontam)'
FROM entities v WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

COMMIT;
