-- migration 036 — re-enable australia-health.
--
-- CONTEXT: Migration 031 disabled this source after every plain-httpx
-- fetch from our VPS hung at the TLS Finished step (Akamai's WAF in
-- front of www.health.gov.au silently severs the TLS handshake when
-- the client's JA3/JA4 fingerprint matches Python's default httpx).
--
-- New evidence (2026-05-13 09:55 UTC): probing the same URL with
-- curl_cffi using Chrome-120 TLS fingerprint impersonation returns
-- HTTP 200 + 8,621 bytes of real RSS XML. Akamai accepts the
-- handshake when the client TLS profile matches a real browser.
--
-- This migration re-enables the source. The connector code is
-- unchanged — the new fetch path lives in BaseConnector.run() which
-- now tries curl_cffi first, falls back to httpx otherwise.

BEGIN;

UPDATE sources
SET enabled = TRUE,
    updated_at = NOW()
WHERE code = 'australia-health';

COMMIT;
