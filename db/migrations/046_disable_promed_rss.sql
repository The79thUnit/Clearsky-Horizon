-- migration 046 — Disable promed-rss: platform fully paywalled as of 2025.
--
-- Investigation (2026-05-13):
--   ProMED migrated to a Next.js + Auth0 + subscription-based platform in
--   2024-2025 (ISID infrastructure rebuild, covered by Science Nov 2025).
--   Findings:
--     - https://promedmail.org/promed-news/feed/ → Next.js HTML (no RSS)
--     - https://www.promedmail.org/api/v1/* → 401
--       {"success":false,"message":"Authorization header missing"} on ALL paths
--     - posts-sitemap.xml: 5 marketing blog posts only (anniversary, webinar,
--       samdesk alliance, submit info, coming-soon) — none are outbreak reports
--     - Individual /posts/* pages return HTTP 404
--     - robots.txt confirms no public crawler path for outbreak content
--
--   Conclusion: there is no free public access path to ProMED outbreak reports.
--   ProMED is a paid subscription service. The connector WILL fail on every
--   run with a 401 or HTML parse error. Beat schedule entry also removed
--   from celery_app.py (this migration is the DB half of the disable).
--
--   Coverage note: ProMED was a secondary aggregator (NATO B2). The same
--   outbreak events are covered by paho-alerts (A1), paho-news (B2),
--   who-don (A2), cdc-han (A1), ecdc-rapid (A1), and the academic feeds.
--   The gap is minimal.
--
--   Re-enable path: if ProMED ever restores a public RSS feed or offers a
--   free API tier, write migration 0NN_reenable_promed_rss.sql, update
--   the FEED_URL in connectors/promed_rss.py, and restore the beat entry.

BEGIN;

UPDATE sources
SET
    enabled    = FALSE,
    notes      = 'DISABLED 2026-05-13 (migration 046). ProMED migrated to '
                 'Next.js + Auth0 + subscription model in 2024-2025. '
                 '/promed-news/feed/ returns HTML; /api/v1/* returns 401. '
                 'posts-sitemap.xml has 5 marketing posts only (no outbreak '
                 'reports). No public free-tier access path exists. '
                 'Coverage gap is minimal — same events covered by '
                 'paho-alerts (A1), paho-news (B2), who-don, cdc-han, '
                 'ecdc-rapid. Re-enable if ProMED restores a public feed.',
    updated_at = NOW()
WHERE code = 'promed-rss';

COMMIT;
