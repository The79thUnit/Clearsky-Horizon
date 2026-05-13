# HORIZON

Local-first hantavirus surveillance platform with audit-grade source qualification.

> Built by the 79th Unit. Independent of CLEARSKY production.
> No PII. UK GDPR Art 6 lawful basis: legitimate interests (public health information).

## What this is

A standalone tracker that ingests hantavirus outbreak reports from ~45 sources
(WHO, CDC, ECDC, PAHO, ProMED, national health ministries, peer-reviewed research,
genomic repositories, news, social) and presents them with:

- ICD 206 Source Reference Citations
- NATO Admiralty Scale reliability scores (A1 to F6)
- Dual confidence model (pipeline_confidence auto, analyst_confidence human)
- Berkeley Protocol chain-of-custody hash on every record

No competitor implements this. Source provenance is the wedge.

## Status

**Phase 1: Proof of Life.** See `PROJECT_MANAGEMENT.MD` for live status,
`CHANGELOG.md` for recent changes, `docs/adr/` for architecture decisions.

## Quick start

```bash
# bring up the stack (postgres + redis only at Phase 1 T-01)
./scripts/bootstrap.sh

# run quality gates
./scripts/check.sh

# tests only
./scripts/test.sh
```

## Stack

Python 3.12 + FastAPI + PostgreSQL 16 + Redis 7 + Celery + Vite + React 18 + TypeScript.
Docker Compose orchestrates locally. No Kubernetes.

## Layout

```
horizon/
  api/       FastAPI service, public read endpoints
  worker/    Celery worker, ingest pipeline, source qualification
  web/       Vite + React frontend
  db/        SQL migrations, seed data (sources inventory)
  docs/adr/  Architecture Decision Records
  scripts/   bootstrap, check, format, test
```

## Not for medical advice

This site is informational only. For diagnosis or care, contact a qualified clinician.
HORIZON is not affiliated with WHO, CDC, ECDC, PAHO, or any national health authority.
