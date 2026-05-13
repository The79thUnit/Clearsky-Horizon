-- migration 026 — allow source='cruisemapper' on vessel_track_points
--
-- CruiseMapper embeds live vessel JSON in its public HTML pages.
-- Fixes arrive via the poll_cruisemapper Celery task with source
-- 'cruisemapper' so provenance is always clear.

BEGIN;

ALTER TABLE vessel_track_points
DROP CONSTRAINT IF EXISTS vessel_track_points_source_check;

ALTER TABLE vessel_track_points
ADD CONSTRAINT vessel_track_points_source_check CHECK (
    source IN (
        'aisstream',
        'marinetraffic',
        'myshiptracking',
        'cruisemapper',
        'port_call',
        'manual'
    )
);

COMMIT;
