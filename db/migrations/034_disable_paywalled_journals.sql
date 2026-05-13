-- migration 034 — Tier-1 audit follow-on: disable redundant paywalled
-- journal connectors that PubMed already covers.
--
-- CONTEXT: eurosurveillance, jvi-asm, mbio, viruses-mdpi all return
-- HTTP 403/0 from our VPS (publisher anti-scraper WAFs). Article count
-- ingested over the lifetime of each source: ZERO. Meanwhile, the
-- canonical pubmed connector (verified 2026-05-13: 44 articles ingested
-- including The Journal of general virology, BMJ, Nature, EBioMedicine,
-- Microbiology and immunology, etc.) indexes every PubMed-tagged
-- hantavirus paper regardless of publishing journal. mBio, JVI,
-- Eurosurveillance, Viruses (MDPI) all index in PubMed, so their
-- hantavirus papers DO arrive — just via the pubmed pipe, not their
-- individual RSS connectors.
--
-- ACTION: disable the four redundant connectors. Keep their Python
-- source in place under worker/horizon_worker/connectors/ in case a
-- publisher restores open RSS later. The connector classes remain
-- importable; only the source-registry enabled flag flips.
--
-- KEPT ENABLED:
--   * lancet-id        — HTTP 200, just no hantavirus content yet
--   * plos-pathogens   — HTTP 200, low signal but working
--   * plos-ntds        — HTTP 200, 1 article ingested
--   * cdc-eid          — HTTP 200, fetches successful
--   * cdc-eid-ahead    — HTTP 200, fetches successful
--   * pubmed           — 44 articles, working perfectly
--
-- SIGNAL LOSS: zero. PubMed catches everything these did and more.

BEGIN;

UPDATE sources
SET enabled = FALSE,
    updated_at = NOW()
WHERE code IN (
    'eurosurveillance',
    'jvi-asm',
    'mbio',
    'viruses-mdpi'
);

COMMIT;
