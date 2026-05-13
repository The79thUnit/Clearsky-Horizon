# Changelog

All notable changes to HORIZON. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- European Tier 1 sources: SPF France, FHM (Sweden), FHI (Norway), PHAC (Canada),
  UKHSA (United Kingdom) — all qualified at NATO Admiralty reliability A/B
- ECDC sub-feeds: CDTR, Risk Assessments, and Epidemiological Updates tracked as
  separate sources with independent qualification scores
- Recency decay on pipeline_confidence: -0.001/day after 7-day grace, floor -0.05
- Corroboration bonus: +0.02 per independent confirming source, capped at +0.10
- Source quality log: per-fetch reliability and credibility history for every connector
- MV Hondius AIS vessel tracking connector (Tier 3, contextual)
- Google News serotype-specific query connectors (ANDV, PUUV, HTNV, SEOV, DOBV, SNV)

---

## [0.3.0] — 2026-05-11

### Added
- Full Celery worker pipeline: ingest task writes case_reports, qualification_scores,
  and source_quality_log per fetch cycle
- Beat scheduler: ProMED connector runs every 15 minutes by default; configurable per source
- Flower monitoring endpoint for task queue visibility
- 50-test suite with 68.91% coverage; 100% coverage on core qualification modules
- Quality gate enforcement: ruff, mypy --strict (0 issues across 15 source files),
  bandit (0 issues across 762 LOC), pytest (passes 60% gate)

### Changed
- Connector framework refactored to BaseConnector abstract class with standardised
  fetch_and_parse lifecycle and typed ParsedItem / FetchResult dataclasses

---

## [0.2.0] — 2026-04-28

### Added
- Production launch: platform live at hantavirus.software
- FastAPI public read-only API at :8000 — /health, /api/v1/cases, /api/v1/sources,
  OpenAPI 3.x docs at /api/docs
- React 18 + TypeScript + Vite frontend: Cases tab, Sources tab, Methodology tab
- Dual-confidence visualisation: pipeline_confidence (amber, automated) and
  analyst_confidence (green, human-set) displayed independently
- Source quality table with NATO Admiralty A1-F6 ratings and relative-age timestamps
- Security headers middleware (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Strict CORS allowlist
- nginx reverse proxy with TLS via Let's Encrypt
- Docker Compose production configuration (--profile app for api/worker/web services)
- ProMED-mail RSS connector: country, region, and serotype extraction

---

## [0.1.0] — 2026-04-17

### Added
- Initial platform build
- Project structure: api/, worker/, web/, db/, docs/adr/, scripts/
- Docker Compose with PostgreSQL 16 + Redis 7
- Workspace pyproject.toml with ruff, mypy strict, bandit, pytest, coverage config
- Quality gate scripts: check.sh, format.sh, test.sh, bootstrap.sh
- PostgreSQL migrations:
  - 001_initial.sql: core schema (case_reports, qualification_scores, sources,
    source_quality_log, audit_log)
  - 002_seed_serotypes.sql: 12 orthohantaviruses (ANDV, PUUV, HTNV, SEOV, DOBV, SNV, +6)
  - 003_seed_sources.sql: initial 11 sources seeded with WHO, CDC, ECDC, PAHO, ProMED
- Source qualification module (worker/horizon_worker/core/):
  - nato.py: NATO Admiralty reliability (A-F) and credibility (1-6) scales
  - qualification.py: dual-confidence model (pipeline_confidence + analyst_confidence)
  - chain_of_custody.py: Berkeley Protocol hash per record
  - src_citation.py: ICD 206 Source Reference Citation
- ADR-0001: stack choice rationale
- ADR-0002: source qualification model algebra
  (PIPELINE_CONFIDENCE_CAP = 0.99, full corroboration and recency decay specification)
- API Dockerfile (Python 3.12-slim, non-root, uvicorn, healthcheck)
- Worker Dockerfile (Python 3.12-slim, non-root, celery + beat single process)
- Web Dockerfile (node 22-alpine, Vite dev server)

---

[Unreleased]: https://github.com/The79thUnit/Clearsky-Horizon/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/The79thUnit/Clearsky-Horizon/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/The79thUnit/Clearsky-Horizon/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/The79thUnit/Clearsky-Horizon/releases/tag/v0.1.0
