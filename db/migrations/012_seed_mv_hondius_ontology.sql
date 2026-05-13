-- HORIZON migration 012: seed the MV Hondius ontology graph.
--
-- Personal names are NOT stored. Person entities carry
-- only public attributes that have already appeared in WHO / CDC / ECDC
-- bulletins: nationality, sex, age, role, status, dates of clinically-relevant
-- public events (symptoms onset, hospitalisation, death). No identifying name.
--
-- Sources for the seeded facts:
--   - WHO Disease Outbreak News 2026-DON600 (2026-05-11)
--   - ECDC surveillance update https://www.ecdc.europa.eu/en/infectious-disease-topics/hantavirus-infection/surveillance-and-updates/andes-hantavirus-outbreak
--   - Reuters / Guardian / Le Monde / France 24 / AP / BBC coverage 2026-05-09..11

\echo '==> HORIZON 012 seed MV Hondius ontology graph'

-- ----------------------------------------------------------------------------
-- 1) VESSEL entity
-- ----------------------------------------------------------------------------
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT
    'vessel',
    'MV Hondius',
    jsonb_build_object(
        'imo', '9818709',
        'mmsi', '244327000',
        'flag_iso2', 'NL',
        'operator', 'Oceanwide Expeditions',
        'type', 'polar expedition cruise',
        'length_m', 107,
        'passenger_capacity_approx', 174
    ),
    i.id
FROM incidents i WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2) PORT entities (chronological port-call sequence)
-- ----------------------------------------------------------------------------
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT 'port', port_name,
       jsonb_build_object('country_iso2', country, 'lat', lat, 'lng', lng, 'unlocode', unlocode),
       i.id
FROM incidents i
CROSS JOIN (VALUES
    ('Ushuaia',        'AR', -54.8019, -68.3030, 'ARUSH'),
    ('Saint Helena',   'SH', -15.9650,  -5.7089, 'SHJAM'),
    ('Cape Town',      'ZA', -33.9180,  18.4233, 'ZACPT'),
    ('Tenerife (Santa Cruz)', 'ES', 28.4682, -16.2546, 'ESSCT')
) AS p(port_name, country, lat, lng, unlocode)
WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3) EXCURSION entity: the suspected pre-departure exposure event
-- ----------------------------------------------------------------------------
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT
    'excursion',
    'Ushuaia landfill bird-watching (pre-departure)',
    jsonb_build_object(
        'location_name', 'Ushuaia landfill site',
        'country_iso2', 'AR',
        'region', 'Tierra del Fuego',
        'date_window_start', '2026-03-25',
        'date_window_end', '2026-03-31',
        'activity', 'bird-watching',
        'suspected_reservoir', 'Oligoryzomys longicaudatus (long-tailed pygmy rice rat)',
        'serotype', 'ANDV',
        'notes', 'Pre-boarding 3-month overland trip across Argentina/Chile/Uruguay; landfill visited just before boarding the MV Hondius'
    ),
    i.id
FROM incidents i WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 4) VOYAGE entity: the cruise leg
-- ----------------------------------------------------------------------------
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT
    'voyage',
    'MV Hondius voyage Ushuaia → Tenerife (Apr 2026)',
    jsonb_build_object(
        'departed_port', 'Ushuaia',
        'departed_at', '2026-04-01',
        'arrived_port', 'Tenerife',
        'arrived_at', '2026-05-10',
        'passenger_count_approx', 110,
        'crew_count_approx', 60
    ),
    i.id
FROM incidents i WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5) PERSON entities (opaque; no names)
-- ----------------------------------------------------------------------------
-- Index case: 70M Dutch passenger; probable; deceased on-board 2026-04-11
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT
    'person',
    'Patient zero (M, 70, NL, probable, deceased)',
    jsonb_build_object(
        'sex', 'M',
        'age', 70,
        'nationality_iso2', 'NL',
        'role', 'passenger',
        'case_status', 'probable',
        'serotype', 'ANDV',
        'symptoms_onset', '2026-04-06',
        'symptoms_initial', 'fever / headache / diarrhea',
        'died_at', '2026-04-11',
        'died_location', 'aboard MV Hondius at sea',
        'pcr_status', 'not sampled before death; classified probable based on epidemiology',
        'narrative', 'Index case. Symptoms developed five days after boarding. Rapid progression to respiratory distress; died on board. Hantavirus not initially suspected because early symptoms mirrored common respiratory illness.'
    ),
    i.id
FROM incidents i WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- Spouse: 69F Dutch passenger; PCR-confirmed; deceased in South Africa 2026-04-26
INSERT INTO entities (entity_type, public_label, properties, incident_id)
SELECT
    'person',
    'Index case spouse (F, 69, NL, confirmed, deceased)',
    jsonb_build_object(
        'sex', 'F',
        'age', 69,
        'nationality_iso2', 'NL',
        'role', 'passenger',
        'case_status', 'confirmed',
        'serotype', 'ANDV',
        'disembarked_at_port', 'Saint Helena',
        'disembarked_at_date', '2026-04-24',
        'died_at', '2026-04-26',
        'died_location_country_iso2', 'ZA',
        'died_location', 'South Africa (after medical evacuation from Saint Helena)',
        'pcr_status', 'PCR-confirmed Andes hantavirus post-mortem; this is the laboratory anchor of the cluster',
        'narrative', 'Case 2. Disembarked at Saint Helena symptomatic on 2026-04-24; medevacked to South Africa where she died 2026-04-26. PCR-confirmed Andes hantavirus on her samples — this is the test result that confirmed the outbreak source.'
    ),
    i.id
FROM incidents i WHERE i.code = 'mv-hondius-2026'
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------------------------
-- 6) RELATIONSHIPS
-- ----------------------------------------------------------------------------

-- Helper CTEs by entity public_label scoped to this incident.
-- (We use a transaction here so the inserts below see the entities just created.)

WITH ids AS (
    SELECT
        (SELECT id FROM entities WHERE entity_type='vessel'    AND public_label='MV Hondius' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS vessel_id,
        (SELECT id FROM entities WHERE entity_type='voyage'    AND public_label='MV Hondius voyage Ushuaia → Tenerife (Apr 2026)' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS voyage_id,
        (SELECT id FROM entities WHERE entity_type='excursion' AND public_label='Ushuaia landfill bird-watching (pre-departure)' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS excursion_id,
        (SELECT id FROM entities WHERE entity_type='port'      AND public_label='Ushuaia' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS ushuaia_id,
        (SELECT id FROM entities WHERE entity_type='port'      AND public_label='Saint Helena' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS sthelena_id,
        (SELECT id FROM entities WHERE entity_type='port'      AND public_label='Cape Town' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS capetown_id,
        (SELECT id FROM entities WHERE entity_type='port'      AND public_label='Tenerife (Santa Cruz)' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS tenerife_id,
        (SELECT id FROM entities WHERE entity_type='person'    AND public_label='Patient zero (M, 70, NL, probable, deceased)' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS pz_id,
        (SELECT id FROM entities WHERE entity_type='person'    AND public_label='Index case spouse (F, 69, NL, confirmed, deceased)' AND incident_id=(SELECT id FROM incidents WHERE code='mv-hondius-2026')) AS spouse_id
)
INSERT INTO relationships (src_id, dst_id, rel_type, properties, confidence, src_citation)
SELECT src, dst, rel, props, conf, cit FROM ids,
LATERAL (VALUES
    -- Voyage <-> Vessel
    (voyage_id,    vessel_id,    'on_vessel',     '{}'::jsonb, 1.00,
     '[PUBLIC] Oceanwide Expeditions itinerary 2026; cross-checked WHO DON 600'),
    -- Voyage <-> Ports (departed / arrived)
    (voyage_id,    ushuaia_id,   'departed_from', jsonb_build_object('at','2026-04-01'), 0.99,
     '[PUBLIC] WHO DON 600 names Ushuaia 2026-04-01 as cruise departure'),
    (voyage_id,    tenerife_id,  'arrived_at',    jsonb_build_object('at','2026-05-10'), 0.99,
     '[PUBLIC] AP/Reuters/Al Jazeera 2026-05-10 cruise dock Tenerife'),
    -- Voyage's intermediate calls
    (voyage_id,    sthelena_id,  'port_called',   jsonb_build_object('at','2026-04-24','note','medevac of symptomatic passenger'), 0.95,
     '[PUBLIC] WHO DON 600 + BBC 2026-05-10 paratrooper assist on St Helena'),
    (voyage_id,    capetown_id,  'medevac_destination', jsonb_build_object('at','2026-04-26','note','spouse died here'), 0.95,
     '[PUBLIC] WHO DON 600 — spouse PCR-confirmed post-mortem in ZA'),
    -- Excursion location
    (excursion_id, ushuaia_id,   'at_port',       '{}'::jsonb, 0.95,
     '[PUBLIC] Argentine Health Ministry investigation focus on Ushuaia landfill site'),
    -- Patient zero
    (pz_id,        excursion_id, 'attended',      jsonb_build_object('window','2026-03-25..2026-03-31'), 0.85,
     '[PUBLIC] Index couple bird-watching at Ushuaia landfill per local media + investigators'),
    (pz_id,        voyage_id,    'in_voyage',     jsonb_build_object('embarked','2026-04-01'), 0.99,
     '[PUBLIC] WHO DON 600 — index case boarded Ushuaia 2026-04-01'),
    -- Spouse
    (spouse_id,    excursion_id, 'attended',      jsonb_build_object('window','2026-03-25..2026-03-31'), 0.85,
     '[PUBLIC] Index couple bird-watching at Ushuaia landfill'),
    (spouse_id,    voyage_id,    'in_voyage',     jsonb_build_object('embarked','2026-04-01','disembarked','2026-04-24','disembark_port','Saint Helena'), 0.99,
     '[PUBLIC] WHO DON 600 — case 2 disembarked St Helena symptomatic 2026-04-24'),
    -- Person-to-person transmission (the defining feature of ANDV)
    (pz_id,        spouse_id,    'transmitted_to', jsonb_build_object('mode','person-to-person ANDV','timing','aboard or pre-voyage'), 0.70,
     '[PUBLIC] ANDV is the only orthohantavirus with documented P2P; spouse PCR-confirmed shortly after index case died')
) AS rels(src, dst, rel, props, conf, cit)
WHERE src IS NOT NULL AND dst IS NOT NULL
ON CONFLICT (src_id, dst_id, rel_type) DO NOTHING;


-- ----------------------------------------------------------------------------
-- 7) VESSEL_TRACK_POINTS: bootstrap with the known port-call sequence
--    Real-time AIS positions will be inserted by the AISStream.io worker.
-- ----------------------------------------------------------------------------
WITH vessel_ent AS (
    SELECT id FROM entities WHERE entity_type='vessel' AND public_label='MV Hondius'
)
INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, ts::timestamptz, lat, lng, 'port_call',
       '[PUBLIC] Oceanwide itinerary + WHO DON 600 port-call sequence'
FROM vessel_ent v
CROSS JOIN (VALUES
    ('2026-04-01 18:00:00+00', -54.8019, -68.3030),  -- Depart Ushuaia
    ('2026-04-11 12:00:00+00', -32.0000, -10.0000),  -- South Atlantic (index case death; approx position)
    ('2026-04-24 09:00:00+00', -15.9650,  -5.7089),  -- Saint Helena port-call (medevac)
    ('2026-04-26 16:00:00+00', -33.9180,  18.4233),  -- Cape Town medevac terminus
    ('2026-05-10 08:00:00+00',  28.4682, -16.2546)   -- Arrive Tenerife
) AS t(ts, lat, lng)
ON CONFLICT DO NOTHING;

\echo '==> 012 done (ontology graph seeded: vessel, ports, excursion, voyage, index couple, P2P link, 5 track points)'
