-- migration 044 -- Housekeeping: disable CNN orphan + document GBIF multi-taxon fix.
--
-- CNN ORPHAN:
--   The 'cnn' source record was seeded with enabled=TRUE but has never had
--   a connector class or a beat schedule entry. Every missed poll is silent --
--   no connector means the task never fires, but the source appears as
--   enabled=true in the Sources tab, which is misleading.
--   Disable it with an explanatory note. The Python file does not exist so
--   there is nothing to delete.
--
-- GBIF MULTI-TAXON FIX:
--   GBIFConnector 0.1.0 queried only Peromyscus maniculatus (SNV host).
--   0.2.0 (2026-05-13) overrides fetch_raw to pass all five reservoir species
--   as repeated taxonKey params:
--     2436895 Peromyscus maniculatus  (SNV)
--     2438009 Oligoryzomys longicaudatus (ANDV) -- the primary ANDV host
--     2437394 Apodemus agrarius        (HTNV)
--     8260714 Myodes glareolus         (PUUV)
--     2439261 Rattus norvegicus        (SEOV)
--   The curl_cffi path is skipped for GBIF (no WAF on api.gbif.org).

BEGIN;

-- Disable CNN orphan.
UPDATE sources
SET enabled    = FALSE,
    notes      = 'DISABLED 2026-05-13 (migration 044): seeded as an enabled source '
                 'but no connector class or beat schedule entry was ever created. '
                 'CNN homepage is not a parseable hantavirus data source. Kept for '
                 'audit trail; do not re-enable without a connector.',
    updated_at = NOW()
WHERE code = 'cnn';

-- Document the GBIF multi-taxon connector fix.
UPDATE sources
SET notes      = 'GBIF connector 0.2.0 (2026-05-13, migration 044): 0.1.0 queried '
                 'only Peromyscus maniculatus (SNV). 0.2.0 queries all five reservoir '
                 'hosts via repeated taxonKey params: P. maniculatus (SNV), '
                 'O. longicaudatus (ANDV), A. agrarius (HTNV), M. glareolus (PUUV), '
                 'R. norvegicus (SEOV). curl_cffi path skipped; httpx handles GBIF fine.',
    updated_at = NOW()
WHERE code = 'gbif';

COMMIT;
