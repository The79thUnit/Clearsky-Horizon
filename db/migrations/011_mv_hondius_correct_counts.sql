-- HORIZON migration 011: correct MV Hondius cluster counts.
--
-- Per WHO Disease Outbreak News 2026-DON600 + ECDC surveillance update
-- 2026-05-11, the breakdown is:
--   9 total cases
--   7 lab-confirmed (PCR positive for Andes hantavirus)
--   2 probable / suspected (incl. index Dutch man who died before sampling)
--   3 deaths
--
-- Also corrects:
--   - started_at: index case symptom onset was 2026-04-06 (not 2026-04-28)
--   - origin narrative: bird-watching at landfill site near Ushuaia, not a
--     generic "wildlife excursion"
--   - per-country split: Netherlands attributed for the index couple

\echo '==> HORIZON 011 correct MV Hondius counts (9 total / 7 conf / 2 prob / 3 deaths)'

UPDATE incidents
SET
    started_at = '2026-04-06',  -- index case first symptoms (fever / headache / diarrhea)
    summary = $$Andes virus (ANDV) cluster aboard the MV Hondius polar expedition cruise. The probable index case is a 70-year-old Dutch man who boarded in Ushuaia on 2026-04-01, developed fever, headache and diarrhea on 2026-04-06, and died on board 2026-04-11. His 69-year-old spouse disembarked at Saint Helena on 2026-04-24 and died in South Africa on 2026-04-26; PCR confirmed Andes hantavirus on her samples and is the laboratory confirmation that anchors the cluster. Pre-boarding exposure is suspected during bird-watching at a landfill site near Ushuaia (Tierra del Fuego), where the long-tailed pygmy rice rat (Oligoryzomys longicaudatus) — the natural ANDV reservoir — is present. Andes virus is the only orthohantavirus with documented person-to-person transmission, which explains onboard spread to crew and other passengers despite no rodents on the ship. Incubation 1 to 8 weeks; the cruise was already at sea before symptoms appeared. As of 2026-05-11 (WHO DON 600 / ECDC update): 9 total cases, 7 lab-confirmed, 2 probable, 3 deaths.$$,
    primary_location_name = 'Ushuaia (Tierra del Fuego, Argentina) — bird-watching at landfill site, pre-boarding exposure',
    updated_at = NOW()
WHERE code = 'mv-hondius-2026';

-- Update WHO authoritative count with the corrected numbers + add ECDC.
UPDATE incident_authoritative_counts
SET confirmed_cases = 7,
    suspected_cases = 2,
    deaths = 3,
    recovered = 0,
    src_citation = '[PUBLIC] WHO (A1) "Disease Outbreak News 2026-DON600: Andes hantavirus — MV Hondius cluster" World Health Organization, 2026-05-11',
    notes = 'WHO DON 600 corrected count: 9 total (7 lab-confirmed PCR positive for Andes hantavirus + 2 probable including the deceased Dutch index case). 3 deaths recorded among the total: index case (70M NL) died on board 2026-04-11; spouse (69F NL) died in South Africa 2026-04-26; one additional fatality not yet publicly attributed.'
WHERE incident_id = (SELECT id FROM incidents WHERE code = 'mv-hondius-2026')
  AND source_id = (SELECT id FROM sources WHERE code = 'who-don');

-- Add ECDC as a second authoritative source.
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
    7, 2, 3, 0,
    s.id,
    '2026-05-11 14:00:00+00'::TIMESTAMPTZ,
    'A', 2,
    '[PUBLIC] ECDC (A2) "Andes hantavirus outbreak — surveillance and updates" European Centre for Disease Prevention and Control, 2026-05-11',
    'ECDC surveillance update corroborating WHO DON 600. ECDC link: https://www.ecdc.europa.eu/en/infectious-disease-topics/hantavirus-infection/surveillance-and-updates/andes-hantavirus-outbreak'
FROM incidents i
CROSS JOIN sources s
WHERE i.code = 'mv-hondius-2026'
  AND s.code = 'ecdc-tessy'
ON CONFLICT (incident_id, source_id, reported_at) DO NOTHING;

-- Re-distribute per-country numbers to reflect known attributions.
-- The Dutch couple = 2 confirmed (after PCR confirmation on the wife;
-- the husband is probable, post-mortem). For surveillance attribution we
-- count both as NL nationality. Country-of-death (ZA for the wife) is
-- noted separately in narratives, not in this per-nationality table.
DELETE FROM incident_countries
WHERE incident_id = (SELECT id FROM incidents WHERE code = 'mv-hondius-2026');

INSERT INTO incident_countries (
    incident_id, country_iso2,
    confirmed_count, suspected_count, deaths, first_reported_at
)
SELECT i.id, c.iso, c.conf, c.susp, c.deaths, c.first_reported
FROM incidents i
CROSS JOIN (VALUES
    ('NL', 1, 1, 2, DATE '2026-04-06'),  -- index case (probable, deceased) + spouse (confirmed, deceased)
    ('US', 1, 0, 0, DATE '2026-05-11'),  -- 1 confirmed (Reuters/AP)
    ('FR', 1, 0, 0, DATE '2026-05-11'),  -- 1 confirmed (Le Monde / France 24)
    ('GB', 0, 0, 0, DATE '2026-05-10'),  -- ~30 exposed under isolation at Arrowe Park (suspected unconfirmed contacts, not cases)
    ('AR', 0, 0, 0, DATE '2026-03-25'),  -- exposure-origin investigation (no Argentine cases attributed)
    ('ES', 0, 0, 0, DATE '2026-05-10'),  -- evacuation point (Tenerife) only
    ('ZA', 0, 0, 1, DATE '2026-04-26'),  -- spouse died in ZA (Dutch national; ZA = country of death)
    ('SH', 0, 0, 0, DATE '2026-04-24')   -- St Helena: spouse disembarked here ill (UK overseas territory)
) AS c(iso, conf, susp, deaths, first_reported)
WHERE i.code = 'mv-hondius-2026';

\echo '==> 011 done (WHO+ECDC reconciled: 7 conf / 2 prob / 3 deaths)'
