# ADR-0001: Stack Choice for HORIZON

**Status:** Accepted
**Date:** 2026-05-11
**Decision-maker:** 79th Unit Limited
**Implementer:** 79th Unit engineering

## Context

HORIZON is a local-first public-health surveillance platform tracking hantavirus
outbreaks worldwide. It must:

- Ingest from ~45 heterogeneous sources (RSS, JSON, HTML, ArcGIS REST)
- Apply source qualification (ICD 206 SRC + NATO Admiralty + dual confidence)
- Serve a public web UI showing case lists, source quality, outbreak map
- Run on a single dev laptop locally with no cloud dependency
- Be skill-transferable from CLEARSKY so the operator does not learn a new stack
- Avoid coupling to CLEARSKY production so failure here does not affect CLEARSKY

## Options considered

### Option A: Match CLEARSKY stack (Python 3.12 + FastAPI + Postgres 16 + Vite/React/TS + Docker Compose)

Pros:
- Every CLEARSKY skill transfers. Same async patterns, same frontend conventions.
- Postgres permits adding PostGIS + pgvector later without a rewrite.
- Docker Compose deploys locally with one command.

Cons:
- Shares dependency surface area with CLEARSKY production. CVE patching affects both.
- Heavier than strictly necessary for a single-domain tracker.

### Option B: Lighter stack (SQLite + FastAPI + plain JS)

Pros:
- Smaller surface area. Can run without Docker.

Cons:
- Cannot do PostGIS / pgvector later. Frontend pattern diverges from CLEARSKY.
- Lower learning transfer.

### Option C: Node-only stack (Node + Express + Postgres + Next.js)

Pros:
- Single language across stack.

Cons:
- Discards all CLEARSKY Python skill. Different connector pattern from CLEARSKY's
  YAML connector library. Worker scheduling needs a separate solution.

## Decision

**Option A.** Match CLEARSKY stack: Python 3.12 + FastAPI + PostgreSQL 16 + Redis 7 +
Celery + Vite/React 18/TypeScript + Docker Compose.

No Kubernetes. No k3s. No CLEARSKY ontology dependency. Local-first via Docker
Compose. Per-service `Dockerfile` in `api/`, `worker/`, `web/`.

## Consequences

Pros (realised):
- Operator's CLEARSKY skill carries over 1:1
- Async patterns, dependency tooling, test framework identical
- Postgres permits adding PostGIS + pgvector later without a rewrite

Cons (accepted, mitigated):
- Dependency surface overlaps CLEARSKY -> patch both when CVEs hit
- Heavier than strictly necessary for a single-domain tracker

Mitigations:
- HORIZON declares its own `pyproject.toml` per service with pinned, audited deps
- Versions can drift from CLEARSKY if operationally useful
- No shared code modules between HORIZON and CLEARSKY (independence preserved)

## Related decisions

- ADR-0002 (forthcoming, P-1-T-03): Source qualification model algebra
- ADR-0003 (forthcoming, P-1-T-04): Connector framework (YAML-driven vs Python-class)
