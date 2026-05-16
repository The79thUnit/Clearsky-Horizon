# HORIZON SEO submission + diagnostic checklist

> Owner: 79th Unit Limited (Phoenix Valentino)
> Site: <https://hantavirus.software/>
> Updated: 16 May 2026

This file is the **operator checklist** for SEO work that can't be done from
inside the codebase (account auth, manual form submissions, human review).
The on-page surface is already automated; what's listed below requires a
human in the loop.

Run order top-to-bottom for a first-time setup. After that, only Section 6
(Search Console diagnostic) needs to be a recurring task.

---

## 1. Google Search Console (highest priority)

**Goal:** see what Google has actually indexed, what queries we rank for, and
what's blocked.

1. Sign in at <https://search.google.com/search-console/> as
   `abscondituseminus@gmail.com` (or director@79thunit.co.uk if that's
   verified instead).
2. **Add property** → "URL prefix" → `https://hantavirus.software/` →
   Continue.
3. **Verify ownership.** Recommended method: **HTML tag** (paste into
   `web/index.html` `<head>`). Alternative: TXT record on the DNS zone.
4. **Submit sitemaps** under Sitemaps → Add a new sitemap, one at a time:
   - `sitemap.xml`
   - `news-sitemap.xml`
5. **Diagnostic queries to run on Day 1** (Coverage + Performance):
   - **Coverage → Indexed** count vs. submitted count. If indexed < 30% of
     submitted after 14 days, escalate.
   - **Coverage → Not indexed** breakdown. Common false-positives we expect
     to see: `Discovered - currently not indexed` (crawl-budget queue,
     normal), `Crawled - currently not indexed` (Google has the page but
     decided not to index — content quality signal, investigate).
   - **Performance → Queries** sorted by impressions descending. If the top
     queries don't include "hantavirus tracker", "hantavirus outbreak",
     "MV Hondius", we're ranking for the wrong things and need on-page
     fixes.
   - **Performance → Pages** sorted by clicks descending. Confirm the
     homepage is the top clicked URL. If not, we have a canonical or
     internal-linking problem.
6. **Request indexing** for these URLs (URL Inspection → Request indexing).
   Limit is 10/day per property:
   - `https://hantavirus.software/`
   - `https://hantavirus.software/outbreaks/mv-hondius-2026`
   - `https://hantavirus.software/hantavirus/2026`
   - `https://hantavirus.software/hantavirus/andes-virus`
   - `https://hantavirus.software/timeline`
   - `https://hantavirus.software/chronology`
7. **Set preferred URL parameters** under Settings → Crawl stats. None
   currently used in canonical paths, so leave defaults.

**Recurring**: once a week, check Performance → Queries for new ranking
queries. New rankings for high-volume queries are the leading indicator we
need to expand the relevant page.

---

## 2. Bing Webmaster Tools

Already federated via IndexNow (URLs submitted on every `ping_indexers.py`
run), but the dashboard view is worth verifying.

1. <https://www.bing.com/webmasters/> → sign in (same Microsoft account
   used for other 79th Unit services).
2. Import the verified property from Google Search Console (Bing supports
   this directly under "Import from GSC" — saves re-verifying ownership).
3. Submit `sitemap.xml`.
4. Configure crawl rate to **High** (we're a fresh data feed).
5. Set the IndexNow key: `59d765645bcc5c9d796c94bf59063fe5` (already live
   at <https://hantavirus.software/indexnow-keyfile> and in the
   `<meta name="indexnow">` tag).

---

## 3. Wikidata submission (one-shot)

See `docs/wikidata-submission.md` for the full procedure. After the QIDs
come back from QuickStatements:

```bash
# On the prod VPS (91.134.255.231) — add to /opt/horizon/.env or systemd:
WIKIDATA_ORG_QID=Qxxxxx       # 79th Unit Limited
WIKIDATA_DATASET_QID=Qyyyyy   # HORIZON dataset
# Then:
docker compose restart horizon-api
```

The Organization JSON-LD `sameAs` array will automatically include the
new URLs on every server-rendered SEO page.

**Verify** the QIDs are picked up:

```bash
curl -A "Googlebot/2.1" https://hantavirus.software/ | grep -o 'wikidata.org/wiki/Q[0-9]\+'
```

Should print at least both QIDs.

---

## 4. re3data.org submission (one-shot, free)

re3data is the global registry of research data repositories. A re3data
record gives us:

- A canonical citation pointer used by every academic citation manager.
- An authority backlink (PR ~9) directly into the dataset record.
- Inclusion in DataCite Commons, OpenAIRE, and the Council of European
  Social Science Data Archives discovery graphs.

**Process** (no fees, takes 2-4 weeks for editor review):

1. Go to <https://www.re3data.org/suggest/> (Suggest a Repository).
2. Fill the form with:
   - **Repository Name**: `HORIZON Hantavirus Outbreak Surveillance Dataset`
   - **URL**: `https://hantavirus.software/`
   - **Description**: copy the Dataset JSON-LD `description` from
     `https://hantavirus.software/data` (it's the canonical text).
   - **Subjects**: 205 Public Health & Health Services; 304 Microbiology,
     Virology and Immunology; 205-21 Epidemiology.
   - **Country**: United Kingdom.
   - **Institution**: 79th Unit Limited (CRN 17133814).
   - **Persistent Identifier**: leave blank (no DOI yet — add later when
     we get DataCite Membership).
   - **API**: yes — REST + OpenAPI at
     `https://hantavirus.software/api/openapi.json`.
   - **Standardised Metadata**: DCAT-AP — point at
     `https://hantavirus.software/api/v1/meta/dcat`.
   - **Licence**: CC BY 4.0.
   - **Submitter email**: `clearsky@79thunit.co.uk`.
3. Submit. re3data editorial team reviews within 2-4 weeks. Once
   accepted, record the re3data ID (e.g. `r3d100000000`).
4. Add the re3data URL to the homepage Dataset JSON-LD `sameAs` array:
   edit `api/horizon_api/routers/seo.py` `homepage_dataset_schema` and
   add `"sameAs": ["https://www.re3data.org/repository/r3dXXXXXXXXX"]`.

---

## 5. Google Dataset Search

No submission needed — Google Dataset Search crawls schema.org `Dataset`
JSON-LD automatically. We declare the Dataset on:
- `/` (homepage, since 16 May 2026)
- `/data` (since launch)
- Every sub-sitemap is reachable from `sitemap.xml`.

**Verify discovery** ~7-14 days after a Search Console URL Inspection
re-submit:

1. Go to <https://datasetsearch.research.google.com/>.
2. Search "HORIZON hantavirus" or "hantavirus surveillance dataset".
3. Confirm we appear, with the CC BY 4.0 licence chip and the right
   author attribution (79th Unit Limited).

If not appearing after 21 days, run the Rich Results Test:
<https://search.google.com/test/rich-results> on
`https://hantavirus.software/` and confirm the Dataset block parses
cleanly.

---

## 6. DataCite (deferred — costs money)

DataCite minting of dataset DOIs requires a Member or Direct Member
account. **DataCite Direct Membership for SMEs/non-profits is currently
£1,615/yr or $2,025/yr**. Defer unless we hit the threshold where a
formal DOI becomes worth it (≥100 citations expected, or a
peer-reviewed publication referencing the dataset).

Free alternative for now: Zenodo, which mints DOIs gratis and is
DataCite-backed. Workflow:

1. <https://zenodo.org/> → sign in via GitHub (`AbsconditusEminus`).
2. Upload → New upload → Dataset.
3. Title: "HORIZON Hantavirus Outbreak Surveillance Dataset (snapshot
   YYYY-MM-DD)".
4. Description: copy from homepage Dataset JSON-LD.
5. Upload `cases.ndjson` snapshot from
   `https://hantavirus.software/api/v1/cases/bulk/ndjson`. Cap at 50 GB
   per upload.
6. License: CC BY 4.0.
7. Publish. Zenodo mints a DOI — record it and add to the homepage
   Dataset JSON-LD `identifier` field.

Refresh quarterly. Each snapshot gets a new DOI; previous DOIs remain
valid.

---

## 7. Backlink-friendly directories (free, low effort)

For each, submit the homepage URL + a one-sentence description.

- [ ] **Awesome Public Datasets** — open a PR adding HORIZON to the
      `Public Health` section at
      <https://github.com/awesomedata/awesome-public-datasets>.
- [ ] **Awesome OSINT** — PR to `Surveillance / Public Health` section at
      <https://github.com/jivoi/awesome-osint>.
- [ ] **EU Open Data Portal** — submit at <https://data.europa.eu/> →
      Suggest dataset. Free, manual review.
- [ ] **HealthData.gov** (if US-focused mirror added later) — N/A for now.
- [ ] **Knoema Public Data Marketplace** — free submission, indexed by
      Google Dataset Search separately.
- [ ] **CKAN.net** — register the OpenAPI as a CKAN-compatible dataset
      (we already serve DCAT-AP).

---

## 8. Press / journalist outreach (one-shot)

The MV Hondius story is the most-searched hantavirus topic of 2026 and we
have unique data (live country counts, NATO-scaled source provenance, the
Oxford Kraemer Lab line list). One decent news mention is worth months of
on-page SEO.

Pitch targets (cold, expect 5-10% response):

- BBC Health (Helen Briggs, James Gallagher).
- The Guardian Health (Jessica Glenza, Sarah Boseley).
- Stat News (Helen Branswell — outbreak specialist).
- New York Times Public Health (Apoorva Mandavilli).
- BNO News (Twitter-first, sharp on outbreaks).

Pitch should lead with the *unique angle* (cruise-ship vector, first
ever) and the *data value* (we're the only live tracker with NATO-scaled
provenance + Oxford Kraemer line list integration). Offer pre-publication
embargo data on request. **Do NOT** offer to write a guest piece — too
fluffy and journalists hate it.

Draft email template lives at
`data/draft-emails-for-review.md`  (admin workstation only — kept off
this repo for privacy).

---

## 9. Quick verification script

After any of the above, run:

```bash
python scripts/ping_indexers.py            # IndexNow + Google sitemap ping
python scripts/ping_indexers.py --all      # full sitemap (10k URL cap)
```

For a one-off URL after editing a page:

```bash
python scripts/ping_indexers.py --url https://hantavirus.software/outbreaks/mv-hondius-2026
```
