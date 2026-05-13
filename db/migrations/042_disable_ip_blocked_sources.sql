-- migration 042 — Disable nmh-data and chile-deis: persistent OVH-IP blocks.
--
-- PROBES (server-side, 2026-05-13):
--
-- nmh-data:  www.nmhealth.org/about/erd/ideb/zdp/hps/ -> 000 (TCP timeout after 30s)
--   Quality log: 7 consecutive status=0 failures across all fetches since 2026-05-11.
--   US government sites frequently blocklist commercial VPS IP ranges. NM HPS
--   case data is covered by CDC HAN (enabled, A1), CDC MMWR, pubmed, and google-news.
--
-- chile-deis: www.minsal.cl/feed/ -> 403 + ALL alternative paths 403 (4554B WAF response)
--   Quality log: 43 consecutive status=0 failures since first deploy 2026-05-11.
--   Chile MoH has a WAF that blocks the OVH Gravelines IP range entirely.
--   ANDV Chile coverage mitigated by paho-alerts (enabled, A1) and google-news
--   Spanish-language query. High-priority re-enable if IP situation resolves or a
--   different fetch path (Tor egress / Cloudflare Workers proxy) becomes available.
--
-- Both connectors keep their Python source files in place for trivial re-enable.

BEGIN;

UPDATE sources
SET enabled = FALSE,
    notes = 'DISABLED 2026-05-13 (migration 042): www.nmhealth.org TCP timeout (000) '
            'on all fetches from OVH VPS. US government site blocking commercial VPS '
            'IPs. Coverage maintained by cdc-han, cdc-mmwr, pubmed, google-news. '
            'Re-enable if proxy/residential IP available.',
    updated_at = NOW()
WHERE code = 'nmh-data';

UPDATE sources
SET enabled = FALSE,
    notes = 'DISABLED 2026-05-13 (migration 042): minsal.cl WAF returns 403 on all '
            'paths from OVH Gravelines IP range. Chile is a primary ANDV country; '
            'high-priority re-enable target. Coverage maintained by paho-alerts (A1) '
            'and google-news Spanish-language query. Re-enable if IP or proxy changes.',
    updated_at = NOW()
WHERE code = 'chile-deis';

COMMIT;
