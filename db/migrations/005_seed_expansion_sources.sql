-- HORIZON migration 005: source expansion wave.
--
-- Adds 20 new connectors taking the registry from 16 -> 36 active sources.
-- Each row references a connector in worker/horizon_worker/connectors/.
-- All URLs verified resolving 2026-05-11. NATO scores reflect the source's
-- known authority + recency at qualification time.
--
-- Categories:
--   Tier 1 (official authority):     ukhsa, phac, rki, phs, hpsc, who-afro
--   Tier 2 (aggregator):             cidrap-news, ecdc-cdtr
--   Tier 3 (news + social):          outbreak-news-today
--   Tier 4 (peer-reviewed):          cdc-eid, cdc-eid-ahead, eurosurveillance,
--                                    lancet-id, viruses-mdpi, jvi-asm,
--                                    nature-news, science-news, pubmed
--   Tier 5 (sequence record):        -- (none in this wave; NCBI Datasets pending)
--   Tier 6 (ecological):             inaturalist, gbif

\echo '==> HORIZON 005 source expansion: 20 new connectors'

INSERT INTO sources
    (code, name, url, tier, provenance_type, nato_reliability, nato_credibility,
     fetch_interval_sec, enabled, notes)
VALUES
-- ============================================================================
-- Tier 1: official national / regional public-health authorities
-- ============================================================================
('ukhsa',              'UK Health Security Agency news',
                       'https://www.gov.uk/government/organisations/uk-health-security-agency.atom',
                       1, 'official-authority', 'A', 1, 3600, TRUE,
                       'GOV.UK ATOM feed for UKHSA. Successor to PHE; covers UK zoonotic + outbreak surveillance.'),
('phac',               'Public Health Agency of Canada news',
                       'https://www.canada.ca/en/news.atom?dept=publichealthagencyofcanada',
                       1, 'official-authority', 'A', 1, 3600, TRUE,
                       'Canada.ca ATOM filtered to PHAC. Covers Canadian HPS surveillance (SNV endemic in western provinces).'),
('rki',                'Robert Koch Institute Epidemiologisches Bulletin',
                       'https://www.rki.de/SiteGlobals/Functions/RSSFeed/RSSGenerator/RSS_EpidBull.xml',
                       1, 'official-authority', 'A', 1, 21600, TRUE,
                       'Germany federal disease control + surveillance. Weekly bulletin; PUUV dominant in southern Germany.'),
('phs',                'Public Health Scotland news',
                       'https://publichealthscotland.scot/all-news/rss.xml',
                       1, 'official-authority', 'A', 1, 3600, TRUE,
                       'Scotland national public-health body. RSS for all news items.'),
('hpsc',               'Health Protection Surveillance Centre (Ireland)',
                       'https://www.hpsc.ie/news/RSS/',
                       1, 'official-authority', 'A', 1, 3600, TRUE,
                       'HSE national surveillance centre, Ireland. Covers Irish notifiable disease alerts.'),
('who-afro',           'WHO Regional Office for Africa news',
                       'https://www.afro.who.int/rss.xml',
                       1, 'official-authority', 'A', 2, 3600, TRUE,
                       'WHO AFRO regional bulletin. Hantavirus rare in region but kept for completeness on zoonotic surveillance.'),

-- ============================================================================
-- Tier 2: outbreak intelligence aggregators (separate from existing healthmap / gdelt / google-news)
-- ============================================================================
('cidrap-news',        'CIDRAP News (University of Minnesota)',
                       'https://www.cidrap.umn.edu/news-perspective/feed',
                       2, 'aggregator', 'B', 2, 1800, TRUE,
                       'Editorial outbreak coverage. Gold standard for English-language US/global public-health journalism.'),
('ecdc-cdtr',          'ECDC Communicable Disease Threats Report',
                       'https://www.ecdc.europa.eu/en/publications-data/rss.xml',
                       2, 'aggregator', 'A', 2, 21600, TRUE,
                       'ECDC weekly multi-disease threat report. Distinct from ecdc-tessy (surveillance atlas).'),

-- ============================================================================
-- Tier 3: news + editorial outbreak coverage
-- ============================================================================
('outbreak-news-today', 'Outbreak News Today',
                       'https://outbreaknewstoday.com/feed/',
                       3, 'media-unconfirmed', 'C', 3, 1800, TRUE,
                       'Independent outbreak news, edited by Robert Herriman. Analyst review mandatory before any high-confidence write.'),

-- ============================================================================
-- Tier 4: peer-reviewed literature + ahead-of-print
-- ============================================================================
('cdc-eid',            'CDC Emerging Infectious Diseases journal',
                       'https://wwwnc.cdc.gov/eid/rss/current.xml',
                       4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                       'CDC peer-reviewed journal of record for emerging infectious diseases. Monthly issue feed.'),
('cdc-eid-ahead',      'CDC EID Ahead-of-Print',
                       'https://wwwnc.cdc.gov/eid/rss/upcoming.xml',
                       4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                       'CDC EID upcoming articles. Earlier signal than the monthly issue feed.'),
('eurosurveillance',   'Eurosurveillance (ECDC peer-reviewed weekly)',
                       'https://www.eurosurveillance.org/action/showFeed?type=etoc&feed=rss&jc=esw',
                       4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                       'ECDC peer-reviewed weekly journal of European communicable disease control.'),
('lancet-id',          'The Lancet Infectious Diseases',
                       'https://www.thelancet.com/rssfeed/laninf_current.xml',
                       4, 'peer-reviewed', 'A', 1, 43200, TRUE,
                       'Tier-1 peer-reviewed infectious disease journal. Current-issue feed.'),
('viruses-mdpi',       'Viruses (MDPI)',
                       'https://www.mdpi.com/rss/journal/viruses',
                       4, 'peer-reviewed', 'B', 2, 43200, TRUE,
                       'Open-access peer-reviewed virology journal. MDPI editorial standards looser than top-tier publishers.'),
('jvi-asm',            'Journal of Virology (ASM)',
                       'https://journals.asm.org/action/showFeed?type=etoc&feed=rss&jc=jvi',
                       4, 'peer-reviewed', 'A', 1, 43200, TRUE,
                       'American Society for Microbiology flagship virology journal. Peer-reviewed.'),
('nature-news',        'Nature.com news',
                       'https://www.nature.com/nature.rss',
                       4, 'peer-reviewed', 'A', 2, 21600, TRUE,
                       'Nature general news feed. Hantavirus mentions rare but high-quality (typically major outbreaks or research breakthroughs).'),
('science-news',       'Science magazine news (AAAS)',
                       'https://www.science.org/rss/news_current.xml',
                       4, 'peer-reviewed', 'A', 2, 21600, TRUE,
                       'AAAS Science news feed. Same role as Nature feed.'),
('pubmed',             'PubMed E-utilities',
                       'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
                       4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                       'NCBI biomedical literature index. Two-step esearch + esummary for MeSH-tagged hantavirus papers, reverse-date sort.'),

-- ============================================================================
-- Tier 6: ecological / reservoir-host observations
-- ============================================================================
('inaturalist',        'iNaturalist (reservoir-host observations)',
                       'https://api.inaturalist.org/v1/observations',
                       6, 'ecological-indicator', 'C', 3, 43200, TRUE,
                       'Citizen-science research-grade observations of reservoir species: Peromyscus maniculatus (SNV), Oligoryzomys longicaudatus (ANDV), Apodemus agrarius (HTNV), Myodes glareolus (PUUV), Rattus norvegicus (SEOV).'),
('gbif',               'GBIF (Global Biodiversity Information Facility)',
                       'https://api.gbif.org/v1/occurrence/search',
                       6, 'ecological-indicator', 'B', 2, 43200, TRUE,
                       'Museum vouchers + academic surveys of hantavirus reservoir species. Higher pedigree than iNaturalist citizen science.')
ON CONFLICT (code) DO NOTHING;

\echo '==> 005 done (20 new sources, all enabled)'
