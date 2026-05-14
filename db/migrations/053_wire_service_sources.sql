-- migration 053 — Wire service + major broadcaster sources.
--
-- Closes the news cross-reference gap identified 2026-05-14.
-- Previous coverage relied on Google News (broad query, C3) and CIDRAP
-- for news-layer corroboration. Wire services move within hours of an
-- outbreak event; official agency bulletins (WHO, CDC) follow days later.
-- Adding wire feeds closes the lag and provides independent corroboration
-- required for pipeline_confidence corroboration_boost (+0.02 per source).
--
-- Sources added:
--
-- BBC HEALTH (bbc-health):
--   URL: https://feeds.bbci.co.uk/news/health/rss.xml
--   Confirmed 200, RSS 2.0, public feed. Established broadcaster with
--   editorial fact-checking. Strong on UK/Europe hantavirus (PUUV, SEOV).
--   MV Hondius cluster already covered by BBC Science. NATO B2. Tier 2.
--   Beat: every 30 min (news cadence, same as HealthMap).
--
-- REUTERS HEALTH (reuters-health):
--   URL: Google News RSS filtered to site:reuters.com
--   Reuters discontinued direct topic RSS ~2020. Google News source-filter
--   is the standard aggregator route; semantically equivalent.
--   First wire to break WHO/CDC embargo releases. NATO B2. Tier 2.
--   Beat: every 30 min.
--
-- ASSOCIATED PRESS (ap-news):
--   URL: Google News RSS filtered to site:apnews.com
--   AP has no public topic RSS. Member-funded, non-profit, strong correction
--   policy. First to break US domestic CDC/NIH outbreak announcements.
--   NATO B2. Tier 2. Beat: every 30 min.
--
-- AGENCE FRANCE-PRESSE (afp-wire):
--   URL: Google News RSS filtered to site:afp.com
--   No public RSS. AFP Buenos Aires and Santiago bureaus critical for
--   ANDV Southern Cone coverage ahead of Anglophone wires. NATO B2. Tier 2.
--   Beat: every 30 min.
--
-- EFE WIRE (efe-wire):
--   URL: Google News RSS filtered to site:efe.com (Latin American Spanish)
--   World's largest Spanish-language agency. Primary wire for Argentina,
--   Chile, Peru, Bolivia on hantavirus events. Credibility 3 (not 2)
--   because Spanish text requires translation before analyst review.
--   NATO B3. Tier 2. Beat: every 30 min.
--
-- MERCOPRESS (mercopress):
--   URL: https://en.mercopress.com/rss
--   English-language Southern Cone wire. Covers Patagonian hantavirus
--   outbreaks (Neuquén, Río Negro, Chilean Aysén) ahead of larger wires.
--   NATO C3. Tier 3. Beat: every hour.

BEGIN;

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'bbc-health',
    'BBC News — Health',
    'https://feeds.bbci.co.uk/news/health/rss.xml',
    2,
    'media-confirmed',
    'B',
    2,
    TRUE,
    'Added 2026-05-14 (migration 053). Established broadcaster, fact-checked '
    'editorial standards. Direct public RSS 2.0. Strong PUUV/SEOV/ANDV coverage '
    'for UK and European outbreaks. MV Hondius cluster already in BBC Science '
    'coverage. Beat: every 30 min.'
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'reuters-health',
    'Reuters — hantavirus (via Google News)',
    'https://news.google.com/rss/search?q=hantavirus+OR+%22Andes+virus%22+site:reuters.com&hl=en-US&gl=US&ceid=US:en',
    2,
    'media-confirmed',
    'B',
    2,
    TRUE,
    'Added 2026-05-14 (migration 053). Major global wire service. Reuters '
    'discontinued direct topic RSS ~2020; Google News source-filter used. '
    'First wire to break WHO/CDC embargo releases. Beat: every 30 min.'
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'ap-news',
    'Associated Press — hantavirus (via Google News)',
    'https://news.google.com/rss/search?q=hantavirus+OR+%22Andes+virus%22+site:apnews.com&hl=en-US&gl=US&ceid=US:en',
    2,
    'media-confirmed',
    'B',
    2,
    TRUE,
    'Added 2026-05-14 (migration 053). Member-funded non-profit wire. No public '
    'topic RSS; Google News source-filter used. Strong US domestic CDC/NIH '
    'outbreak coverage. Beat: every 30 min.'
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'afp-wire',
    'Agence France-Presse — hantavirus (via Google News)',
    'https://news.google.com/rss/search?q=hantavirus+OR+%22virus+Andes%22+site:afp.com&hl=en-US&gl=US&ceid=US:en',
    2,
    'media-confirmed',
    'B',
    2,
    TRUE,
    'Added 2026-05-14 (migration 053). Major global wire, francophone and '
    'Latin American bureaus critical for ANDV (Buenos Aires, Santiago). '
    'No public RSS; Google News source-filter used. Beat: every 30 min.'
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'efe-wire',
    'EFE — hantavirus en español (via Google News)',
    'https://news.google.com/rss/search?q=hantavirus+OR+%22virus+Andes%22+site:efe.com&hl=es-419&gl=AR&ceid=AR:es-419',
    2,
    'media-confirmed',
    'B',
    3,
    TRUE,
    'Added 2026-05-14 (migration 053). World''s largest Spanish-language agency. '
    'Primary wire for Argentina, Chile, Peru, Bolivia hantavirus events. '
    'Credibility 3 (not 2): Spanish text requires translation before analyst '
    'review; serotype/count extraction less reliable on non-English content. '
    'Google News source-filter, Latin American Spanish locale. Beat: every 30 min.'
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'mercopress',
    'Mercopress — South Atlantic News Agency',
    'https://en.mercopress.com/rss',
    3,
    'media-unconfirmed',
    'C',
    3,
    TRUE,
    'Added 2026-05-14 (migration 053). English-language Southern Cone wire. '
    'Covers Patagonian hantavirus outbreaks (Neuquén, Río Negro, Chilean Aysén) '
    'ahead of larger international wires. Direct public RSS 2.0. Beat: hourly.'
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
