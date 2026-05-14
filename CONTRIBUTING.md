# Contributing to HORIZON

HORIZON is maintained by 79th Unit Limited. Contributions are welcome in the
areas below.

---

## What we accept

| Type | Welcome |
|---|---|
| New source connectors | Yes — see below |
| Bug fixes (connector failures, parse errors, API issues) | Yes |
| Documentation improvements | Yes |
| New language support for detection (`text_utils.py`) | Yes |
| Frontend improvements (React/TypeScript) | Yes |
| Changes to the qualification model | **No** — requires an ADR and maintainer sign-off (see `docs/adr/0002-qualification-model.md`) |
| Changes to NATO Admiralty base confidence values | **No** — same requirement |

---

## Adding a source connector

1. Check `worker/horizon_worker/connectors/` for the existing pattern.
2. For RSS/Atom sources, subclass `RSSConnectorBase` — set `SOURCE_CODE`,
   `FEED_URL`, `KEYWORDS`, optionally `PARSER_VERSION` and `EXTRA_HEADERS`.
3. For HTML-scraped sources, subclass `BaseConnector` and implement
   `fetch_raw` and `parse`.
4. Add a migration in `db/migrations/` that `INSERT`s the source into the
   `sources` table with a NATO Admiralty rating and provenance notes.
5. Add a beat schedule entry in `worker/horizon_worker/celery_app.py`.
6. Write at least one test in `worker/tests/`.

Assign NATO Admiralty ratings honestly:
- **A/B** — official government health agencies, major wire services
- **C** — regional news, community health monitors
- **D/E** — social media, unverified forums

---

## Development setup

```bash
# Clone
git clone https://github.com/The79thUnit/Clearsky-Horizon.git
cd Clearsky-Horizon

# Start services
docker compose up -d

# Install Python dependencies
cd worker && pip install -r requirements.txt

# Run quality checks (must pass before submitting)
bash scripts/check.sh   # ruff + mypy --strict + bandit
bash scripts/test.sh    # pytest (60% coverage gate)
```

---

## Code standards

All code must pass the quality gate before a PR is accepted:

- **`ruff`** — zero lint issues
- **`mypy --strict`** — zero type errors across all source files
- **`bandit`** — zero security issues
- **`pytest`** — tests pass, coverage gate met

Run `bash scripts/check.sh` to verify all four before opening a PR.

---

## Submitting a pull request

1. Fork the repository.
2. Create a branch: `git checkout -b feat/your-connector-name`.
3. Make your changes and ensure all quality checks pass.
4. Open a pull request against `main` with a clear description of what
   source you have added and why it is relevant to hantavirus surveillance.

---

## Reporting data errors

If you believe a case report, confidence score, or source rating is
incorrect, open an issue using the **Data Correction** template rather
than submitting a PR directly. Data corrections require maintainer review
before any change is applied to the qualification pipeline.
