-- migration 038 — add NCBI GenBank orthohantavirus sequence-record source.
--
-- NCBI E-utilities esearch + esummary against db=nuccore with term
-- orthohantavirus[organism], reldate=14.
--
-- This is the molecular confirmation layer. Genome deposits to GenBank
-- arrive 24-72h before formal WHO DON updates because sequencing labs
-- upload directly to NCBI once the sequence QC passes. The Swiss MV
-- Hondius case (PZ385161-163, ANDV/Switzerland/Hu-3337/2026) was
-- deposited 2026-05-11 — three segments (S, M, L), all annotated
-- Homo sapiens / Switzerland / collection 2026-05-04. Verified
-- accessible 2026-05-13.
--
-- Provenance: sequence-record (INSDC-submitted primary molecular data).
-- NATO rating: A1 (completely reliable, confirmed by definition —
-- the deposit IS primary evidence, not a report about evidence).

BEGIN;

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility, enabled)
VALUES (
    'ncbi-virus',
    'NCBI GenBank — orthohantavirus sequence records (E-utilities)',
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
    1,
    'sequence-record',
    'A',
    1,
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
