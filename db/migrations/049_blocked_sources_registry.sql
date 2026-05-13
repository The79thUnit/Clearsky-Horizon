-- migration 049 — Blocked/unreachable sources registry.
--
-- WHO EMRO (who-emro):
--   Disabled. emro.who.int/rss-feeds/whoemro-rss.xml returns 302→404.
--   WHO CMS restructure also broke EMRO RSS alongside euro/searo/wpro feeds.
--   WHO EMRO region (Egypt, Iran, Saudi Arabia, Iraq, etc.) has minimal
--   ANDV/HFRS burden; who-don global disease outbreak news provides adequate
--   coverage. Beat minute=9 removed.
--   Re-enable if WHO EMRO publishes a replacement RSS URL.
--
-- KDCA (kdca):
--   Korean Disease Control and Prevention Agency. Korea has the highest HFRS
--   burden outside China (Seoul virus, Hantaan virus, Soochong virus).
--   URL probed: https://www.kdca.go.kr/board/board.es?mid=a20501010000&bid=0015
--   Geo-blocked: SSL handshake failure (cURL 000) from all EU/US IPs including
--   OVH VPS hantavirus.software (Gravelines, FR). .go.kr TLD blocks non-Korean IP
--   ranges at TLS level. No accessible path, mirror, or CDN variant found.
--   Stored DISABLED as a known gap for future re-assessment.
--   Re-enable path: Korean residential proxy / Scraper API with KR exit node.
--
-- THL — Finnish Institute for Health and Welfare (thl-finland):
--   Finland is PUUV (Puumala virus) endemic — one of the highest per-capita
--   hantavirus notification rates in Europe (Fennoscandia zone). THL publishes
--   weekly PUUV incidence data and communicable disease situation reports.
--   URL probed: https://thl.fi/en/web/infectious-diseases-and-vaccinations/
--              current-issues/communicable-disease-situation-in-finland
--   Blocked: Cloudflare Bot Management returns managed JS challenge (HTTP 403)
--   from OVH VPS. sampo.thl.fi pivot service accessible from OVH but returns
--   "Not available" for all communicable-disease pivot queries.
--   Accessible from residential IPs with rate limiting (HTTP 429, Retry-After: 8s).
--   Stored DISABLED as a known gap.
--   Partial coverage: ECDC CDTR + PubMed index THL-originated PUUV alerts
--   with 1-3 day lag.
--   Re-enable path: Scraper API with residential proxy / Cloudflare bypass.

BEGIN;

-- ---- WHO EMRO: disable dead RSS URL ----------------------------------------
UPDATE sources
SET enabled    = FALSE,
    notes      = notes
                 || E'\nDISABLED 2026-05-13 (migration 049). '
                 || 'emro.who.int/rss-feeds/whoemro-rss.xml returns 302 then 404. '
                 || 'WHO CMS restructure broke EMRO RSS (same root cause as euro/searo/wpro). '
                 || 'EMRO region has minimal ANDV/HFRS burden; covered by who-don. '
                 || 'Re-enable if WHO EMRO publishes a replacement RSS URL.',
    updated_at = NOW()
WHERE code = 'who-emro';

-- ---- KDCA: Korean CDC (geo-blocked, known gap) ------------------------------
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'kdca',
    'KDCA — Korea Disease Control and Prevention Agency (press releases)',
    'https://www.kdca.go.kr/board/board.es?mid=a20501010000&bid=0015',
    2,
    'official-authority',
    'B',
    2,
    FALSE,
    'Added 2026-05-13 (migration 049). DISABLED — geo-blocked at TLS level. '
    'Korea has the highest HFRS burden outside China; Seoul virus (SEOV), '
    'Hantaan virus (HTNV), and Soochong virus (SOOV) all endemic. '
    'SSL handshake failure (cURL 000) from all EU/US IPs including OVH VPS '
    'hantavirus.software (Gravelines FR). .go.kr TLD blocks non-Korean IP ranges. '
    'No accessible path, CDN variant, or English-language mirror found. '
    'Re-enable: Korean residential proxy or Scraper API with KR exit node. '
    'Beat: not scheduled (disabled on add).'
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

-- ---- THL: Finnish Institute for Health and Welfare (Cloudflare-blocked) ----
INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled, notes)
VALUES (
    'thl-finland',
    'THL — Finnish Institute for Health and Welfare (communicable disease surveillance)',
    'https://thl.fi/en/web/infectious-diseases-and-vaccinations/current-issues/communicable-disease-situation-in-finland',
    2,
    'official-authority',
    'B',
    2,
    FALSE,
    'Added 2026-05-13 (migration 049). DISABLED — Cloudflare Bot Management. '
    'Finland is PUUV (Puumala virus) endemic with one of the highest per-capita '
    'hantavirus notification rates in Europe (Fennoscandia zone). THL publishes '
    'weekly PUUV incidence and communicable disease situation reports. '
    'Cloudflare managed JS challenge (HTTP 403) from OVH VPS hantavirus.software. '
    'sampo.thl.fi pivot service accessible from OVH but returns "Not available" '
    'for all communicable disease pivot queries. '
    'Accessible from residential IPs with rate limiting (HTTP 429, Retry-After: 8s). '
    'Partial coverage via ECDC CDTR + PubMed (1-3 day lag on THL PUUV alerts). '
    'Re-enable: Scraper API with residential proxy exit node. '
    'Beat: not scheduled (disabled on add).'
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
