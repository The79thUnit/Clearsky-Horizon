-- migration 051 — European coverage expansion: SPF France + Sweden FHM + Norway FHI.
--
-- Closes three significant European gaps in the source registry:
--
-- SANTÉ PUBLIQUE FRANCE (spf-france):
--   URL: https://www.santepubliquefrance.fr/rss/news/1008
--   Confirmed 200, RSS 2.0, 30 items, 2026-05-13. Dublin Core; some
--   pubDate fields empty (feedparser falls back to updated_parsed → None).
--   France is involved via two routes:
--     1. MV Hondius ANDV cruise-ship cluster: France cluster at 43 cases
--        (2026-05-13 production DB) -- SPF is the coordinating authority.
--     2. PUUV endemic in NE France (Ardennes, Champagne-Ardenne) with
--        annual nephropathia epidemica reports.
--   NATO A2. Tier 1. Beat: hourly minute=9 (former who-emro slot).
--
-- FOLKHÄLSOMYNDIGHETEN (sweden-fhm):
--   URL: https://www.folkhalsomyndigheten.se/nyheter-och-press/nyhetsarkiv/
--        ?topic=smittskydd-och-sjukdomar&syndication=rss
--   Confirmed 200, RSS 2.0, 21 items, 2026-05-13. Infectious disease
--   topic filter applied at source. Sweden has one of the highest per-capita
--   PUUV (Puumala virus) incidence rates in Europe; endemic in Norrland,
--   Ångermanland, Västernorrland, Jämtland, Norrbotten. "Sorkfeber" is the
--   Swedish term for the disease. NATO A2. Tier 1.
--   Beat: hourly minute=14 (former who-searo slot).
--
-- FOLKEHELSEINSTITUTTET (norway-fhi):
--   URL: https://www.fhi.no/rss/nyheter/
--   Confirmed 200, RSS 2.0, 20 items, 2026-05-13. General FHI news feed.
--   Norway has documented PUUV cases in Innlandet (Hedmark/Oppland).
--   Lower burden than Sweden/Finland but FHI is authoritative for NO
--   hantavirus data including Seoul virus risk from imported rodents.
--   NATO A2. Tier 1. Beat: hourly minute=33.

BEGIN;

-- Santé publique France — general public health news RSS
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'spf-france',
    'Santé publique France — actualités santé publique RSS',
    'https://www.santepubliquefrance.fr/rss/news/1008',
    1,
    'official-authority',
    'A',
    2,
    TRUE,
    'Added 2026-05-13 (migration 051). France has 43-case MV Hondius ANDV '
    'cluster (2026-05-13 production data); SPF is the coordinating authority. '
    'Also PUUV endemic in NE France (Ardennes, Champagne-Ardenne). '
    'RSS 2.0, 30 items on add date. pubDate may be empty (feedparser falls '
    'back to updated_parsed → None; pipeline stores NULL reported_date). '
    'Beat: hourly minute=9 (former who-emro slot, freed by migration 049).'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

-- Folkhälsomyndigheten — Swedish Public Health Agency (infectious disease RSS)
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'sweden-fhm',
    'Folkhälsomyndigheten — Swedish Public Health Agency (smittskydd RSS)',
    'https://www.folkhalsomyndigheten.se/nyheter-och-press/nyhetsarkiv/?topic=smittskydd-och-sjukdomar&syndication=rss',
    1,
    'official-authority',
    'A',
    2,
    TRUE,
    'Added 2026-05-13 (migration 051). Sweden has one of the highest per-capita '
    'PUUV (Puumala virus) incidence rates in Europe. Significant annual '
    '"sorkfeber" (nephropathia epidemica) cycles in Norrland, Ångermanland, '
    'Västernorrland, Jämtland, Norrbotten, Västerbotten. RSS 2.0, topic-filtered '
    'to smittskydd-och-sjukdomar (communicable disease), 21 items on add date. '
    'Swedish language. Beat: hourly minute=14 (former who-searo slot).'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

-- Folkehelseinstituttet — Norwegian Institute of Public Health (news RSS)
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'norway-fhi',
    'Folkehelseinstituttet — Norwegian Institute of Public Health (nyheter RSS)',
    'https://www.fhi.no/rss/nyheter/',
    1,
    'official-authority',
    'A',
    2,
    TRUE,
    'Added 2026-05-13 (migration 051). Norway has documented PUUV cases in '
    'Innlandet (Hedmark, Oppland). FHI is authoritative for NO hantavirus data '
    'including Seoul virus risk from imported rodents. RSS 2.0, 20 items on add '
    'date. Norwegian language (bokmål). '
    'Beat: hourly minute=33.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

COMMIT;
