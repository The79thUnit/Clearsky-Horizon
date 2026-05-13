-- migration 021 — correct MV Hondius vessel route per CNN graphic
--
-- Errors in prior migrations (012, 020) being fixed here:
--
--   1. CAPE TOWN was added to vessel_track_points as if the ship sailed
--      there on 26 April. That is WRONG. Per CNN 2026-05-08 graphic:
--      victim 2 (wife) was MEDEVACED BY AIR from St Helena to Cape Town
--      where she died at Groote Schuur Hospital. The MV Hondius itself
--      sailed St Helena → Ascension Island, not St Helena → Cape Town.
--      The death event entity stays at Cape Town (correct death
--      location); only the polyline waypoint is removed.
--
--   2. At-sea death 1 position (-32, -10) was a rough guess. Correcting
--      to a realistic position on the Ushuaia→Tristan da Cunha leg
--      ~75% of the way (10 days at sea at ~12 knots): (-41.5, -26.3).
--
--   3. At-sea death 3 position (4, -19) was close but slightly off.
--      Tightened to (4.6, -19.4) — actual midpoint of Ascension→Cape
--      Verde leg at 5/9 of the way.
--
--   4. Tenerife → Rotterdam straight line crossed Iberia + France.
--      Adding three intermediate maritime waypoints (off Lisbon, west
--      of Brittany, English Channel approach) so the projected dashed
--      polyline follows the actual ship route through open Atlantic.
--
-- All changes are surgical UPDATEs / DELETEs / INSERTs so the existing
-- entity IDs and relationships are preserved.

BEGIN;

-- --------------------------------------------------------------------
-- 1. Remove Cape Town from the vessel track polyline.
--    The death event entity for victim 2 (wife) STAYS at Cape Town —
--    that's where she physically died after the air medevac.
-- --------------------------------------------------------------------

DELETE FROM vessel_track_points
WHERE vessel_entity_id = (
        SELECT id FROM entities
        WHERE entity_type = 'vessel' AND public_label = 'MV Hondius'
      )
  AND ts::date = '2026-04-26'
  AND ABS(lng - 18.4233) < 0.1
  AND ABS(lat - (-33.918)) < 0.1;

-- --------------------------------------------------------------------
-- 2. Reposition at-sea death 1 (victim 1, 11 April) to a realistic
--    point on the Ushuaia→Tristan da Cunha track.
-- --------------------------------------------------------------------

UPDATE entities
SET properties = properties
  || jsonb_build_object(
       'lat', -41.5,
       'lng', -26.3,
       'note', '~75% of the way Ushuaia→Tristan da Cunha at 12 kt cruise speed'
     )
WHERE entity_type = 'death_event'
  AND public_label LIKE '%victim 1%';

-- Also fix the corresponding at-sea breadcrumb in vessel_track_points
UPDATE vessel_track_points
SET lat = -41.5, lng = -26.3,
    src_citation = src_citation || '; repositioned to realistic on-route point'
WHERE vessel_entity_id = (
        SELECT id FROM entities
        WHERE entity_type = 'vessel' AND public_label = 'MV Hondius'
      )
  AND ts::date = '2026-04-11';

-- --------------------------------------------------------------------
-- 3. Tighten at-sea death 3 (victim 3, 2 May) position to midpoint of
--    Ascension → Cape Verde leg (5/9 of the way, ~5 days of 9-day run).
-- --------------------------------------------------------------------

UPDATE entities
SET properties = properties
  || jsonb_build_object(
       'lat', 4.64,
       'lng', -19.4,
       'note', '~5/9 of the way Ascension→Praia, mid-Atlantic open ocean'
     )
WHERE entity_type = 'death_event'
  AND public_label LIKE '%victim 3%';

-- (No corresponding vessel_track_point for this date in current data —
-- the polyline interpolates between Ascension Apr 27 and Cape Verde
-- May 6 without needing an explicit waypoint at the at-sea death.)

-- --------------------------------------------------------------------
-- 4. Add intermediate maritime waypoints for the Tenerife → Rotterdam
--    projection so the dashed polyline follows the actual ship route
--    (around Iberia, through the English Channel) instead of cutting
--    across the Iberian peninsula and France.
--
--    Inserted with future timestamps so they render on the dashed
--    "projected" segment.
-- --------------------------------------------------------------------

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-05-13 12:00:00+00', 38.50, -10.50, 'port_call',
       'Projected route waypoint — open Atlantic west of Cape da Roca, Portugal'
FROM entities v
WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-05-15 06:00:00+00', 48.20, -6.50, 'port_call',
       'Projected route waypoint — open Atlantic west of Brest, France'
FROM entities v
WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

INSERT INTO vessel_track_points (vessel_entity_id, ts, lat, lng, source, src_citation)
SELECT v.id, '2026-05-16 12:00:00+00', 50.80, 1.40, 'port_call',
       'Projected route waypoint — English Channel approach (Strait of Dover)'
FROM entities v
WHERE v.entity_type = 'vessel' AND v.public_label = 'MV Hondius'
ON CONFLICT DO NOTHING;

COMMIT;
