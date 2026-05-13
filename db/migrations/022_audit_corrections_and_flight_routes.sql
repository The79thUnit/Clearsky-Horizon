-- migration 022 — triple-audit corrections + flight repatriation routes
--
-- Coordinate corrections (verified against Wikipedia + UN/LOCODE):
--   - St Helena Jamestown port: -15.9650,-5.7089 → -15.9252,-5.7281
--   - Cape Town death event   : -33.9249,18.4241 → -33.9396,18.4644
--     (Groote Schuur Hospital exact coordinates — where the wife died)
--
-- Flight branches added per CNN graphic + WHO/ECDC repatriation data:
--   1. St Helena → Cape Town       — medevac of victim 2 (HIGH conf)
--   2. Ascension Island → UK       — RAF Brize Norton typical route (MED)
--   3. Praia, Cape Verde → Lisbon  — TAP hub for European return (MED)
--   4. Tenerife → Amsterdam        — NL repatriation (HIGH — confirmed cases)
--   5. Tenerife → Paris            — FR repatriation (HIGH — confirmed case)
--   6. Tenerife → Boston (proxy)   — US repatriation (HIGH — confirmed case)
--   7. Tenerife → Cape Town        — ZA repatriation (MED — assumed)
--
-- Stored as `flight_route` entities so the front-end can render them as
-- a distinct curved layer (separate from the vessel polyline). Each
-- entity carries: origin coords, destination coords, evac date, count,
-- confidence, source citation.

BEGIN;

-- 1. Port coordinate corrections ----------------------------------------

UPDATE entities
SET properties = properties || jsonb_build_object(
  'lat', -15.9252,
  'lng', -5.7281,
  'coord_source', 'UN/LOCODE SHJAM + Wikipedia Jamestown harbour'
)
WHERE entity_type = 'port' AND public_label = 'Saint Helena';

UPDATE entities
SET properties = properties || jsonb_build_object(
  'lat', -33.9396,
  'lng', 18.4644,
  'location_name', 'Groote Schuur Hospital, Cape Town',
  'coord_source', 'Wikipedia Groote Schuur Hospital'
)
WHERE entity_type = 'death_event' AND public_label LIKE '%victim 2%';

-- 2. New entity_type: flight_route -------------------------------------

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'entities_entity_type_check'
  ) THEN
    ALTER TABLE entities DROP CONSTRAINT entities_entity_type_check;
  END IF;
  ALTER TABLE entities ADD CONSTRAINT entities_entity_type_check CHECK (
    entity_type IN (
      'vessel','port','excursion','country','voyage','port_call',
      'person','incident','death_event','planned_event','flight_route'
    )
  );
END $$;

-- 3. Flight repatriation routes (7 total) -------------------------------

WITH incid AS (SELECT id FROM incidents WHERE code = 'mv-hondius-2026')

-- 3a. St Helena → Cape Town: confirmed medevac of victim 2 (became death)
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), incid.id, 'flight_route', 'Medevac flight — St Helena → Cape Town',
       jsonb_build_object(
         'origin_label',  'Saint Helena',
         'origin_lat',    -15.9252, 'origin_lng',    -5.7281,
         'dest_label',    'Cape Town (Groote Schuur Hospital)',
         'dest_lat',      -33.9396, 'dest_lng',      18.4644,
         'flown_at',      '2026-04-24',
         'pax_count',     1,
         'purpose',       'medevac',
         'subject',       'index case spouse (F, 69, NL) — became victim 2',
         'confidence',    1.0,
         'source',        'CNN 2026-05-08 + WHO DON 600',
         'arrived_alive', false
       )
FROM incid
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Medevac flight — St Helena → Cape Town'
);

-- 3b. Ascension Island → UK (Brize Norton typical for RAF Ascension)
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Evacuation flight — Ascension Island → UK',
       jsonb_build_object(
         'origin_label',  'Georgetown (Ascension Island)',
         'origin_lat',    -7.9286, 'origin_lng',    -14.4146,
         'dest_label',    'RAF Brize Norton (UK)',
         'dest_lat',      51.7500, 'dest_lng',      -1.5837,
         'flown_at',      '2026-04-27',
         'pax_count',     2,
         'purpose',       'evacuation',
         'subject',       '2 passengers — 1 later PCR+ hantavirus',
         'confidence',    0.7,
         'source',        'CNN 2026-05-08 + standard RAF Ascension repat route',
         'note',          'RAF Voyager / typical Ascension repatriation route'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Evacuation flight — Ascension Island → UK'
);

-- 3c. Praia, Cape Verde → Lisbon (TAP hub for EU return)
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Evacuation flight — Praia → Lisbon',
       jsonb_build_object(
         'origin_label',  'Praia (Cape Verde)',
         'origin_lat',    14.9177, 'origin_lng',    -23.5092,
         'dest_label',    'Lisbon (LIS — TAP hub)',
         'dest_lat',      38.7813, 'dest_lng',      -9.1359,
         'flown_at',      '2026-05-06',
         'pax_count',     3,
         'purpose',       'evacuation',
         'subject',       '3 passengers — symptomatic / contact-traced',
         'confidence',    0.7,
         'source',        'CNN 2026-05-08 + TAP Cape Verde routing',
         'note',          'TAP Air Portugal is the primary Cape Verde → Europe carrier'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Evacuation flight — Praia → Lisbon'
);

-- 3d. Tenerife → Amsterdam — NL repatriation (confirmed NL cases)
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Repatriation flight — Tenerife → Amsterdam',
       jsonb_build_object(
         'origin_label',  'Tenerife (TFS / TFN)',
         'origin_lat',    28.4682, 'origin_lng',    -16.2546,
         'dest_label',    'Amsterdam (AMS)',
         'dest_lat',      52.3676, 'dest_lng',      4.9041,
         'flown_at',      '2026-05-10',
         'pax_count',     null,
         'purpose',       'repatriation',
         'subject',       'NL passengers — patient zero + spouse home country',
         'confidence',    0.95,
         'source',        'CNN 2026-05-08 (122 evacuated and flown home) + DB NL=2 confirmed cases'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Repatriation flight — Tenerife → Amsterdam'
);

-- 3e. Tenerife → Paris — FR repatriation
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Repatriation flight — Tenerife → Paris',
       jsonb_build_object(
         'origin_label',  'Tenerife (TFS / TFN)',
         'origin_lat',    28.4682, 'origin_lng',    -16.2546,
         'dest_label',    'Paris (CDG)',
         'dest_lat',      48.8566, 'dest_lng',      2.3522,
         'flown_at',      '2026-05-10',
         'pax_count',     null,
         'purpose',       'repatriation',
         'subject',       'FR passengers — DB has 1 confirmed FR case',
         'confidence',    0.9,
         'source',        'CNN 2026-05-08 + DB FR=1 confirmed case'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Repatriation flight — Tenerife → Paris'
);

-- 3f. Tenerife → Boston (US) — US repatriation, east-coast hub proxy
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Repatriation flight — Tenerife → Boston',
       jsonb_build_object(
         'origin_label',  'Tenerife (TFS / TFN)',
         'origin_lat',    28.4682, 'origin_lng',    -16.2546,
         'dest_label',    'Boston (BOS — proxy for east coast)',
         'dest_lat',      42.3601, 'dest_lng',      -71.0589,
         'flown_at',      '2026-05-10',
         'pax_count',     null,
         'purpose',       'repatriation',
         'subject',       'US passengers — DB has 1 confirmed US case (exact city undisclosed)',
         'confidence',    0.8,
         'source',        'CNN 2026-05-08 + DB US=1 confirmed case'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Repatriation flight — Tenerife → Boston'
);

-- 3g. Tenerife → Cape Town — ZA repatriation (we have ZA fatality data)
INSERT INTO entities (id, incident_id, entity_type, public_label, properties)
SELECT gen_random_uuid(), (SELECT id FROM incidents WHERE code = 'mv-hondius-2026'),
       'flight_route', 'Repatriation flight — Tenerife → Cape Town',
       jsonb_build_object(
         'origin_label',  'Tenerife (TFS / TFN)',
         'origin_lat',    28.4682, 'origin_lng',    -16.2546,
         'dest_label',    'Cape Town (CPT)',
         'dest_lat',      -33.9249, 'dest_lng',      18.4241,
         'flown_at',      '2026-05-10',
         'pax_count',     null,
         'purpose',       'repatriation',
         'subject',       'ZA passengers / crew returning home',
         'confidence',    0.6,
         'source',        'CNN 2026-05-08 + DB ZA=1 fatality (post-medevac) suggests ZA pax present',
         'note',          'Lower confidence — ZA contingent inferred from medevac + crew profile'
       )
WHERE NOT EXISTS (
  SELECT 1 FROM entities WHERE entity_type='flight_route'
    AND public_label = 'Repatriation flight — Tenerife → Cape Town'
);

COMMIT;
