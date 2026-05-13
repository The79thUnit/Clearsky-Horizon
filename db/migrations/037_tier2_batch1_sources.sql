-- migration 037 — Tier-2 audit batch 1: register new sources.
--
-- Two new sources verified reachable from the production worker on
-- 2026-05-13 via curl_cffi(chrome120):
--
--   1. avian-flu-diary  Mike Coston's outbreak blog (running since
--      2006). Despite the avian flu naming, covers the full zoonotic
--      portfolio: hantavirus, MERS-CoV, Marburg, Nipah, etc. Feed at
--      afludiary.blogspot.com/feeds/posts/default returns 25 recent
--      items as Atom XML. Value-add is rapid commentary on primary
--      sources (WHO DON / CDC HAN / ECDC) — secondary not primary,
--      hence NATO B3.
--
--   2. one-health  Elsevier open-access peer-reviewed journal
--      (ISSN 2352-7714) covering the human/animal/environment
--      interface. Reservoir-host papers (Peromyscus, Oligoryzomys,
--      Apodemus serosurveys) establish baseline ecology before human
--      clusters surface. Feed at rss.sciencedirect.com/publication/
--      science/23527714 returns 100 items (full TOC + ahead-of-print).
--      Peer-reviewed and PubMed-indexed, hence NATO A2.
--
-- Both are corroborative sources; the extraction pipeline's
-- cluster-tie-score gate prevents auto-application without a primary
-- corroborating bulletin from an A1 authority.

BEGIN;

-- Avian Flu Diary — aggregator commentary blog.
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'avian-flu-diary',
    'Avian Flu Diary (Mike Coston) — zoonotic outbreak commentary',
    'https://afludiary.blogspot.com/feeds/posts/default',
    3,
    'aggregator',
    'B',
    3,
    TRUE
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    updated_at       = NOW();

-- One Health — Elsevier peer-reviewed open-access journal.
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'one-health',
    'One Health (Elsevier, ISSN 2352-7714) — human/animal/environment interface',
    'https://rss.sciencedirect.com/publication/science/23527714',
    2,
    'peer-reviewed',
    'A',
    2,
    TRUE
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    enabled          = EXCLUDED.enabled,
    updated_at       = NOW();

COMMIT;
