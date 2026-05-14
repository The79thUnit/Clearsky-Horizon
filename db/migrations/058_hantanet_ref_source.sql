-- HORIZON migration 058: seed cdc-hantanet-ref source.
--
-- CDC HantaNet reference genome set (github.com/CDCgov/HantaNet) was
-- published by CDC's Molecular Epidemiology and Bioinformatics Team and
-- peer-reviewed in Viruses (MDPI, November 2023, PMC10675615). It provides
-- 41 curated reference genomes for all three Orthohantavirus gene segments
-- (S/M/L) covering US isolates 1984-2016.
--
-- The genomic data is stored in MicrobeTrace's proprietary .microbetrace
-- binary format and has no standalone CSV export. The canonical source for
-- those same accession numbers is NCBI GenBank RefSeq. This connector fetches
-- the complete Orthohantavirus RefSeq set via NCBI E-utilities (no reldate
-- filter) to build a static genomic reference layer that does NOT overlap
-- with ncbi-virus (migration 038, reldate=14 days only).
--
-- provenance_type: sequence-record (defined in migration 001, no DDL change
-- needed). NATO A1: NCBI RefSeq is US federal genomic data infrastructure.
-- Tier 2: curated reference data, not primary outbreak surveillance.

\echo '==> HORIZON 058 cdc-hantanet-ref source'

INSERT INTO sources (code, name, url, tier, provenance_type,
                     nato_reliability, nato_credibility,
                     fetch_interval_sec, enabled, notes)
VALUES (
    'cdc-hantanet-ref',
    'CDC HantaNet — Orthohantavirus RefSeq Reference Genomes (NCBI)',
    'https://github.com/CDCgov/HantaNet',
    2,
    'sequence-record',
    'A',
    1,
    86400,  -- daily; RefSeq reference sequences update infrequently
    TRUE,
    'Added 2026-05-14 (migration 058). CDC HantaNet reference genome set '
    'via NCBI E-utilities. Fetches ALL Orthohantavirus[Organism] RefSeq '
    'nucleotide records (no date filter): ~200-300 records covering S/M/L '
    'segments for all major serotypes. HantaNet published in Viruses MDPI '
    'November 2023 (PMC10675615). Apache 2.0 + CC0. '
    'Distinct from ncbi-virus (migration 038, reldate=14 days) which covers '
    'recent molecular confirmation; this source covers the static historical '
    'reference layer. Enables serotype → genomic lineage annotation. '
    'NATO A1 (NCBI RefSeq is US federal scientific infrastructure). '
    'Beat: 07:47 UTC daily.'
)
ON CONFLICT (code) DO UPDATE SET
    name             = EXCLUDED.name,
    url              = EXCLUDED.url,
    tier             = EXCLUDED.tier,
    provenance_type  = EXCLUDED.provenance_type,
    nato_reliability = EXCLUDED.nato_reliability,
    nato_credibility = EXCLUDED.nato_credibility,
    fetch_interval_sec = EXCLUDED.fetch_interval_sec,
    enabled          = EXCLUDED.enabled,
    notes            = EXCLUDED.notes,
    updated_at       = NOW();

INSERT INTO schema_migrations (version) VALUES ('058_hantanet_ref_source')
    ON CONFLICT DO NOTHING;

\echo '==> 058 done (cdc-hantanet-ref seeded)'
