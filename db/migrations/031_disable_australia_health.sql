-- migration 031 — Item 2 of the 13 May 2026 audit: disable
-- australia-health source.
--
-- AUDIT FINDING (verified by curl 2026-05-13 09:07 UTC):
--
-- www.health.gov.au sits behind Akamai's edge WAF (resolved IPv6 ranges
-- 2a02:26f0:9100:6::1748:f8xx are Akamai-allocated). TLS handshake
-- completes, but the connection then hangs at TLS Finished — Akamai
-- silently drops our request mid-stream. Result: HTTP 000 in 0.6
-- seconds for every probe across multiple URL variations.
--
-- This is not fixable on our side:
--   - Bumping the timeout doesn't help (the connection is being
--     intentionally severed, not stalled by latency).
--   - Switching IPs would only buy us minutes before Akamai re-blocks.
--   - The site has no public API alternative.
--
-- Signal cost of disabling: very low. Australia has no endemic
-- hantavirus serotype; imported cases are notifiable but historically
-- rare (single-digit per year). Coverage will continue via Google News
-- (which DOES syndicate AU MoH press releases) and australian press.
--
-- The connector code stays in place under
-- worker/horizon_worker/connectors/australia_health.py so that if AU
-- MoH ever publishes a non-Akamai-protected feed (or offers an API key
-- programme) we can re-enable in one line.

BEGIN;

UPDATE sources
SET enabled = FALSE,
    updated_at = NOW()
WHERE code = 'australia-health';

COMMIT;
