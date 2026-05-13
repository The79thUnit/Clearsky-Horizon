# Changelog

All notable changes to HORIZON. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html). Status: pre-1.0, anything may change.

## [Unreleased]

### Added
- Project scaffold: directory structure, README.md, docs/adr/0001-stack-choice.md
- Docker Compose with PostgreSQL 16 + Redis 7 (api/worker/web services declared via --profile app)
- Workspace pyproject.toml with ruff + mypy strict + bandit + pytest + coverage config
- Quality gate scripts: scripts/check.sh, scripts/format.sh, scripts/test.sh, scripts/bootstrap.sh
- PROJECT_MANAGEMENT.MD ledger seeded with Phase 1 audit findings and plan
- Postgres migrations: 001_initial.sql (schema), 002_seed_serotypes.sql (12 orthohantaviruses),
  003_seed_sources.sql (11 sources, ProMED enabled)
- Source qualification module: NATO Admiralty scale (worker/horizon_worker/core/nato.py),
  dual confidence (qualification.py), Berkeley Protocol chain-of-custody (chain_of_custody.py),
  ICD 206 Source Reference Citation (src_citation.py)
- ADR-0002: source qualification model algebra (PIPELINE_CONFIDENCE_CAP = 0.99,
  corroboration +0.02/source cap +0.10, recency -0.001/day after 7-day grace cap -0.05)
- Connector framework: BaseConnector abstract class with fetch_and_parse + run lifecycle,
  ParsedItem dataclass, FetchResult dataclass
- ProMED-mail RSS connector with country + region + serotype extraction
- Celery worker + beat schedule (ProMED every 15 min by default) + ingest task that
  writes case_reports + qualification_scores + source_quality_log per fetch
- FastAPI public read-only API at port 8000: /health, /api/v1/cases, /api/v1/sources,
  OpenAPI 3.x docs at /api/docs, security headers middleware, strict CORS allowlist
- Vite + React 18 + TypeScript frontend at port 5173 with three tabs (Cases, Sources,
  Methodology), CLEARSKY design system, IBM Plex fonts, dual-confidence visualisation,
  source quality table with relative-age timestamps, footer with UK GDPR + not-medical-advice
- Test suite: 50 tests, all passing, 68.91% coverage (100% on core/ qualification modules)
- Worker Dockerfile (Python 3.12-slim, non-root user, celery + beat single process)
- API Dockerfile (Python 3.12-slim, non-root user, uvicorn, healthcheck)
- Web Dockerfile (node 22-alpine, Vite dev server for Phase 1 local-first)

### Quality gates (verified 2026-05-11)
- ruff check: all checks passed
- ruff format: 21 files formatted
- mypy --strict: success, no issues found in 15 source files
- bandit: 0 issues across 762 LOC
- pytest: 50 passed, coverage 68.91% (above 60% gate)
