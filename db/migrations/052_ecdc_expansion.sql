-- migration 052 — ECDC sub-feed expansion: Risk Assessments + Epidemiological Updates.
--
-- We already capture ecdc-cdtr (Scientific and Technical Publications,
-- /en/taxonomy/term/1244/feed) which is the super-feed. These two additions
-- target specific high-signal sub-categories:
--
-- ECDC RISK ASSESSMENTS (ecdc-risk):
--   URL: https://www.ecdc.europa.eu/en/taxonomy/term/1295/feed
--   Confirmed 200, RSS 2.0, 10 items, 2026-05-13.
--   Rapid Risk Assessments (RRAs) are published when an event meets the
--   threshold for EU-level scientific assessment. An ECDC RRA for hantavirus
--   is a very high-confidence signal. During the 2026 MV Hondius cluster,
--   ECDC published an RSA covering secondary spread risk in repatriated EU
--   passengers. Beat: every 6h, minute=36.
--
-- ECDC EPIDEMIOLOGICAL UPDATES (ecdc-updates):
--   URL: https://www.ecdc.europa.eu/en/taxonomy/term/1310/feed
--   Confirmed 200, RSS 2.0, 10 items, 2026-05-13.
--   First item: "MERS-CoV worldwide overview" (2026-05-11).
--   Epidemiological updates are pathogen-specific surveillance summaries
--   published when new EU-level data warrants an update. A hantavirus
--   epidemiological update represents authoritative EU case-count data.
--   Beat: every 6h, minute=43.
--
-- The existing cross-source dedup (content_topic_hash 7-day window) handles
-- any overlap between these feeds and ecdc-cdtr.

BEGIN;

-- ECDC Rapid Risk Assessments
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'ecdc-risk',
    'ECDC Rapid Risk Assessments RSS',
    'https://www.ecdc.europa.eu/en/taxonomy/term/1295/feed',
    1,
    'official-authority',
    'A',
    2,
    TRUE,
    'Added 2026-05-13 (migration 052). ECDC Rapid Risk Assessments: published '
    'when an event meets EU-level assessment threshold. An ECDC RRA for hantavirus '
    'is a very high-confidence signal. Complements ecdc-cdtr (super-feed at '
    '/taxonomy/term/1244). 10 items on add date. '
    'Beat: every 6h minute=36.'
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

-- ECDC Epidemiological Updates
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'ecdc-updates',
    'ECDC Epidemiological Updates RSS',
    'https://www.ecdc.europa.eu/en/taxonomy/term/1310/feed',
    1,
    'official-authority',
    'A',
    2,
    TRUE,
    'Added 2026-05-13 (migration 052). ECDC Epidemiological Updates: pathogen-'
    'specific EU surveillance summaries. High-confidence EU case-count data. '
    'Complements ecdc-cdtr (super-feed). 10 items on add date. '
    'First item on add date: MERS-CoV worldwide overview (2026-05-11). '
    'Beat: every 6h minute=43.'
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
