# HORIZON — Real-Time Hantavirus Surveillance

[![Live Platform](https://img.shields.io/badge/Live%20Platform-hantavirus.software-2d7ff9?style=flat-square)](https://hantavirus.software)
[![MIT Licence](https://img.shields.io/badge/Licence-MIT-00e87a?style=flat-square)](LICENSE)
[![Sources](https://img.shields.io/badge/Sources-65%2B%20authoritative-f59e0b?style=flat-square)](https://hantavirus.software)

Real-time outbreak surveillance for hantavirus pulmonary syndrome (HPS) and haemorrhagic fever
with renal syndrome (HFRS). HORIZON aggregates intelligence from 65+ authoritative sources,
qualifies every record with NATO Admiralty dual-confidence scoring, and presents live case
counts, serotype tracking, and geographic spread at [hantavirus.software](https://hantavirus.software).
Built during the 2026 MV Hondius Andes virus cluster — the first documented large-scale
hantavirus exposure on a cruise vessel. Includes the Oxford Kraemer Lab individual-level ANDV
line list (Dr Moritz Kraemer, Sam Scarpino, Andrew Rambaut / Nextstrain) — the highest
epidemiological resolution available for the MV Hondius outbreak.

---

## What is HORIZON?

HORIZON is an open-source, real-time hantavirus surveillance platform that aggregates and
qualifies intelligence from 65+ authoritative sources across Tier 1-3: WHO Disease Outbreak
News, CDC Health Alert Network, ECDC epidemiological updates, PAHO, RKI, RIVM, national
health ministries, peer-reviewed literature, genomic repositories, individual-level research
line lists, and open-source signals. Every ingested record is attributed, timestamped, and
scored before it reaches the dashboard.

HORIZON is the only public surveillance platform ingesting the Oxford Kraemer Lab
individual-level ANDV line list — a CC0 living dataset maintained by Dr Moritz Kraemer
(University of Oxford, Dept of Biology), Sam Scarpino, and Andrew Rambaut (University of
Edinburgh / Nextstrain) with 28-column per-person resolution covering symptom onset, outcome,
nationality, treatment, and Pathoplexus/GenBank accession IDs for every tracked case. This is
cross-referenced against WHO DON600 and national health authority press releases for every row.

Source qualification uses the NATO Admiralty dual-confidence model — the same framework
applied in intelligence analysis. Each record carries a pipeline_confidence score (automated,
based on source reliability and corroboration) and an analyst_confidence score (human-set,
immutable). The separation between machine confidence and human judgement is enforced at the
schema level and is never conflated in the UI.

HORIZON tracks all major serotypes: Andes virus (ANDV), Puumala (PUUV), Hantaan (HTNV),
Seoul (SEOV), Dobrava (DOBV), Sin Nombre (SNV), and 12 further orthohantaviruses. Each
record is linked to ICD-10/ICD-11 codes and carries a Berkeley Protocol chain-of-custody hash
for audit-grade provenance. This makes HORIZON suitable not only for situational awareness
but for rigorous post-hoc epidemiological review.

The platform was built in direct response to the 2026 MV Hondius outbreak — a hantavirus
pulmonary syndrome cluster among passengers on an Antarctic expedition cruise vessel, believed
to be the first documented case of large-scale Andes virus (ANDV) transmission in a
closed-vessel environment. HORIZON provides the open-source reference platform for tracking
that cluster and future hantavirus events worldwide.

---

## Live Platform

**[hantavirus.software](https://hantavirus.software)**

The live platform shows:

- Real-time case counts by serotype and region
- Outbreak timeline with source-qualified events
- Geographic spread overlays
- Source quality metrics per record (NATO Admiralty A1-F6)
- Dual-confidence visualisation: pipeline confidence (auto) vs analyst confidence (human)
- Methodology tab explaining the source qualification model

---

## Data Sources

HORIZON ingests from 53+ sources across three qualification tiers.

### Tier 1 — Official Authority (highest reliability)

Direct feeds from national and international public health bodies. Reliability score: A or B.

| Source | Feed Type |
|--------|-----------|
| WHO Disease Outbreak News (DON) | RSS / JSON |
| CDC Health Alert Network (HAN) | RSS |
| ECDC Communicable Disease Threats Report (CDTR) | HTML / PDF |
| ECDC Risk Assessments | HTML |
| ECDC Epidemiological Updates | HTML |
| PAHO (Pan American Health Organization) | RSS |
| RKI (Robert Koch Institut, Germany) | RSS / HTML |
| RIVM (Netherlands) | RSS / HTML |
| UKHSA (UK Health Security Agency) | RSS |
| PHAC (Public Health Agency of Canada) | RSS |
| SPF France (Sante Publique France) | HTML |
| FHM (Folkhalsomyndigheten, Sweden) | RSS |
| FHI (Folkehelseinstituttet, Norway) | RSS |
| ECDC Surveillance Atlas | API |
| WHO AFRO / AMRO / EURO / SEARO / WPRO regional offices | RSS |

### Tier 2 — High-Quality Secondary (peer-reviewed and curated)

Peer-reviewed literature, curated surveillance aggregators, and genomic repositories.
Reliability score: C or D.

| Source | Feed Type |
|--------|-----------|
| CDC Emerging Infectious Diseases (EID) | RSS |
| Eurosurveillance | RSS |
| PubMed (hantavirus MeSH queries) | API |
| bioRxiv / medRxiv preprints | API |
| CIDRAP (Center for Infectious Disease Research and Policy) | RSS |
| HealthMap | API |
| GDELT Global Disease Monitor | API |
| Google News (serotype-specific queries) | JSON |
| GBIF (rodent host species occurrence) | API |
| iNaturalist (rodent host observations) | API |
| NCBI GenBank — recent orthohantavirus sequences (reldate 14 days) | API |
| NCBI RefSeq — full Orthohantavirus reference genome set (HantaNet, CDC, PMC10675615) | API |
| Oxford Kraemer Lab — MV Hondius individual-level ANDV line list (CC0, Kraemer/Scarpino/Rambaut) | CSV |
| ProMED-mail | RSS |

### Tier 3 — Contextual and OSINT (signal amplification)

Open-source signals used to detect emerging clusters before Tier 1 confirmation.
Reliability score: E or F. Never used as sole basis for a claim.

| Source | Feed Type |
|--------|-----------|
| Reddit (r/medicine, r/epidemiology, outbreak threads) | API |
| Mastodon public health instances | API |
| Vessel AIS tracking (MV Hondius and similar) | AIS feed |
| Google Trends (hantavirus-related queries) | Trends API |

---

## Source Qualification Model

Every record ingested by HORIZON receives two independent confidence scores.

**pipeline_confidence** (automated) — computed from:
- Source reliability (NATO Admiralty A-F: A = completely reliable, F = reliability cannot be judged)
- Source credibility (NATO Admiralty 1-6: 1 = confirmed, 6 = truth cannot be judged)
- Corroboration: +0.02 per additional independent source, capped at +0.10
- Recency decay: -0.001 per day after a 7-day grace period, floor -0.05
- Hard cap: 0.99 (certainty is never claimed algorithmically)

**analyst_confidence** (human-set) — set by a qualified analyst after review. Immutable once
set. Displayed separately in the UI (green indicator). Pipeline confidence is amber. The two
are never merged, averaged, or substituted for each other.

This model is documented formally in `docs/adr/0002-source-qualification-model.md`.

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.12), uvicorn, async SQLAlchemy |
| Task queue | Celery + Redis 7, beat scheduler |
| Database | PostgreSQL 16, pg_trgm, pgcrypto |
| Frontend | React 18 + TypeScript + Vite |
| UI framework | Custom design system (IBM Plex Mono/Sans) |
| Infrastructure | Docker Compose, nginx, Let's Encrypt TLS |
| Data connectors | 65+ RSS / JSON / HTML / API / CSV scrapers |
| Vessel tracking | AIS integration (MV Hondius cluster) |
| Source qualification | NATO Admiralty scale, Berkeley Protocol CoC hashes |
| Quality gates | ruff, mypy --strict, bandit, pytest (60% coverage gate) |

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- No other local dependencies required

### Run locally

```bash
git clone https://github.com/The79thUnit/Clearsky-Horizon.git
cd Clearsky-Horizon

# Copy environment template
cp .env.production.example .env

# Start the full stack (PostgreSQL, Redis, API, worker, frontend)
docker compose up -d

# Verify all services are healthy
docker compose ps
```

The frontend is available at `http://localhost:5173`.
The API is at `http://localhost:8000` with OpenAPI docs at `http://localhost:8000/api/docs`.

### Run quality gates

```bash
./scripts/check.sh    # ruff + mypy + bandit + pytest
./scripts/format.sh   # ruff format
./scripts/test.sh     # pytest only
```

---

## Architecture

```
horizon/
  api/        FastAPI service — public read-only endpoints
  worker/     Celery worker — ingest pipeline, source qualification, connectors
  web/        Vite + React 18 + TypeScript frontend
  db/         SQL migrations, serotype and source seed data
  docs/adr/   Architecture Decision Records
  scripts/    Development and CI scripts
```

Architecture decisions are documented in `docs/adr/`. Key ADRs:

- `0001-stack-choice.md` — rationale for Python/FastAPI/React/PostgreSQL
- `0002-source-qualification-model.md` — full algebra for the NATO Admiralty model

---

## Security

- The API is public and **read-only**. No write endpoints are exposed without authentication.
- All environment variables (database credentials, API keys, secrets) are externally injected via `.env`. No credentials exist in source code.
- An `.env.production.example` template is provided with placeholder values only.
- Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options) are enforced at the nginx and API middleware layers.
- Bandit static analysis is part of the standard quality gate and must pass at 0 issues.

---

## Not medical advice

HORIZON is an informational surveillance tool only. It is not a diagnostic system and does not
provide medical advice. For clinical guidance, contact a qualified healthcare professional.
HORIZON is not affiliated with WHO, CDC, ECDC, PAHO, or any national health authority.

---

## Licence

MIT. See [LICENSE](LICENSE).

---

*Built by the 79th Unit. Keywords: hantavirus, Andes virus, ANDV, hantavirus pulmonary syndrome, HPS, haemorrhagic fever with renal syndrome, HFRS, Puumala, Hantaan, Seoul virus, Sin Nombre, outbreak surveillance, real-time epidemiology, MV Hondius 2026, cruise ship hantavirus, open-source surveillance platform, Oxford Kraemer Lab, individual line list, research linelist, HantaNet, NCBI RefSeq, genomic reference, Andrew Rambaut, Nextstrain, Moritz Kraemer.*
