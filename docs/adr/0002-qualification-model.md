# ADR-0002: Source Qualification Model

**Status:** Accepted
**Date:** 2026-05-11
**Decision-maker:** 79th Unit Limited

## Context

HORIZON's wedge against every competitor tracker (HantaCount, HantaTracker.app,
EpiTrace, etc.) is auditable source provenance. Every record must surface:

- WHERE it came from (source registry + ICD 206 SRC)
- HOW RELIABLE the source generally is (NATO Admiralty Scale)
- HOW CONFIDENT the system is in this specific record (pipeline_confidence)
- HOW CONFIDENT a human analyst is after review (analyst_confidence)
- FORENSIC INTEGRITY of the capture (Berkeley Protocol chain-of-custody)

No competitor implements this. Every competitor treats sources as binary
(cited or not) and weighs WHO confirmed cases identically with Twitter rumours.

## Decision

Adopt a four-layer qualification model:

1. **ICD 206 SRC citation** (worker.core.src_citation)
   Format: `[CLASS] source_code (NATO) "title" source_name, YYYY-MM-DD`
   Required on every record.

2. **NATO Admiralty Scale A1 to F6** (worker.core.nato)
   STANAG 2511. Set per-source as the default, can be overridden per-record.
   Base confidence table hard-coded after calibration against ICD 206 examples.

3. **Dual confidence** (worker.core.qualification)
   - `pipeline_confidence`: auto-calculated, bounded [0.0, 0.99]
     formula: base(NATO) + corroboration_boost - recency_decay
       corroboration: +0.02 per source, cap +0.10
       recency: -0.001/day after 7-day grace, cap -0.05
   - `analyst_confidence`: human-set, nullable until reviewed
   Both surfaced separately in the UI. Amber for pipeline, green for analyst.

4. **Berkeley Protocol chain-of-custody** (worker.core.chain_of_custody)
   SHA-256 hash of raw payload + raw URL + UTC capture timestamp + parser version.
   Stored on every record. Required for forensic reproducibility.

## Why these numbers

`PIPELINE_CONFIDENCE_CAP = 0.99` because automation should never claim 1.0.
A1 from automation gets 0.95, which means even WHO with a confirmed report
needs analyst review to reach 1.0.

`CORROBORATION_PER_SOURCE = 0.02, MAX_BOOST = 0.10` because diminishing returns:
5 sources independently corroborating is a strong signal, but the 11th adds nothing
the 10th did not.

`RECENCY_GRACE_DAYS = 7` because most outbreak reports are not invalidated by
being a week old. After that, slow decay starts: a year-old report is at -0.05
versus its day-of confidence.

## Consequences

Pros (intended):
- Auditable. Journalists can trust the score because the trail is visible.
- Defensible. ICD 206 + NATO + Berkeley = three independent international standards.
- Distinguishable. Visible difference between "WHO confirmed" and "Twitter rumour"
  is the wedge against every existing competitor.
- Extensible. New factors (e.g. translation_confidence, language_certainty) can
  be added to the qualification pipeline without schema migration if we store
  in `pipeline_factors` JSONB.

Cons (accepted, mitigated):
- Calibration is judgement. Numbers above are defensible but not optimal.
  Mitigation: log all factor values so we can recalibrate from real data.
- Performance: every ingest calls `calculate()`. Bench at 10k records: should
  complete in <100ms total (pure Python, no I/O). Acceptable.

## Hard stops on changes

**Any** change to this model requires:
1. New ADR (do not modify this one)
2. Phoenix sign-off
3. Re-test of every NATO score in the existing test matrix

The qualification model is HORIZON's moat. Treat it accordingly.

## Related

- ADR-0001: Stack choice
- ADR-0003 (forthcoming, T-04): Connector framework
