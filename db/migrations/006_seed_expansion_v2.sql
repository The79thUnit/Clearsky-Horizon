-- HORIZON migration 006: Wave Z+ source expansion.
--
-- Adds 16 new connectors taking the registry from 36 -> 52 active sources.
-- All idempotent via ON CONFLICT (code) DO NOTHING.
--
-- Categories:
--   Tier 1 (national / regional authority):
--     who-euro, who-emro, who-searo, who-wpro,
--     china-cdc, japan-niid, australia-health, nz-moh,
--     argentina-msal, chile-deis, brazil-ms
--   Tier 4 (peer-reviewed): plos-pathogens, plos-ntds, mbio, elife
--   Tier 5/6 (sequence + ecological / animal health): wahis

\echo '==> HORIZON 006 source expansion v2: 16 new connectors'

INSERT INTO sources
    (code, name, url, tier, provenance_type, nato_reliability, nato_credibility,
     fetch_interval_sec, enabled, notes)
VALUES
-- WHO regional offices (separate from the global DON feed)
('who-euro',          'WHO Regional Office for Europe',
                      'https://www.who.int/europe/rss-feeds/news',
                      1, 'official-authority', 'A', 2, 3600, TRUE,
                      'WHO EURO regional bulletin. Europe + Russia + Central Asia + Israel coverage.'),
('who-emro',          'WHO Regional Office for the Eastern Mediterranean',
                      'https://www.emro.who.int/rss-feeds/whoemro-rss.xml',
                      1, 'official-authority', 'A', 2, 3600, TRUE,
                      'WHO EMRO regional bulletin. Hantavirus uncommon in region; kept for zoonotic completeness.'),
('who-searo',         'WHO Regional Office for South-East Asia',
                      'https://www.who.int/southeastasia/rss-feeds/news',
                      1, 'official-authority', 'A', 2, 3600, TRUE,
                      'WHO SEARO regional bulletin. India + Indonesia + Thailand + Myanmar.'),
('who-wpro',          'WHO Regional Office for the Western Pacific',
                      'https://www.who.int/westernpacific/rss-feeds/news',
                      1, 'official-authority', 'A', 2, 3600, TRUE,
                      'WHO WPRO regional bulletin. China + Korea + Japan; Hantaan-virus heartland.'),

-- Asia-Pacific national authorities
('china-cdc',         'China CDC Weekly',
                      'https://weekly.chinacdc.cn/rss/Article.htm',
                      1, 'official-authority', 'A', 1, 21600, TRUE,
                      'China CDC peer-reviewed weekly bulletin. Global HFRS heartland; HTNV + SEOV dominant.'),
('japan-niid',        'Japan NIID Infectious Disease Weekly Report',
                      'https://www.niid.go.jp/niid/en/rss/whatsnew-en.xml',
                      1, 'official-authority', 'A', 1, 21600, TRUE,
                      'Japan National Institute of Infectious Diseases. IDWR + outbreak alerts.'),
('australia-health',  'Australian Government Department of Health',
                      'https://www.health.gov.au/news/rss.xml',
                      1, 'official-authority', 'A', 1, 3600, TRUE,
                      'Australian Department of Health news + NNDSS surveillance updates.'),
('nz-moh',            'New Zealand Ministry of Health (Manatū Hauora)',
                      'https://www.health.govt.nz/news-media/rss.xml',
                      1, 'official-authority', 'A', 1, 3600, TRUE,
                      'NZ Ministry of Health news. Imported-case surveillance for HPS/HFRS.'),

-- Latin America (Andes virus heartland)
('argentina-msal',    'Argentina Ministerio de Salud',
                      'https://www.argentina.gob.ar/salud/noticias.xml',
                      1, 'official-authority', 'A', 1, 3600, TRUE,
                      'Global ANDV epicentre. Boletín Integrado de Vigilancia weekly. Spanish keyword filter applied.'),
('chile-deis',        'Chile Departamento de Epidemiología (MINSAL)',
                      'https://www.minsal.cl/feed/',
                      1, 'official-authority', 'A', 1, 3600, TRUE,
                      'Chile MoH. Significant ANDV activity in Aysén + Los Lagos. Spanish filter.'),
('brazil-ms',         'Brazil Ministério da Saúde',
                      'https://www.gov.br/saude/pt-br/assuntos/noticias/RSS',
                      1, 'official-authority', 'A', 1, 3600, TRUE,
                      'Brazil MoH. HPS via Araraquara / Juquitiba / Laguna Negra. Portuguese filter.'),

-- Tier 4: more peer-reviewed
('plos-pathogens',    'PLOS Pathogens',
                      'https://journals.plos.org/plospathogens/feed/atom',
                      4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                      'Open-access peer-reviewed pathogen biology journal.'),
('plos-ntds',         'PLOS Neglected Tropical Diseases',
                      'https://journals.plos.org/plosntds/feed/atom',
                      4, 'peer-reviewed', 'A', 1, 21600, TRUE,
                      'Open-access peer-reviewed NTD journal. Outbreak coverage in low-resource settings.'),
('mbio',              'mBio (ASM)',
                      'https://journals.asm.org/action/showFeed?type=etoc&feed=rss&jc=mbio',
                      4, 'peer-reviewed', 'A', 1, 43200, TRUE,
                      'American Society for Microbiology open-access journal.'),
('elife',             'eLife',
                      'https://elifesciences.org/rss/recent.xml',
                      4, 'peer-reviewed', 'A', 1, 43200, TRUE,
                      'Open-access peer-reviewed life-sciences journal.'),

-- Animal health (rodent reservoir mortality + species jumps)
('wahis',             'WOAH WAHIS (animal health events)',
                      'https://wahis.woah.org/rss/list/EVENT',
                      5, 'sequence-record', 'A', 1, 21600, TRUE,
                      'World Organisation for Animal Health (ex-OIE). Rodent reservoir die-offs surface here first.')
ON CONFLICT (code) DO NOTHING;

\echo '==> 006 done (16 new sources upserted, all enabled)'
