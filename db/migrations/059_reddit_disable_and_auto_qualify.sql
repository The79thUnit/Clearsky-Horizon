-- HORIZON migration 059: disable Reddit source + batch analyst confidence pre-fill
-- 2026-05-14
--
-- Reddit (NATO E/4, social-rumour) disabled per source quality review.
-- Social monitoring now handled by Mastodon feeds (NATO C/3, better SNR) and
-- wire services (Reuters, AP, AFP, BBC -- NATO B/2-3).
-- Existing Reddit case_reports are retained for audit trail but excluded from
-- the public API unless a human analyst explicitly sets analyst_confidence.
--
-- The batch auto-qualifier pre-fills analyst_confidence for all non-Reddit
-- records using a NATO reliability band algorithm:
--
--   NATO A (completely reliable):   floor 0.70, cap 0.92
--   NATO B (usually reliable):      floor 0.60, cap 0.85
--   NATO C (fairly reliable):       floor 0.45, cap 0.75
--   NATO D (not usually reliable):  floor 0.30, cap 0.60
--   NATO E (unreliable):            0 -- pipeline x 0.70, cap 0.30
--   NATO F (cannot be judged):      0 -- pipeline x 0.40, cap 0.15
--
-- Identifies as HORIZON-AUTO-SCORER/1.0. Human analysts may override.

\echo '==> HORIZON 059 Reddit disable + batch analyst confidence pre-fill'

-- Step 1: Disable Reddit source
UPDATE sources
SET    enabled    = false,
       updated_at = NOW(),
       notes      = COALESCE(notes || E'\n', '')
                 || '[2026-05-14] Disabled per source quality review. '
                 || 'NATO E/4 social signal; Mastodon feeds (C/3) provide better-qualified '
                 || 'social monitoring. Wire services (B/2-3) cover news. '
                 || 'Existing case_reports retained for audit trail. '
                 || 'Records excluded from public API unless analyst_confidence is set.'
WHERE  code = 'reddit';

\echo 'Reddit source disabled.'

-- Step 2: Batch analyst_confidence pre-fill for all non-Reddit records
-- that have not yet been reviewed (analyst_confidence IS NULL).
UPDATE qualification_scores qs
SET
    analyst_confidence = (
        CASE s.nato_reliability
            WHEN 'A' THEN LEAST(0.92, GREATEST(0.70, qs.pipeline_confidence + 0.05))
            WHEN 'B' THEN LEAST(0.85, GREATEST(0.60, qs.pipeline_confidence + 0.03))
            WHEN 'C' THEN LEAST(0.75, GREATEST(0.45, qs.pipeline_confidence + 0.01))
            WHEN 'D' THEN LEAST(0.60, GREATEST(0.30, qs.pipeline_confidence))
            WHEN 'E' THEN LEAST(0.30, qs.pipeline_confidence * 0.70)
            ELSE           LEAST(0.15, qs.pipeline_confidence * 0.40)
        END
    )::NUMERIC(3,2),
    analyst_id    = 'HORIZON-AUTO-SCORER/1.0',
    analyst_at    = NOW(),
    analyst_notes = 'AUTO-SCORER/1.0 pre-fill (migration 059). NATO-'
                 || s.nato_reliability || s.nato_credibility::text
                 || ' (' || s.name || '). '
                 || 'Machine-assisted qualification. Human override replaces this value.',
    updated_at    = NOW()
FROM case_reports cr
JOIN sources s ON s.id = cr.source_id
WHERE qs.case_report_id = cr.id
  AND qs.analyst_confidence IS NULL
  AND s.code != 'reddit';

\echo 'Batch analyst confidence pre-fill complete.'

-- Report what was done
SELECT
    s.nato_reliability,
    COUNT(*)::int AS records_scored,
    ROUND(AVG(qs.analyst_confidence)::numeric, 3) AS avg_analyst_confidence
FROM qualification_scores qs
JOIN case_reports cr ON cr.id = qs.case_report_id
JOIN sources s ON s.id = cr.source_id
WHERE qs.analyst_id = 'HORIZON-AUTO-SCORER/1.0'
  AND qs.analyst_at >= NOW() - INTERVAL '5 minutes'
GROUP BY s.nato_reliability
ORDER BY s.nato_reliability;
