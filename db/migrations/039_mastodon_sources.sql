-- migration 039 — Tier-2 batch 2: Mastodon hashtag sources.
--
-- mastodon.social exposes public RSS feeds for hashtag timelines at
-- /tags/{tag}.rss, no authentication required. Verified 2026-05-13:
--
--   #hantavirus : 35 KB, real-time public-health posts (C3)
--   #MVHondius  : 42 KB, vessel-specific MV Hondius cluster (C3)
--
-- Both are registered as separate sources so they can be independently
-- scheduled and their quality metrics tracked separately.
--
-- NATO rating: C3 — social media (possibly unverified source, possibly
-- true). Posts from epidemiologists and journalists are fast but require
-- corroboration from A1/B2 sources before analyst confidence is set.
-- The extraction pipeline's cluster-tie-score gate prevents auto-
-- application without a corroborating primary-source bulletin.

BEGIN;

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'mastodon-hantavirus',
    'Mastodon #hantavirus (mastodon.social) — real-time social commentary',
    'https://mastodon.social/tags/hantavirus.rss',
    3,
    'aggregator',
    'C',
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

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'mastodon-hondius',
    'Mastodon #MVHondius (mastodon.social) — MV Hondius cluster feed',
    'https://mastodon.social/tags/MVHondius.rss',
    3,
    'aggregator',
    'C',
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

COMMIT;
