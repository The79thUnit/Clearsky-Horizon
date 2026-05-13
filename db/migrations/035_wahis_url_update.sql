-- migration 035 — Tier-1 audit follow-on: WAHIS URL update.
--
-- The original wahis.woah.org/rss/list/EVENT endpoint now returns
-- HTTP 404 (verified 2026-05-13). WAHIS migrated entirely to a React
-- single-page app backed by wahis.woah.org/api/v1/... — that REST
-- API requires API credentials we don't have access to.
--
-- The WOAH organisation's main news feed at www.woah.org/en/rss/
-- remains publicly accessible (HTTP 200, application/rss+xml, 77 KB,
-- 10 recent items per fetch). It carries higher-level WOAH bulletins
-- including the official "WOAH Statement on Hantavirus" published
-- 8 May 2026 (the WOAH position paper on the MV Hondius cluster).
--
-- Connector PARSER_VERSION bumped to 0.2.0; this row keeps the source
-- registry in sync.

BEGIN;

UPDATE sources
SET url = 'https://www.woah.org/en/rss/',
    name = 'WOAH — World Organisation for Animal Health (news feed)',
    updated_at = NOW()
WHERE code = 'wahis';

COMMIT;
