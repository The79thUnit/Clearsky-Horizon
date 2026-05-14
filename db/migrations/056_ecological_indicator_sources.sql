-- HORIZON migration 056: Ecological indicator data sources.
--
-- Hantavirus outbreaks are predictable 6-24 months in advance using ecological
-- leading indicators. Two key indicators are implemented:
--
-- 1. NOAA MEI.v2 (Multivariate ENSO Index):
--    El Nino conditions (MEI > 0.5) increase rainfall and vegetation in ANDV/SNV
--    endemic regions of Latin America, driving rodent population surges 12-24 months
--    later. Well-documented correlation with HPS outbreaks in Chile and Argentina.
--    NOAA PSL publishes MEI.v2 monthly. Free, no API key. Very high authority.
--
-- 2. NASA MODIS MOD13A3 NDVI (vegetation anomaly):
--    Elevated NDVI in endemic regions supports larger rodent food supplies. This
--    is the PUUV/HTNV leading indicator for Europe and Asia (mast-year proxy)
--    and the SNV/ANDV leading indicator for the Americas. NASA SERVIR demonstrated
--    operational hantavirus risk mapping using NDVI + ENSO (earthdata.nasa.gov).
--    ORNL MODIS Web Service provides public access without authentication.
--
-- Both sources use the 'ecological-indicator' provenance_type (defined in
-- migration 001 CHECK constraint). Tier 3 reflects these are indirect risk
-- signals, not disease surveillance reports.

\echo '==> HORIZON 056 ecological indicator sources'

-- NOAA Multivariate ENSO Index v2
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility,
                     fetch_interval_sec, enabled, notes)
VALUES (
    'noaa-enso',
    'NOAA PSL — Multivariate ENSO Index v2 (MEI.v2)',
    'https://psl.noaa.gov/enso/mei/',
    3,
    'ecological-indicator',
    'A',
    1,
    86400,  -- daily poll, but data updates monthly
    TRUE,
    'Added 2026-05-14 (migration 056). NOAA Physical Sciences Laboratory '
    'MEI.v2 monthly composite ENSO index. El Nino (MEI > 0.5) drives '
    'vegetation and rodent population surges in ANDV/SNV endemic regions '
    '12-24 months later. Documented correlation with HPS outbreaks in Chile '
    'and Argentina. Free, no auth. NATO A1 (US federal scientific data). '
    'Beat: 06:03 UTC daily.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    fetch_interval_sec = EXCLUDED.fetch_interval_sec,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

-- NASA MODIS MOD13A3 NDVI (via ORNL Web Service)
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility,
                     fetch_interval_sec, enabled, notes)
VALUES (
    'nasa-ndvi',
    'NASA MODIS MOD13A3 — Monthly NDVI Anomaly (5 Endemic Regions)',
    'https://modis.ornl.gov/rst/api/v1/MOD13A3/statistics',
    3,
    'ecological-indicator',
    'A',
    1,
    86400,  -- daily poll, but MODIS data updates monthly
    TRUE,
    'Added 2026-05-14 (migration 056). NASA MODIS Terra MOD13A3 v061 '
    'monthly 1km NDVI via ORNL Web Service (no auth required). '
    'Monitors 5 hantavirus-endemic regions: Patagonia (ANDV), US Four '
    'Corners (SNV), Finland/Scandinavia (PUUV), NE China (HTNV), '
    'Balkans (DOBV). Elevated NDVI predicts rodent population surges '
    '6-18 months before case increases. NASA SERVIR operational risk '
    'mapping demonstrated. NATO A1 (NASA federal remote sensing data). '
    'Beat: 06:23 UTC daily.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    fetch_interval_sec = EXCLUDED.fetch_interval_sec,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

INSERT INTO schema_migrations (version) VALUES ('056_ecological_indicator_sources')
    ON CONFLICT DO NOTHING;

\echo '==> 056 done (NOAA ENSO + NASA NDVI seeded)'
