-- migration 050 — arXiv connector HTTPS fix.
--
-- The arXiv export API at export.arxiv.org no longer accepts plain HTTP
-- connections (status_code=0 from OVH VPS; port 80 closed). The connector
-- was using http:// which produced a hard connection failure rather than
-- a redirect. Updating to https:// restores fetch behaviour.
--
-- Confirmed: https://export.arxiv.org/api/query?search_query=all:hantavirus
-- returns HTTP 200, valid Atom feed, 16 items, 2026-05-13.
--
-- Connector PARSER_VERSION bumped 0.1.0 -> 0.2.0 in arxiv.py.

BEGIN;

UPDATE sources
SET url        = 'https://export.arxiv.org/api/query',
    notes      = COALESCE(notes, '')
                 || E'\nFIXED 2026-05-13 (migration 050). http:// -> https://. '
                 || 'export.arxiv.org port 80 closed; plain HTTP produced '
                 || 'status_code=0 from OVH VPS. HTTPS confirmed 200, valid Atom, '
                 || '16 hantavirus papers. Parser 0.1.0->0.2.0.',
    updated_at = NOW()
WHERE code = 'arxiv';

COMMIT;
