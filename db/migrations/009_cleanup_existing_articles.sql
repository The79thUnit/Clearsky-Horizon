-- HORIZON migration 009: clean up existing articles ingested before the
-- HTML-strip + dedup fixes landed. Idempotent.

\echo '==> HORIZON 009 cleanup existing articles (one-time)'

-- Strip HTML tags and unescape common entities from existing summaries.
UPDATE case_reports
SET summary = btrim(regexp_replace(
        regexp_replace(
          regexp_replace(summary, E'<[^>]+>', ' ', 'g'),
          E'&(nbsp|amp|quot|lt|gt|#\d+);', ' ', 'g'
        ),
        E'\s+', ' ', 'g'
      ))
WHERE summary IS NOT NULL AND summary ~ E'<[^>]+>';

-- Drop the SEO / explainer entries that aren't outbreak events.
DELETE FROM qualification_scores
 WHERE case_report_id IN (
   SELECT id FROM case_reports
   WHERE LOWER(title) ~ '(what is hantavirus|how worried|should i be worried|symptoms you need|how it differs|tell us:|inside the laboratory|hantavirus[: ]+the silent|jersey hantavirus risk|rapid reaction)'
 );
DELETE FROM case_reports
 WHERE LOWER(title) ~ '(what is hantavirus|how worried|should i be worried|symptoms you need|how it differs|tell us:|inside the laboratory|hantavirus[: ]+the silent|jersey hantavirus risk|rapid reaction)';

-- Back-fill content_topic_hash for any row that doesn't have one yet.
-- We can't compute the blake2 hash in pure SQL the same way Python does, so
-- we use a cheap MD5 of the lowercased title with stopwords removed.
-- This is a rough equivalent for back-fill purposes; new ingestion uses the
-- proper blake2 hash from text_utils.topic_hash().
UPDATE case_reports
SET content_topic_hash = SUBSTRING(
    MD5(
      regexp_replace(LOWER(title), E'[^a-z0-9 ]', ' ', 'g')
    )
    FROM 1 FOR 16
  )
WHERE content_topic_hash IS NULL AND title IS NOT NULL;

\echo '==> 009 done (existing articles cleaned)'
