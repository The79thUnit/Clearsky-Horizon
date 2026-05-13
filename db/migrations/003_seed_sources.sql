-- HORIZON migration 003: seed source registry.
-- Phase 1: only ProMED enabled. Other tier-1/tier-2 sources seeded for visibility
-- in the source quality dashboard, enabled=FALSE until their connectors ship.

\echo '==> HORIZON 003 seed sources'

INSERT INTO sources
    (code, name, url, tier, provenance_type, nato_reliability, nato_credibility,
     fetch_interval_sec, enabled, notes)
VALUES
-- Tier 1: official health authorities
-- URLs verified resolving 2026-05-11. Where the RSS endpoint has moved or
-- disappeared, we point to the canonical landing page and ingest by scraping
-- the latest item list.
('who-don',     'WHO Disease Outbreak News',
                'https://www.who.int/emergencies/disease-outbreak-news',
                1, 'official-authority', 'A', 1, 3600, FALSE,
                'Authoritative outbreak alerts from WHO. Phase 2 connector scrapes the listing HTML; WHO no longer publishes a public DON RSS.'),
('cdc-han',     'CDC Health Alert Network',
                'https://www.cdc.gov/han/index.html',
                1, 'official-authority', 'A', 1, 3600, FALSE,
                'HAN alerts. HAN00528 covers the 2026 MV Hondius cluster.'),
('cdc-mmwr',    'CDC MMWR (Morbidity and Mortality Weekly Report)',
                'https://www.cdc.gov/mmwr/rss/rss.html',
                1, 'official-authority', 'A', 1, 21600, FALSE,
                'Weekly US morbidity reports. RSS verified resolving 2026-05-11.'),
('ecdc-tessy',  'ECDC Surveillance Atlas of Infectious Diseases',
                'https://atlas.ecdc.europa.eu/public/index.aspx',
                1, 'official-authority', 'A', 1, 86400, FALSE,
                'European Surveillance System (TESSy). Phase 2 connector requires JavaScript-rendered ingestion; access from non-EU IPs is intermittent.'),
('paho-alerts', 'PAHO Epidemiological Alerts',
                'https://www.paho.org/en/topics/hantavirus',
                1, 'official-authority', 'A', 1, 21600, FALSE,
                'Americas region alerts. Dec 2025 alert + May 2026 cruise response active.'),
('nmh-data',    'New Mexico Department of Health HPS',
                'https://www.nmhealth.org/about/erd/ideb/zdp/hps/',
                1, 'official-authority', 'A', 2, 86400, FALSE,
                'US Four Corners endemic zone. HPS by county data tables at /data/view/infectious/890/.'),

-- Tier 2: outbreak intelligence aggregators
-- ProMED note: as of 2026, ProMED has documented infrastructure instability
-- (Science, 2025) and the public RSS endpoint is intermittently 404. Phase 2
-- connector parses the homepage post list as a fallback when RSS is down.
('promed-rss',  'ProMED-mail',
                'https://promedmail.org/',
                2, 'aggregator', 'B', 2, 900, TRUE,
                'Expert-curated 24/7 outbreak alerts. PRIMARY Phase 1 source. ISID-operated.'),
('healthmap',   'HealthMap (Boston Children Hospital)',
                'https://www.healthmap.org/en/',
                2, 'aggregator', 'B', 2, 1800, FALSE,
                'Automated aggregation of news + ProMED + WHO. Boston Children Hospital project.'),

-- Tier 3: news + social
('gdelt',       'GDELT 2.0 Global Knowledge Graph',
                'https://api.gdeltproject.org/api/v2/doc/doc',
                3, 'aggregator', 'C', 3, 900, FALSE,
                'Google-funded global news monitoring. 100+ countries, 65 languages, 15-min cadence.'),

-- Tier 4: academic + research
('pubmed',      'PubMed E-utilities',
                'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
                4, 'peer-reviewed', 'A', 1, 86400, FALSE,
                'NCBI peer-reviewed literature. Search filtered to hantavirus + recent date.'),
('biorxiv',     'bioRxiv preprint server',
                'https://api.biorxiv.org/details/biorxiv/',
                4, 'peer-reviewed', 'B', 2, 86400, FALSE,
                'Preprint server. Lower bar than PubMed (not yet peer-reviewed). NATO B2.');

\echo '==> 003 done (11 sources seeded, ProMED enabled, others gated until connectors ship)'
