-- migration 023 — allow source='myshiptracking' on vessel_track_points
--
-- We now scrape myshiptracking.com's public vessel pages as a free
-- complement to aisstream (gappy mid-ocean) and Kpler (subscription
-- pending). Each scraped fix lands with source='myshiptracking' so we
-- never confuse it with real first-party AIS API data.

BEGIN;

ALTER TABLE vessel_track_points
DROP CONSTRAINT IF EXISTS vessel_track_points_source_check;

ALTER TABLE vessel_track_points
ADD CONSTRAINT vessel_track_points_source_check CHECK (
    source IN (
        'aisstream',
        'marinetraffic',
        'myshiptracking',
        'port_call',
        'manual'
    )
);

COMMIT;
