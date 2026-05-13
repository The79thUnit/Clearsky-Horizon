-- HORIZON migration 004: seed the remaining 15 sources to match the 16 Phase 2
-- connectors. Each row references a connector in worker/horizon_worker/connectors/.
--
-- All NATO scores reflect the source's known authority + recency.
-- All `enabled = TRUE` because every source has a built connector after Phase 2.

\echo '==> HORIZON 004 seed remaining sources'

INSERT INTO sources
    (code, name, url, tier, provenance_type, nato_reliability, nato_credibility,
     fetch_interval_sec, enabled, notes)
VALUES
-- Tier 2: outbreak intel + news aggregators
('google-news',  'Google News (hantavirus query)',
                 'https://news.google.com/rss/search?q=hantavirus',
                 3, 'aggregator', 'C', 3, 900, TRUE,
                 'Real-time global news. Mixed quality; analyst review mandatory for high pipeline_confidence.'),
('gdelt',        'GDELT 2.0 Global Knowledge Graph',
                 'https://api.gdeltproject.org/api/v2/doc/doc',
                 3, 'aggregator', 'C', 2, 900, TRUE,
                 'Google-funded multilingual news monitoring. 65 languages. 15-min cadence.'),
('healthmap',    'HealthMap (Boston Children Hospital)',
                 'https://www.healthmap.org/getAlerts.php',
                 2, 'aggregator', 'B', 2, 1800, TRUE,
                 'Automated aggregation of news + ProMED + WHO. Boston Children Hospital project.'),
('reddit',       'Reddit (hantavirus search)',
                 'https://www.reddit.com/search.json',
                 3, 'social-rumour', 'E', 4, 1800, TRUE,
                 'Public Reddit search. NATO E4 (low reliability). Surfaces social signal; analyst review mandatory.'),

-- Tier 4: academic + research
('arxiv',        'arXiv preprint server (q-bio)',
                 'http://export.arxiv.org/api/query',
                 4, 'peer-reviewed', 'B', 2, 43200, TRUE,
                 'Preprint server, mainly q-bio. Atom feed. 12-hour cadence.'),
('medrxiv',      'medRxiv preprint server',
                 'https://api.biorxiv.org/details/medrxiv/30d/0/json',
                 4, 'peer-reviewed', 'B', 2, 21600, TRUE,
                 'Medical preprints. JSON API. 6-hour cadence.'),
('europe-pmc',   'Europe PMC REST API',
                 'https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                 4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                 'EBI peer-reviewed life-sciences literature. NATO A1 for peer-reviewed core results.'),
('crossref',     'Crossref Works API',
                 'https://api.crossref.org/works',
                 4, 'peer-reviewed', 'B', 1, 43200, TRUE,
                 'DOI registry. Metadata only; no abstracts unless publisher deposits them.')
ON CONFLICT (code) DO NOTHING;

-- Re-enable the Tier-1 + Tier-2 sources seeded in migration 003 (they were
-- disabled until their connectors shipped; now they have connectors). Includes
-- the rows already in 003 even if also re-asserted above via ON CONFLICT.
UPDATE sources SET enabled = TRUE WHERE code IN (
    'who-don', 'cdc-han', 'cdc-mmwr', 'ecdc-tessy', 'paho-alerts',
    'nmh-data', 'promed-rss', 'healthmap', 'gdelt', 'biorxiv', 'pubmed'
);

\echo '==> 004 done (sources upserted, gated sources enabled)'
