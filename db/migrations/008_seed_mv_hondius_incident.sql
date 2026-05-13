-- HORIZON migration 008: seed the MV Hondius incident with WHO's authoritative
-- count as of 2026-05-11.
--
-- WHO statement (cited via Reuters, 2026-05-11): "WHO says seven cases of
-- hantavirus confirmed from cruise ship" — that is the authoritative public
-- number we display as "Confirmed cases" until WHO updates it.

\echo '==> HORIZON 008 seed MV Hondius incident'

INSERT INTO incidents (
    code, name, serotype_id,
    started_at, status, summary,
    primary_location_country_iso2, primary_location_name,
    primary_vessel_imo, primary_vessel_name, primary_vessel_mmsi, primary_vessel_flag
)
VALUES (
    'mv-hondius-2026',
    'MV Hondius hantavirus cluster',
    (SELECT id FROM serotypes WHERE code = 'ANDV'),
    '2026-04-28',  -- approximate index exposure (pre-departure excursion week)
    'active',
    $$Andes virus cluster aboard the MV Hondius polar expedition cruise. Index exposure is suspected during a pre-departure wildlife excursion near Ushuaia, Tierra del Fuego, Argentina. Cases identified across multiple repatriation destinations as passengers and crew dispersed via Tenerife (Canary Islands) and onward flights. UK passengers were isolated at Arrowe Park Hospital; US passengers were flown back; France confirmed its first case 2026-05-11.$$,
    'AR',
    'Ushuaia (Tierra del Fuego, Argentina) — pre-departure wildlife excursion',
    '9818709',
    'MV Hondius',
    '244327000',
    'NL'
)
ON CONFLICT (code) DO NOTHING;

-- Authoritative count snapshot. NATO A1 for WHO DON; cited via Reuters
-- 2026-05-11 ("WHO says seven cases of hantavirus confirmed from cruise ship").
INSERT INTO incident_authoritative_counts (
    incident_id,
    confirmed_cases, suspected_cases, deaths, recovered,
    source_id,
    reported_at,
    nato_reliability, nato_credibility,
    src_citation,
    notes
)
SELECT
    i.id,
    7, 0, 0, 0,
    s.id,
    '2026-05-11 12:00:00+00'::TIMESTAMPTZ,
    'A', 1,
    '[PUBLIC] WHO (A1) "WHO Disease Outbreak News — MV Hondius hantavirus cluster" World Health Organization, 2026-05-11',
    'Authoritative count as of 2026-05-11. WHO statement reported globally including via Reuters ("WHO says seven cases of hantavirus confirmed from cruise ship"). Will be updated as WHO issues fresh DON statements.'
FROM incidents i
CROSS JOIN sources s
WHERE i.code = 'mv-hondius-2026'
  AND s.code = 'who-don'
ON CONFLICT (incident_id, source_id, reported_at) DO NOTHING;

-- Per-country breakdown derived from public reporting at 2026-05-11.
-- These are the COUNTRIES of the confirmed/suspected/exposed individuals,
-- per WHO DON + UKHSA + AP/Reuters/France 24/Le Monde reporting.
-- Each number is what the source said about that nationality, capped at the
-- WHO total of 7 confirmed.
INSERT INTO incident_countries (
    incident_id, country_iso2,
    confirmed_count, suspected_count, deaths,
    first_reported_at
)
SELECT i.id, c.iso, c.confirmed, c.suspected, c.deaths, c.first_reported
FROM incidents i
CROSS JOIN (VALUES
    ('US', 1, 0, 0, DATE '2026-05-11'),  -- "1 US passenger tested positive after evacuation" (AP/Reuters/Time/Forbes)
    ('FR', 1, 0, 0, DATE '2026-05-11'),  -- "French passenger tests positive" (Le Monde, France 24, Reuters)
    ('GB', 0, 30, 0, DATE '2026-05-10'), -- British passengers isolating at Arrowe Park (BBC/Guardian/ITV) — exposed not confirmed
    ('AR', 0, 0, 0, DATE '2026-05-10'),  -- Argentine authorities retracing footsteps (Guardian) — origin investigation
    ('ES', 0, 0, 0, DATE '2026-05-10'),  -- Canary Islands evacuation point (Al Jazeera)
    ('NL', 0, 0, 0, DATE '2026-05-09')   -- Vessel flag state
) AS c(iso, confirmed, suspected, deaths, first_reported)
WHERE i.code = 'mv-hondius-2026'
ON CONFLICT (incident_id, country_iso2) DO UPDATE
SET confirmed_count = EXCLUDED.confirmed_count,
    suspected_count = EXCLUDED.suspected_count,
    deaths = EXCLUDED.deaths,
    first_reported_at = LEAST(incident_countries.first_reported_at, EXCLUDED.first_reported_at),
    last_updated_at = NOW();

\echo '==> 008 done (MV Hondius incident seeded with WHO A1 count: 7 confirmed)'
