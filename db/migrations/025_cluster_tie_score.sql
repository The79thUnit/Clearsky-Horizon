-- migration 025 — cluster_tie_score on extraction_proposals
--
-- Phoenix rule (12 May 2026 PM): a proposal can only auto-update the
-- ontology if the article it came from is provably tied to the MV Hondius
-- cluster. This adds the column + index needed to enforce that.
--
--   1.0  STRONG  — article names the ship / route port / operator
--   0.5  MEDIUM  — hantavirus + evacuee/repatriation + route country
--   0.0  WEAK    — hantavirus mention only (these are rejected at the
--                  extractor stage; we don't even write a proposal row)

BEGIN;

ALTER TABLE extraction_proposals
ADD COLUMN IF NOT EXISTS cluster_tie_score REAL NOT NULL DEFAULT 0.0;

ALTER TABLE extraction_proposals
ADD COLUMN IF NOT EXISTS cluster_tie_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_extraction_proposals_tie
ON extraction_proposals (cluster_tie_score)
WHERE applied = false AND rejected = false;

COMMIT;
