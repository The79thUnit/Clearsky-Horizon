-- migration 030 — Item 1 of the 13 May 2026 audit: fix rki RSS URL,
-- disable nz-moh source with documented reason.
--
-- AUDIT FINDINGS (verified by server-side curl 2026-05-13 09:00 UTC):
--
-- 1) rki: the old feed URL
--      https://www.rki.de/SiteGlobals/Functions/RSSFeed/RSSGenerator/RSS_EpidBull.xml
--    now returns HTTP 404. RKI restructured the public website in
--    2025-26 and moved the Epidemiologisches Bulletin RSS to the
--    institutional edoc server. New canonical URL:
--      https://edoc.rki.de/feed/rss_2.0/176904/45
--    Verified: HTTP 200, application/rss+xml, 4 recent items (most
--    recent published Thu, 07 May 2026), weekly cadence intact.
--    Connector PARSER_VERSION bumped to 0.2.0 to invalidate any
--    cached parses against the old URL.
--
-- 2) nz-moh: every NZ-government health domain we probed is fully
--    behind Imperva Incapsula anti-bot. tewhatuora.govt.nz/news.rss
--    returns 302→/_Incapsula_Resource challenge page (HTML 200 OK
--    but no real feed body); healthnz.govt.nz endpoints all 403;
--    health.govt.nz/news-media/rss.xml redirects to /node/10 with a
--    Cloudflare managed challenge (5.3 KB Cloudflare interstitial
--    HTML). There is no public-RSS path that bypasses this without
--    a scraping proxy that solves Incapsula/Cloudflare challenges,
--    which we will not add (legally grey, against TOS, unreliable).
--    Action: disable the connector at the source registry. The
--    connector code stays in place under
--    worker/horizon_worker/connectors/nz_moh.py in case Te Whatu Ora
--    later publishes a non-protected feed.

BEGIN;

UPDATE sources
SET url = 'https://edoc.rki.de/feed/rss_2.0/176904/45',
    updated_at = NOW()
WHERE code = 'rki';

UPDATE sources
SET enabled = FALSE,
    updated_at = NOW()
WHERE code = 'nz-moh';

COMMIT;
