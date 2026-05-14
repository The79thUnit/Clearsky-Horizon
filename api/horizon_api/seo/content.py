"""Editorial prose for SEO topic-cluster pages.

Every paragraph here is original wording grounded in WHO/CDC/ECDC factsheets,
peer-reviewed sources, and the HORIZON dataset itself. No copied chunks
from external publications, no fabricated claims. We cite sources by name
("per WHO DON 600", "per CDC Yellow Book 2024") so claims are auditable.

These pages do four things at once:

  1. Rank for high-intent hantavirus search terms by being the most rigorous,
     citation-dense, internally-linked page on the public internet.
  2. Feed AI search (Perplexity, ChatGPT search, Gemini, Claude) — clean
     factual prose with named-entity density is exactly what these crawlers
     extract.
  3. Provide an honest, public-health-useful resource. We are a UK OSINT
     consultancy and this is not medical advice — we say so on every page.
  4. Reinforce E-E-A-T (Experience, Expertise, Authority, Trust) by linking
     out to WHO/CDC/ECDC/PAHO authoritative pages and showing methodology.
"""

from __future__ import annotations

from .common import SEROTYPES, esc


# ---------------------------------------------------------------------------
# Reusable building blocks
# ---------------------------------------------------------------------------


_NOT_MEDICAL_ADVICE = (
    '<aside class="callout"><strong>Not medical advice.</strong> '
    'HORIZON is a public-health surveillance and OSINT platform. '
    'If you are unwell, contact a clinician or your local public-health '
    'authority. See '
    '<a href="https://www.cdc.gov/hantavirus/" rel="external">CDC Hantavirus</a> '
    'or <a href="https://www.who.int/news-room/fact-sheets/detail/hantavirus-disease" rel="external">WHO Hantavirus</a>.'
    '</aside>'
)


_CTA_LIVE_MAP = (
    '<p><a class="cta" href="/">Open the live outbreak map →</a></p>'
)


def _related_serotypes_grid(exclude_slug: str | None = None) -> str:
    """Render a small card grid of serotypes, optionally excluding one."""
    rows = [s for s in SEROTYPES if s["slug"] != exclude_slug][:6]
    parts = ['<div class="cards">']
    for s in rows:
        parts.append(
            f'<article class="card"><h3>{esc(s["name"])}</h3>'
            f'<p class="kv">{esc(s["syndrome"])} · CFR {esc(s["cfr"])}</p>'
            f'<p>{esc(s["summary"])[:180]}…</p>'
            f'<a class="more" href="/hantavirus/{esc(s["slug"])}">Read more on {esc(s["code"])} →</a>'
            f'</article>'
        )
    parts.append('</div>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# /hantavirus — overview hub
# ---------------------------------------------------------------------------


HANTAVIRUS_HUB_BODY = f"""
<p class="lead">
Hantaviruses are a family of rodent-borne RNA viruses (genus
<em>Orthohantavirus</em>, family <em>Hantaviridae</em>) capable of causing
two distinct clinical syndromes in humans: <strong>Hantavirus Pulmonary
Syndrome (HPS)</strong>, predominantly in the Americas, and
<strong>Haemorrhagic Fever with Renal Syndrome (HFRS)</strong>,
predominantly across Eurasia. HORIZON tracks every known orthohantavirus
of public-health concern and aggregates outbreak signal from WHO, CDC,
ECDC, PAHO, ProMED, peer-reviewed literature, and open news — with full
audit-grade source provenance on every record.
</p>

{_NOT_MEDICAL_ADVICE}

<h2>What is hantavirus?</h2>
<p>
Hantaviruses are tri-segmented negative-sense single-stranded RNA viruses
in the family <em>Hantaviridae</em>. Each serotype is associated with a
specific rodent reservoir species — host specificity is so strong that
co-divergence with the rodent lineage is one of the dominant evolutionary
features of the family. Humans become infected when they inhale virus
aerosolised from rodent excreta (urine, faeces, saliva) or rarely via
direct contact with infected animals. With one exception — Andes virus —
hantaviruses do not transmit person-to-person.
</p>

<h3>Active outbreak tracking</h3>
<p>
The 2026 <a href="/outbreaks/mv-hondius-2026">MV Hondius cluster</a> is the
flagship investigation currently surfaced on the HORIZON live map. The
cluster traces back to suspected pre-departure exposure during a wildlife
excursion near Ushuaia (Tierra del Fuego, Argentina), with Andes virus
(ANDV) confirmed by PCR on the South African case. Authoritative counts
come from WHO Disease Outbreak News 2026-DON600 and ECDC surveillance
updates; news corroboration is layered with NATO Admiralty Scale ratings
and dual confidence scoring.
</p>

{_CTA_LIVE_MAP}

<h2>Serotypes tracked</h2>
<p>
HORIZON surfaces a dedicated page per orthohantavirus serotype of
documented public-health concern. Each page details the reservoir species,
endemic range, syndrome type, case-fatality estimate, transmission
profile, and links to authoritative WHO/CDC sources.
</p>

{_related_serotypes_grid()}

<p><a href="/hantavirus/andes-virus">All 12 tracked serotypes →</a></p>

<h2>The two clinical syndromes</h2>

<h3>Hantavirus Pulmonary Syndrome (HPS)</h3>
<p>
HPS is the more lethal presentation, with overall case-fatality between
30 and 50 percent for Andes virus and around 38 percent for Sin Nombre
virus per CDC surveillance. After a 1–8 week incubation, patients
develop a brief flu-like prodrome (fever, myalgia, headache) followed by
rapid cardiopulmonary collapse with non-cardiogenic pulmonary oedema and
shock. The defining lab finding is thrombocytopenia plus left-shifted
white-cell count with circulating immunoblasts.
</p>

<h3>Haemorrhagic Fever with Renal Syndrome (HFRS)</h3>
<p>
HFRS is associated with Old World serotypes — Hantaan virus and
Dobrava-Belgrade virus cause severe disease (CFR 5 to 15 percent);
Puumala virus and Seoul virus cause milder presentations
(CFR less than 2 percent). The classical five-stage clinical course
(febrile, hypotensive, oliguric, diuretic, convalescent) is most
recognisable in Hantaan-virus disease. Acute kidney injury is the
defining renal feature.
</p>

<p>
A detailed breakdown is available on the
<a href="/hantavirus/symptoms">hantavirus symptoms</a>,
<a href="/hantavirus/transmission">transmission</a>,
<a href="/hantavirus/prevention">prevention</a>, and
<a href="/hantavirus/treatment">treatment</a> pages.
</p>

<h2>Geographic distribution</h2>
<p>
HORIZON maintains <a href="/countries">per-country</a> pages with case
chronology and authoritative-source linkage. Recognised endemic regions
include:
</p>
<ul>
<li><strong>Americas</strong> — Argentina, Chile, USA (Four Corners),
Canada, Brazil, Panama, Bolivia, Paraguay (HPS-causing New World
hantaviruses including Andes, Sin Nombre, Bayou, Laguna Negra,
Black Creek Canal, and Choclo).</li>
<li><strong>Europe and western Russia</strong> — Finland, Sweden,
Germany, France, Belgium, Russia, the Balkans
(Puumala virus, Dobrava-Belgrade virus, Saaremaa virus, Tula virus).</li>
<li><strong>East Asia</strong> — China, Korean peninsula, Russian Far
East, Japan (Hantaan virus, Seoul virus).</li>
<li><strong>Global</strong> — Seoul virus circulates wherever its
<em>Rattus</em> reservoirs do, which is effectively everywhere ports,
agriculture, and urban density support rat populations.</li>
</ul>

<h2>Methodology and source provenance</h2>
<p>
Every record on HORIZON carries an
<a href="/methodology">audit-grade citation</a> including:
</p>
<ul>
<li><strong>ICD 206 Source Reference Citation</strong> — the formal
intelligence-community citation format.</li>
<li><strong>NATO Admiralty Scale</strong> — reliability (A–F) and
credibility (1–6) per AJP-2.1.</li>
<li><strong>Dual confidence model</strong> — separate pipeline (auto)
and analyst (human) confidence so statistical noise cannot be conflated
with vetted intelligence.</li>
<li><strong>Berkeley Protocol chain-of-custody</strong> — SHA-256 hash
of fetched content so any record is independently verifiable.</li>
</ul>

<p>
Browse the <a href="/sources">live source registry</a> for the current
status of every WHO, CDC, ECDC, PAHO, ProMED, national-authority,
peer-reviewed-journal, and aggregator feed in the pipeline.
</p>

<h2>Open data — CC BY 4.0</h2>
<p>
All HORIZON data is published under the
<a href="https://creativecommons.org/licenses/by/4.0/" rel="external license">Creative Commons Attribution 4.0 International</a>
licence. Mirror it, scrape it, index it, train on it — attribution to
79th Unit Limited is the only requirement. JSON endpoints are documented
in our <a href="/api/openapi.json">OpenAPI schema</a>:
</p>
<ul>
<li><code>GET /api/v1/cases</code> — ingested case reports with qualification scores</li>
<li><code>GET /api/v1/incidents</code> — authoritative outbreak counts and ontology</li>
<li><code>GET /api/v1/sources</code> — source registry with quality telemetry</li>
<li><code>GET /api/v1/meta/stats</code> — global counters</li>
<li><code>GET /api/v1/meta/events</code> — chronological event feed</li>
</ul>

<p>
Or subscribe via <a href="/rss.xml">RSS</a>,
<a href="/atom.xml">Atom</a>, or <a href="/feed.json">JSON Feed</a>.
</p>

{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /hantavirus/symptoms
# ---------------------------------------------------------------------------


SYMPTOMS_BODY = f"""
<p class="lead">
Hantavirus disease presents with two distinct clinical syndromes
depending on which serotype caused the infection. Both share an early
flu-like prodrome lasting 3 to 7 days, then diverge sharply: <strong>HPS</strong>
progresses to cardiopulmonary failure; <strong>HFRS</strong> progresses to
renal failure with bleeding. Incubation is 1 to 8 weeks.
</p>

{_NOT_MEDICAL_ADVICE}

<h2>Stage 1 — Prodrome (days 1 to 7)</h2>
<p>
Both syndromes begin similarly and are easily mistaken for influenza,
COVID-19, viral gastroenteritis, dengue, leptospirosis, scrub typhus,
or early sepsis. Typical features per CDC and WHO:
</p>
<ul>
<li>High-grade fever (often 39–40°C)</li>
<li>Severe muscle aches (myalgia), particularly thighs, hips, and lower back</li>
<li>Headache</li>
<li>Fatigue and malaise</li>
<li>Gastrointestinal symptoms — nausea, vomiting, abdominal pain, diarrhoea</li>
<li>Dizziness, chills</li>
</ul>

<h2>Hantavirus Pulmonary Syndrome (HPS) — Stage 2</h2>
<p>
4 to 10 days after symptom onset, HPS rapidly transitions to the
cardiopulmonary phase. The defining feature is non-cardiogenic
pulmonary oedema with shock. CDC reports overall HPS case-fatality
at 38 percent for Sin Nombre virus and 30 to 50 percent for Andes virus.
Hallmarks:
</p>
<ul>
<li>Cough and progressive shortness of breath</li>
<li>Tachypnoea and hypoxia</li>
<li>Bilateral pulmonary infiltrates on chest radiograph</li>
<li>Hypotension and circulatory collapse</li>
<li>Thrombocytopenia (platelet count below 150,000/μL)</li>
<li>Haemoconcentration and lactic acidosis</li>
<li>Left-shifted white-cell count with circulating immunoblasts
(hantavirus &quot;triad&quot; on blood smear)</li>
</ul>

<h2>Haemorrhagic Fever with Renal Syndrome (HFRS) — Stage 2 to 5</h2>
<p>
HFRS classically progresses through five stages, each lasting hours to
days. CFR depends on serotype: Hantaan and Dobrava-Belgrade 5 to 15
percent; Puumala under 1 percent.
</p>
<table class="facts">
<tr><th>Stage</th><th>Features</th></tr>
<tr><th>Febrile (days 3–7)</th><td>Fever, flushing, conjunctival injection, petechial rash, retro-orbital pain</td></tr>
<tr><th>Hypotensive (hours to 2 days)</th><td>Vascular leak, shock, tachycardia, oliguria onset</td></tr>
<tr><th>Oliguric (days 2–10)</th><td>Acute kidney injury, fluid overload, haemorrhagic complications (epistaxis, haematemesis, intracranial bleed in severe cases)</td></tr>
<tr><th>Diuretic (days 4 onwards)</th><td>Polyuria as renal function recovers; fluid/electrolyte management critical</td></tr>
<tr><th>Convalescent (weeks)</th><td>Gradual return to baseline; some patients have persistent renal impairment</td></tr>
</table>

<h2>When to seek care</h2>
<p>
Anyone with the prodromal symptoms above plus a credible exposure
history — rural rodent contact, recent travel to an endemic area
(<a href="/countries">see country pages</a>), occupational exposure
(camping, hunting, conservation, agricultural work, cleaning rodent-infested
structures) — should seek urgent medical assessment. Early intensive
supportive care, particularly for HPS, is the single strongest
predictor of survival. There is no specific antiviral, but ribavirin
has shown benefit in early HFRS (less in HPS).
</p>

<h2>Differential diagnosis to consider</h2>
<p>
Clinicians evaluating a suspected hantavirus case in 2026 should consider:
influenza A and B, COVID-19, viral pneumonia, atypical bacterial
pneumonia (Legionella, Mycoplasma), leptospirosis, dengue haemorrhagic
fever, scrub typhus, severe sepsis, Plasmodium falciparum malaria,
pulmonary embolism, and early HELLP syndrome in pregnancy. The
hantavirus blood smear triad (thrombocytopenia, left shift,
immunoblasts) plus haemoconcentration is highly suggestive.
</p>

{_related_serotypes_grid()}

<p><a href="/hantavirus">← Back to hantavirus overview</a></p>
{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /hantavirus/transmission
# ---------------------------------------------------------------------------


TRANSMISSION_BODY = f"""
<p class="lead">
Hantaviruses are <strong>rodent-borne</strong>. Humans are accidental,
dead-end hosts for almost every serotype. Transmission is overwhelmingly
via inhalation of aerosolised rodent excreta in enclosed spaces.
<strong>Andes virus is the sole exception</strong> — it has documented
person-to-person transmission, primarily between close household contacts.
</p>

{_NOT_MEDICAL_ADVICE}

<h2>Primary route: rodent-to-human aerosol</h2>
<p>
Infected rodents shed virus in urine, faeces, and saliva. When
dried excreta is disturbed — by sweeping, vacuuming, or vehicle
movement in a barn or cabin — virus-laden particles aerosolise and
can be inhaled. Risk is highest in poorly-ventilated, rodent-infested
structures: cabins, outbuildings, grain stores, agricultural sheds,
abandoned vehicles, military barracks, and rodent-occupied apartments.
</p>

<h2>Secondary routes</h2>
<ul>
<li><strong>Direct rodent bite</strong> — rare, but documented for
Seoul virus from pet rats in the US and UK.</li>
<li><strong>Mucous-membrane contact</strong> — eye-rubbing after
handling rodent material is a plausible inoculation route.</li>
<li><strong>Contaminated food</strong> — possible but rare; not a
mainstream transmission mode.</li>
<li><strong>Laboratory exposure</strong> — historical lab outbreaks
during early hantavirus research; modern BSL-3 containment makes this
rare.</li>
</ul>

<h2>Andes virus person-to-person transmission</h2>
<p>
Andes virus (ANDV) is the only orthohantavirus with documented P2P
transmission. Cluster evidence comes from:
</p>
<ul>
<li><strong>El Bolsón, Argentina (1996)</strong> — Wells et al. described
20 cases linked through close-contact transmission, including healthcare
workers and household contacts.</li>
<li><strong>Coyhaique, Chile (2018–2019)</strong> — sequenced clusters
showing inter-person transmission between non-household close contacts.</li>
<li><strong>MV Hondius cluster (2026)</strong> — actively monitored.
Onboard spread is suspected given the long voyage and shared crew
quarters; HORIZON ontology models this explicitly under the
&quot;transmitted_to&quot; relationship between the index couple.</li>
</ul>
<p>
P2P transmission appears to require close, prolonged contact rather
than fleeting exposure. Universal precautions, droplet isolation for
known/suspected ANDV cases, and respirator use during aerosol-generating
procedures are recommended by Argentine and Chilean health authorities
during active outbreaks.
</p>

<h2>What does NOT transmit hantavirus</h2>
<ul>
<li>Mosquitoes, ticks, or any arthropod vector — hantaviruses are
<em>not</em> arboviruses despite the &quot;haemorrhagic fever&quot;
naming.</li>
<li>Casual contact with HPS/HFRS patients (except for ANDV close
contacts) — this is not an airborne respiratory virus in the
SARS-CoV-2 sense.</li>
<li>Food prepared in non-rodent-contaminated kitchens.</li>
<li>Blood transfusion (no documented cases).</li>
<li>Sexual transmission (no documented cases).</li>
</ul>

<h2>Reservoir species — primary rodent hosts</h2>
<table class="facts">
<tr><th>Serotype</th><th>Reservoir</th><th>Region</th></tr>
{"".join(f'<tr><th>{esc(s["code"])}</th><td>{esc(s["reservoir"])}</td><td>{esc(s["endemic"])}</td></tr>' for s in SEROTYPES[:8])}
</table>

<p>
See <a href="/hantavirus/prevention">prevention</a> for evidence-based
measures to reduce exposure risk in endemic regions.
</p>

<p><a href="/hantavirus">← Back to hantavirus overview</a></p>
{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /hantavirus/prevention
# ---------------------------------------------------------------------------


PREVENTION_BODY = f"""
<p class="lead">
No licensed hantavirus vaccine is available in Europe or North America.
The only authorised vaccine — South Korea's <strong>Hantavax</strong> —
covers Hantaan virus. Prevention is therefore <strong>exposure
control</strong>: reducing rodent populations, suppressing aerosol
generation when cleaning, and using appropriate respiratory protection.
</p>

{_NOT_MEDICAL_ADVICE}

<h2>Reduce rodent presence around homes</h2>
<ul>
<li>Seal entry points larger than 6 mm with steel wool plus caulk; cover vents and chimneys with hardware cloth.</li>
<li>Remove food sources: store grain and pet food in sealed metal or glass containers; remove fallen fruit; secure rubbish.</li>
<li>Remove harbourage: cut grass and brush within 30 m of structures; elevate woodpiles at least 30 cm off the ground and 30 m from the house.</li>
<li>Use snap traps continuously; rotate locations; bait with peanut butter or sunflower seeds.</li>
<li>Avoid live-capture-and-release for confirmed Peromyscus or Apodemus — release sites become re-infestation sources.</li>
</ul>

<h2>Safe cleaning of rodent-contaminated areas</h2>
<p>
Per CDC procedures, <strong>never sweep or vacuum dry excreta</strong> — both
aerosolise virus. The protocol:
</p>
<ol>
<li>Ventilate the space for at least 30 minutes before entry; leave doors and windows open.</li>
<li>Wear an N95/FFP3 respirator, rubber or latex gloves, and goggles.</li>
<li>Saturate excreta and contaminated surfaces with 1:10 household bleach (5,000 ppm) or an EPA-registered disinfectant; allow 5 minutes' contact.</li>
<li>Wipe up with paper towels; bag waste; double-bag and seal.</li>
<li>Mop the floor with disinfectant; do not vacuum even after disinfection.</li>
<li>Wash gloved hands before removing gloves; wash bare hands after; launder clothes in hot water.</li>
</ol>

<h2>Outdoor and occupational exposure</h2>
<ul>
<li>Avoid sleeping near rodent burrows or nests when camping; use ground tarps; air out cabins before sleeping.</li>
<li>Inspect agricultural machinery and grain stores before entry; wear an N95/FFP3 if disturbing accumulated dust.</li>
<li>Conservation, wildlife, and pest-control workers should follow site-specific safety plans; HPS has been documented in field biologists handling Peromyscus and Apodemus species.</li>
</ul>

<h2>Travel precautions for endemic regions</h2>
<p>
HORIZON country pages document recent activity for travellers heading to
endemic areas:
<a href="/countries/AR">Argentina</a>, <a href="/countries/CL">Chile</a>,
<a href="/countries/US">United States</a> (Four Corners),
<a href="/countries/DE">Germany</a>, <a href="/countries/FI">Finland</a>,
<a href="/countries/CN">China</a>, <a href="/countries/KR">South Korea</a>.
Standard advice: avoid rodent-occupied buildings, avoid disturbing
rodent nests during hiking or excursions, prefer modern accommodation,
and report rodent infestation to lodge staff.
</p>

<h2>Vaccine status (2026)</h2>
<table class="facts">
<tr><th>Vaccine</th><th>Coverage</th><th>Region</th></tr>
<tr><th>Hantavax (Green Cross)</th><td>Hantaan virus</td><td>South Korea — licensed</td></tr>
<tr><th>Hantavax-II</th><td>Hantaan + Seoul</td><td>South Korea — licensed</td></tr>
<tr><th>Various DNA/mRNA candidates</th><td>SNV / ANDV / multi-serotype</td><td>Pre-clinical and Phase I/II in US, EU, China</td></tr>
</table>

<p><a href="/hantavirus">← Back to hantavirus overview</a></p>
{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /hantavirus/treatment
# ---------------------------------------------------------------------------


TREATMENT_BODY = f"""
<p class="lead">
There is no specific licensed antiviral for HPS in Europe or North
America. Treatment is <strong>supportive critical care</strong> —
mechanical ventilation, fluid management, vasopressors, ECMO where
indicated, and renal replacement therapy for HFRS. <strong>Early
recognition and intensive care are the strongest survival predictors.</strong>
</p>

{_NOT_MEDICAL_ADVICE}

<h2>HPS supportive care</h2>
<p>
Patients meeting clinical criteria should be transferred to an ICU with
ECMO capability where geographically feasible. Per CDC and Argentine
Ministerio de Salud guidance:
</p>
<ul>
<li><strong>Oxygenation</strong> — early high-flow nasal cannula or
intubation; lung-protective ventilation (low tidal volume, plateau
pressure ≤30 cmH₂O).</li>
<li><strong>Fluid management</strong> — cautious; the cardiopulmonary
phase has profound vascular leak with relative hypovolaemia, but
over-resuscitation worsens pulmonary oedema. Crystalloids first;
vasopressors early.</li>
<li><strong>ECMO</strong> — veno-arterial ECMO has improved outcomes
in Andes-virus HPS in Chile and Argentina. CDC and PAHO both list
ECMO availability as a survival determinant.</li>
<li><strong>Antibiotics</strong> — empirical broad-spectrum cover until
diagnosis confirmed (atypical pneumonia, sepsis, leptospirosis must be
excluded).</li>
</ul>

<h2>HFRS supportive care</h2>
<ul>
<li>Fluid and electrolyte management calibrated to the five-stage
clinical course — restrictive during the oliguric phase, then permissive
during the diuretic phase.</li>
<li>Renal replacement therapy (haemodialysis or CRRT) for acute kidney
injury — required in 30 to 60 percent of severe HFRS cases.</li>
<li>Blood-product transfusion for haemorrhagic complications.</li>
<li>Avoid nephrotoxic drugs (NSAIDs, aminoglycosides) where possible.</li>
</ul>

<h2>Antiviral therapy</h2>
<p>
<strong>Ribavirin</strong> has demonstrated benefit in <em>early</em> HFRS
(meta-analyses of Chinese HTNV cohorts show roughly halved mortality
when started within 7 days of symptom onset). Evidence in HPS is weaker
and most trials have shown no benefit; the US placebo-controlled trial
in SNV-HPS was stopped early for futility. Ribavirin is
not licensed for hantavirus in the EU or US but is used off-label in
Latin America.
</p>
<p>
<strong>Monoclonal antibody and convalescent plasma</strong> approaches
have been investigated in Argentine and Chilean ANDV cohorts with
suggestive but inconclusive efficacy data. Several mAb candidates are
in Phase I/II trials in 2026.
</p>

<h2>Long-term sequelae</h2>
<p>
Survivors of HFRS may have persistent renal impairment (around 5 to 10
percent), hypertension, and proteinuria. HPS survivors generally
recover normal pulmonary function within 6 to 12 months but report
prolonged fatigue. Both syndromes have documented neurocognitive
sequelae in case series — assessment and rehabilitation are
recommended.
</p>

<p><a href="/hantavirus">← Back to hantavirus overview</a></p>
{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /glossary — extensive terminology page (high ranking signal)
# ---------------------------------------------------------------------------


GLOSSARY_TERMS: list[tuple[str, str]] = [
    ("ANDV", "Andes virus — the only orthohantavirus with documented person-to-person transmission. Endemic to southern South America. Implicated in the 2026 MV Hondius cluster."),
    ("Apodemus", "Genus of Old World field mice. <em>Apodemus agrarius</em> is the reservoir for Hantaan virus and Saaremaa virus; <em>Apodemus flavicollis</em> for Dobrava-Belgrade virus."),
    ("Berkeley Protocol", "International protocol for digital open-source investigations developed by UC Berkeley's Human Rights Center. Defines chain-of-custody requirements for OSINT used in legal proceedings. Every HORIZON record carries a Berkeley-compliant SHA-256 hash."),
    ("Case-fatality rate (CFR)", "Proportion of confirmed cases of a disease that die. For hantavirus disease ranges from under 1 percent (Puumala) to 30–50 percent (Andes virus HPS)."),
    ("CDC HAN", "US Centers for Disease Control and Prevention Health Alert Network — official channel for emergent public-health alerts. Indexed by HORIZON."),
    ("Convalescent plasma", "Therapeutic transfusion of antibody-rich plasma from recovered patients. Investigated for Andes virus HPS with suggestive efficacy."),
    ("DOBV", "Dobrava-Belgrade virus — causes the most severe HFRS in Europe. Reservoir: yellow-necked mouse (<em>Apodemus flavicollis</em>)."),
    ("ECDC", "European Centre for Disease Prevention and Control. Authoritative European public-health agency; indexed for surveillance updates and weekly Communicable Disease Threats Reports."),
    ("ECMO", "Extracorporeal membrane oxygenation. Veno-arterial ECMO has improved Andes-virus HPS outcomes in Chile and Argentina."),
    ("Endemic", "Continuously present in a population at a baseline level. Sin Nombre virus is endemic in the US Four Corners region."),
    ("Epizootic", "Outbreak of disease in animal populations. Cyclical Puumala-virus epizootics in bank-vole populations drive human-case peaks across northern Europe."),
    ("Four Corners outbreak", "1993 cluster of HPS cases in the US Four Corners region (Arizona, Colorado, New Mexico, Utah) that led to the identification of Sin Nombre virus. The outbreak is the historical anchor of US hantavirus surveillance."),
    ("HantaNet", "Reference set of Orthohantavirus genome sequences curated by the CDC Molecular Epidemiology and Bioinformatics Team (described in PMC10675615). Covers S, M, and L segments for all NCBI RefSeq Orthohantavirus reference sequences. HORIZON ingests the full HantaNet set daily, cross-linking case records to reference genome sequences."),
    ("Hantavax", "Green Cross hantavirus vaccine licensed in South Korea, covering Hantaan virus. The only licensed hantavirus vaccine; not approved in the EU or US."),
    ("HFRS", "Haemorrhagic Fever with Renal Syndrome. Old World hantavirus syndrome dominated by acute kidney injury and bleeding. Caused by Hantaan, Seoul, Puumala, Dobrava-Belgrade, and Saaremaa viruses."),
    ("HORIZON", "The platform you are reading. Live hantavirus outbreak surveillance with audit-grade source provenance, operated by 79th Unit Limited under CC BY 4.0. Aggregates 65+ sources including the Oxford Kraemer Lab MV Hondius individual-level ANDV line list and the NCBI RefSeq Orthohantavirus reference genome set (HantaNet)."),
    ("Individual line list", "Per-person epidemiological dataset where each row represents one patient or suspected case. The Oxford Kraemer Lab MV Hondius line list (CC0) provides 28-column individual-level resolution for the 2026 ANDV cruise ship cluster — the highest epidemiological granularity available for that outbreak."),
    ("HPS", "Hantavirus Pulmonary Syndrome. New World hantavirus syndrome dominated by non-cardiogenic pulmonary oedema and circulatory collapse. Caused by Andes, Sin Nombre, Bayou, Black Creek Canal, Laguna Negra, and Choclo viruses."),
    ("HTNV", "Hantaan virus — prototype hantavirus, severe HFRS in east Asia. Reservoir: striped field mouse (<em>Apodemus agrarius</em>)."),
    ("ICD 206", "US intelligence-community standard formal-citation format. HORIZON uses ICD 206 Source Reference Citation format on every record."),
    ("Immunoblast", "Activated lymphocyte. Circulating immunoblasts on peripheral blood smear are part of the hantavirus diagnostic triad (with thrombocytopenia and left-shifted white-cell count)."),
    ("MV Hondius", "Polar expedition cruise ship operated by Oceanwide Expeditions (IMO 9818709, MMSI 244327000, Netherlands flag). Centre of the 2026 ANDV cluster tracked at /outbreaks/mv-hondius-2026."),
    ("NATO Admiralty Scale", "Source-evaluation framework per NATO AJP-2.1 with two axes: reliability (A confirmed to F unreliable) and credibility (1 confirmed to 6 cannot be judged). HORIZON tags every source with both."),
    ("Nephropathia epidemica", "Mild HFRS caused by Puumala virus. Endemic across Scandinavia, Baltic states, and central Europe; case-fatality under 1 percent."),
    ("Nextstrain", "Open-source genomic epidemiology platform that provides real-time analysis of pathogen evolution. Andrew Rambaut (University of Edinburgh) is a co-developer. The Oxford Kraemer Lab MV Hondius line list was developed in collaboration with the Nextstrain group."),
    ("Orthohantavirus", "Genus of viruses within family <em>Hantaviridae</em>. All human-pathogenic hantaviruses belong to this genus."),
    ("Oxford Kraemer Lab", "Laboratory of Dr Moritz Kraemer at the University of Oxford Department of Biology. Maintains the MV Hondius individual-level ANDV line list (CC0, github.com/kraemer-lab/Hondius_hantavirus_h2026), the highest-resolution epidemiological dataset available for the 2026 Andes virus cruise ship cluster. Co-created with Sam Scarpino and Andrew Rambaut (University of Edinburgh / Nextstrain)."),
    ("Pathoplexus", "Genomic database for emerging pathogen sequences, linked to the Oxford Kraemer Lab MV Hondius line list via accession identifiers for each tracked case."),
    ("PAHO", "Pan American Health Organization — WHO regional office for the Americas. Authoritative source for hantavirus surveillance in Latin America and the Caribbean."),
    ("Peromyscus", "Genus of New World mice. <em>Peromyscus maniculatus</em> (deer mouse) is the reservoir for Sin Nombre virus across the US Four Corners and beyond."),
    ("ProMED", "Program for Monitoring Emerging Diseases — global outbreak reporting service of the International Society for Infectious Diseases. Critical early-warning feed for outbreak detection."),
    ("PUUV", "Puumala virus — Europe's commonest hantavirus, causing mild renal syndrome (nephropathia epidemica). Reservoir: bank vole (<em>Myodes glareolus</em>)."),
    ("Ribavirin", "Guanosine analogue antiviral with demonstrated benefit in early HFRS (especially Hantaan virus) but limited efficacy in HPS. Used off-label in Latin America for ANDV."),
    ("SEOV", "Seoul virus — globally distributed via Rattus rodents. Causes mild HFRS. Outbreaks documented in pet-rat fanciers in the US and UK."),
    ("Serotype", "Distinct virus variant defined by antigenic profile. HORIZON tracks 12 orthohantavirus serotypes of public-health concern."),
    ("Sin Nombre virus (SNV)", "Original North American HPS-causing hantavirus identified in 1993. Reservoir: deer mouse (<em>Peromyscus maniculatus</em>)."),
    ("Thrombocytopenia", "Low platelet count (below 150,000/μL). Universal feature of severe hantavirus infection — part of the diagnostic triad."),
    ("Ushuaia", "Argentine port at the southern tip of Tierra del Fuego. Suspected exposure location for the MV Hondius cluster. ANDV reservoir <em>Oligoryzomys longicaudatus</em> is endemic in the area."),
    ("Vascular leak", "Pathological extravasation of fluid from capillaries — the defining pathophysiology of hantavirus disease. Drives pulmonary oedema in HPS and shock in HFRS."),
    ("WHO DON", "World Health Organization Disease Outbreak News — the authoritative global outbreak bulletin. HORIZON parses every DON for relevance and ingests case counts."),
]


def render_glossary_body() -> str:
    parts: list[str] = [
        '<p class="lead">An auditable glossary of hantavirus terminology, '
        'surveillance vocabulary, and intelligence-tradecraft terms used '
        'on this site. Cross-linked into the relevant topic pages.</p>',
        '<dl>',
    ]
    for term, defn in sorted(GLOSSARY_TERMS):
        anchor = term.lower().replace(" ", "-").replace("(", "").replace(")", "")
        parts.append(
            f'<dt id="{esc(anchor)}"><strong>{esc(term)}</strong></dt>'
            f'<dd>{defn}</dd>'
        )
    parts.append('</dl>')
    parts.append('<p><a href="/hantavirus">← Back to hantavirus overview</a></p>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# /methodology
# ---------------------------------------------------------------------------


METHODOLOGY_BODY = f"""
<p class="lead">
HORIZON is built to a single principle: <strong>every claim is auditable
back to a public source.</strong> No anonymous tips, no scraped social
posts presented as fact, no laundered citations. This page documents the
exact qualification chain every record passes through.
</p>

{_NOT_MEDICAL_ADVICE}

<h2>1. Source qualification — NATO Admiralty Scale</h2>
<p>
Every source registered on HORIZON receives a two-axis rating per NATO
<a href="https://www.nato.int" rel="external">AJP-2.1</a>:
</p>
<table class="facts">
<tr><th>Reliability (source)</th><td>A confirmed · B usually reliable · C fairly reliable · D not usually reliable · E unreliable · F cannot be judged</td></tr>
<tr><th>Credibility (info)</th><td>1 confirmed · 2 probably true · 3 possibly true · 4 doubtful · 5 improbable · 6 cannot be judged</td></tr>
</table>
<p>
A WHO Disease Outbreak News bulletin rates A1 (confirmed source,
confirmed info). A peer-reviewed Lancet ID paper typically rates A2. A
verified national-authority press release rates B1 to B2. Reuters and AP
news wire rates B2 to B3. A single-source social media post rates
D4 or worse — these are stored but never auto-applied to incident
counts.
</p>
<p>
Auto-application of an extracted fact to the incident ontology requires
an A1/A2/B1/B2 source OR three corroborating independent sources within
48 hours. Both paths are documented per record in the
<code>extraction_proposals</code> audit log.
</p>

<h2>2. ICD 206 Source Reference Citation</h2>
<p>
Every <code>src_citation</code> field follows the US intelligence-community
ICD 206 format: <code>[CLASSIFICATION] AUTHOR (RELIABILITY/CREDIBILITY)
"TITLE" PUBLICATION, DATE, IDENTIFIER</code>. Example for the MV Hondius
WHO bulletin:
</p>
<blockquote>
[PUBLIC] WHO (A1) "Disease Outbreak News 2026-DON600: Andes hantavirus —
MV Hondius cluster" World Health Organization, 2026-05-11
</blockquote>

<h2>3. Dual confidence model</h2>
<p>
<strong>Pipeline confidence</strong> (machine, 0.0 to 1.0) reflects the
statistical confidence of the auto-extraction process — entity
disambiguation, deduplication match score, regex pattern
specificity. <strong>Analyst confidence</strong> (human, 0.0 to 1.0,
nullable) is set only when a 79th Unit analyst has manually reviewed
the record.
</p>
<p>
These are <em>never</em> conflated. Front-end displays distinguish them
clearly: amber for pipeline (provisional), green for analyst (vetted).
Exports require analyst confidence on every included object.
</p>

<h2>4. Berkeley Protocol chain-of-custody</h2>
<p>
The <a href="https://humanrights.berkeley.edu/programs-projects/tech-human-rights-program/berkeley-protocol" rel="external">Berkeley Protocol on Digital Open Source Investigations</a> defines
the chain-of-custody requirements that make OSINT admissible in legal
proceedings. Every fetched document on HORIZON is hashed (SHA-256) at
ingestion and the hash is stored alongside the fetch timestamp, the
URL, and the User-Agent that retrieved it. Re-fetch produces a new row
if the hash changes — we never overwrite history.
</p>

<h2>5. Cluster-tie scoring (incident-specific)</h2>
<p>
For the MV Hondius cluster, an article must pass a cluster-tie classifier
before any extracted facts auto-apply to the ontology:
</p>
<ul>
<li><strong>Strong tie (score 1.0)</strong> — explicit MV Hondius / Oceanwide
Expeditions / Hondius port-name mention.</li>
<li><strong>Medium tie (0.5)</strong> — hantavirus + repatriation/evacuation
context + route country.</li>
<li><strong>Weak tie (0.0)</strong> — hantavirus mention without
ship/port/repatriation context. <em>Produces no proposals.</em></li>
</ul>

<h2>6. Per-country authoritative cap (anti-inflation)</h2>
<p>
News articles frequently report cluster totals ("infections grow to 9 as
Spanish passenger falls ill") that the extractor could mis-attribute to
the country mentioned nearby. HORIZON now enforces a global cap: per-country
proposals where <code>value_numeric ≥ WHO confirmed total</code> are
rejected as cluster-total misattributions. The cap is sourced from the
WHO Disease Outbreak News authoritative count and ECDC corroboration.
</p>

<h2>7. Unique datasets</h2>
<p>
HORIZON ingests two datasets not available in any other public hantavirus
surveillance platform:
</p>
<p>
<strong>Oxford Kraemer Lab MV Hondius individual-level ANDV line list</strong>
(CC0) — maintained by Dr Moritz Kraemer (University of Oxford, Department
of Biology), Sam Scarpino, and Andrew Rambaut (University of Edinburgh,
Nextstrain). Located at
<a href="https://github.com/kraemer-lab/Hondius_hantavirus_h2026" rel="external">github.com/kraemer-lab/Hondius_hantavirus_h2026</a>.
28-column per-person resolution: status, symptom onset date, clinical
outcome, nationality, country of exposure, treatment received, hospitalisation,
travel history, and Pathoplexus/GenBank accession identifiers. Each row is
cross-referenced against WHO Disease Outbreak News DON600 and national health
authority press releases. This is the highest epidemiological resolution
dataset available for the 2026 MV Hondius cluster. Updated continuously
as the outbreak evolves.
</p>
<p>
<strong>NCBI RefSeq Orthohantavirus reference genome set (HantaNet)</strong>
— curated by the CDC Molecular Epidemiology and Bioinformatics Team
(described in <a href="https://pubmed.ncbi.nlm.nih.gov/37937497/" rel="external">PMC10675615</a>).
Covers the full set of NCBI RefSeq Orthohantavirus reference sequences:
S, M, and L segments for Andes virus, Sin Nombre virus, Puumala virus,
Hantaan virus, Seoul virus, Dobrava-Belgrade virus, Bayou virus, Black
Creek Canal virus, Laguna Negra virus, Choclo virus, Saaremaa virus,
Tula virus, and all other listed species. Ingested daily to provide a
permanent genomic annotation layer cross-linked against the
epidemiological case records.
</p>

<h2>8. Open data and API</h2>
<p>
All non-pre-decisional data is published live at <a href="/api/v1/cases">/api/v1/cases</a>,
<a href="/api/v1/incidents">/api/v1/incidents</a>,
<a href="/api/v1/sources">/api/v1/sources</a>, and
<a href="/api/v1/meta/events">/api/v1/meta/events</a> under CC BY 4.0.
Bulk NDJSON streaming export: <a href="/api/v1/cases/bulk/ndjson">/api/v1/cases/bulk/ndjson</a>.
OpenAPI schema: <a href="/api/openapi.json">/api/openapi.json</a>.
Cite: <a href="/CITATION.cff">/CITATION.cff</a>.
</p>

<p><a href="/sources">→ View the full source registry</a></p>
{_CTA_LIVE_MAP}
"""


# ---------------------------------------------------------------------------
# /faq
# ---------------------------------------------------------------------------


FAQ_ENTRIES: list[tuple[str, str]] = [
    (
        "What is hantavirus?",
        "Hantavirus is a family of rodent-borne viruses (genus <em>Orthohantavirus</em>, family <em>Hantaviridae</em>) that can cause severe disease in humans. The two main syndromes are <strong>Hantavirus Pulmonary Syndrome (HPS)</strong>, common in the Americas and caused by Sin Nombre virus and Andes virus, and <strong>Haemorrhagic Fever with Renal Syndrome (HFRS)</strong>, common in Eurasia and caused by Hantaan, Seoul, Puumala, and Dobrava-Belgrade viruses. See the <a href=\"/hantavirus\">hantavirus overview</a> for the full picture.",
    ),
    (
        "How is hantavirus transmitted?",
        "Most hantaviruses are transmitted from rodents to humans by inhalation of aerosolised excreta (urine, faeces, saliva). Direct rodent bites and mucous-membrane contact are documented but rare. <strong>Andes virus is the sole exception</strong> — it has documented person-to-person transmission, primarily between close household contacts. Hantaviruses are <em>not</em> transmitted by mosquitoes or ticks. Full breakdown on the <a href=\"/hantavirus/transmission\">transmission page</a>.",
    ),
    (
        "What are the symptoms of hantavirus disease?",
        "Initial symptoms appear 1 to 8 weeks after exposure: fever, severe muscle aches (myalgia), fatigue, headache, and gastrointestinal upset. In HPS, this progresses to coughing, shortness of breath, and pulmonary oedema — case-fatality 30 to 50 percent. In HFRS, patients develop kidney failure, low platelets, and bleeding — case-fatality 1 to 15 percent depending on serotype. See the <a href=\"/hantavirus/symptoms\">full symptoms page</a>.",
    ),
    (
        "Is there a vaccine or treatment for hantavirus?",
        "South Korea licenses <strong>Hantavax</strong> for Hantaan virus. No vaccine is licensed in the EU or US. Treatment is supportive critical care — fluid management, mechanical ventilation, ECMO, and renal replacement therapy. Ribavirin shows benefit in early HFRS but not HPS. Detailed <a href=\"/hantavirus/treatment\">treatment information</a> is available.",
    ),
    (
        "Which countries report hantavirus cases?",
        "Cases are reported across the Americas (Argentina, Chile, Brazil, USA, Canada, Panama, Bolivia, Paraguay), Europe (Germany, Finland, Russia, Belgium, France, Balkans), east Asia (China, South Korea, Japan, Russian Far East), and parts of Africa and southeast Asia. HORIZON maintains a <a href=\"/countries\">country-by-country page</a>.",
    ),
    (
        "What is the MV Hondius hantavirus cluster?",
        "An Andes virus cluster aboard the polar expedition cruise ship <strong>MV Hondius</strong> (IMO 9818709, MMSI 244327000, Oceanwide Expeditions, NL flag). Suspected pre-departure exposure during a wildlife excursion near Ushuaia, Tierra del Fuego, Argentina. The cluster is being tracked by WHO, ECDC, CDC, PAHO, and Argentine Ministerio de Salud. Live timeline and ontology at <a href=\"/outbreaks/mv-hondius-2026\">/outbreaks/mv-hondius-2026</a>.",
    ),
    (
        "How can I prevent hantavirus infection?",
        "Reduce rodent populations around homes; never sweep or vacuum dry excreta (it aerosolises virus); wear an N95/FFP3 respirator and wet contaminated surfaces with 1:10 bleach before cleaning. Campers and hikers in endemic regions should avoid sleeping near rodent nests. Full evidence-based protocol on the <a href=\"/hantavirus/prevention\">prevention page</a>.",
    ),
    (
        "What is HORIZON?",
        "HORIZON is a live hantavirus surveillance platform operated by <a href=\"https://79thunit.co.uk\">79th Unit Limited</a> (UK Companies House 17133814). It aggregates outbreak signal from WHO, US CDC, ECDC, PAHO, ProMED, national authorities, peer-reviewed literature, and open news. Every record carries audit-grade source provenance per ICD 206, NATO Admiralty Scale, dual confidence, and Berkeley Protocol chain-of-custody. All data is open under CC BY 4.0. Read the full <a href=\"/methodology\">methodology</a>.",
    ),
    (
        "How accurate are the case counts?",
        "Case counts on HORIZON come from authoritative public-health bulletins (WHO Disease Outbreak News, ECDC weekly threats reports, CDC HAN, PAHO updates, national-authority statements). News reports are stored as corroborating evidence but only auto-applied to per-country totals when a NATO A/B source or three independent corroborating sources within 48h confirm. Anti-inflation caps prevent cluster-total numbers from mis-attributing to a single country. The full audit trail per number is on the methodology page.",
    ),
    (
        "Can I use this data?",
        "Yes. All HORIZON data is released under <a href=\"https://creativecommons.org/licenses/by/4.0/\" rel=\"license external\">Creative Commons Attribution 4.0 International</a>. Mirror it, scrape it, index it, train models on it. The only requirement is attribution to 79th Unit Limited. JSON endpoints: <a href=\"/api/openapi.json\">OpenAPI schema</a>.",
    ),
    (
        "How is this different from CDC, WHO, or ECDC?",
        "Those are <em>authoritative primary sources</em>. HORIZON is an <em>aggregator and surveillance layer</em> that sits on top of them — pulling in WHO/CDC/ECDC/PAHO bulletins, cross-referencing peer-reviewed literature, layering open news, and presenting a single live ontology with every claim provenance-traced. Use the primary sources for clinical or regulatory decisions; use HORIZON for situational awareness and OSINT-quality outbreak monitoring.",
    ),
    (
        "Why is the case count different from a news article I read?",
        "News articles routinely conflate per-country counts with cluster totals (an NBC article saying \"3 deaths\" when the cluster has 3 deaths total, but the deaths occurred in Netherlands and South Africa — not the US). HORIZON resolves to per-country authoritative totals from WHO and ECDC and discards cluster-total misattributions. See <a href=\"/methodology\">methodology</a> for the anti-inflation logic.",
    ),
    (
        "How do I report a missing source or an error?",
        "Email <a href=\"mailto:security@79thunit.co.uk\">security@79thunit.co.uk</a> — coordinates and disclosure policy in the <a href=\"/.well-known/security.txt\">security.txt</a>. Corrections to specific case records should include the record ID and a source citation.",
    ),
    (
        "What is the Oxford Kraemer Lab hantavirus line list?",
        "The Oxford Kraemer Lab MV Hondius line list is a living CC0 dataset at "
        "<a href=\"https://github.com/kraemer-lab/Hondius_hantavirus_h2026\" rel=\"external\">github.com/kraemer-lab/Hondius_hantavirus_h2026</a>, "
        "maintained by Dr Moritz Kraemer (University of Oxford), Sam Scarpino, and "
        "Andrew Rambaut (University of Edinburgh / Nextstrain). It provides "
        "28-column per-person resolution for every tracked case in the 2026 MV Hondius "
        "Andes virus cluster, including symptom onset date, clinical outcome, "
        "nationality, treatment, and Pathoplexus genomic accession IDs. HORIZON is "
        "the only public surveillance platform ingesting this dataset in real time. "
        "See the <a href=\"/methodology\">methodology page</a> for details.",
    ),
    (
        "What is HantaNet and how does HORIZON use it?",
        "HantaNet is the reference genome set for Orthohantavirus, curated by the "
        "CDC Molecular Epidemiology and Bioinformatics Team and described in "
        "<a href=\"https://pubmed.ncbi.nlm.nih.gov/37937497/\" rel=\"external\">PMC10675615</a>. "
        "It covers all NCBI RefSeq Orthohantavirus reference sequences (S, M, L "
        "segments for all major serotypes). HORIZON ingests the full HantaNet set "
        "daily via the NCBI E-utilities API, creating a permanent genomic annotation "
        "layer that cross-links case records to their reference genome sequences. "
        "This allows outbreak records to be linked directly to the genomic reference "
        "for the responsible serotype — a capability not available in other public "
        "hantavirus trackers.",
    ),
    (
        "How does HORIZON compare to HantaNet, HantaReg, or ArcGIS dashboards?",
        "HORIZON is complementary to, not a replacement for, these specialised tools. "
        "<strong>HantaNet</strong> is a genomic reference database; HORIZON ingests "
        "HantaNet and links its sequences to epidemiological case records. "
        "<strong>HantaReg</strong> is a clinical registry focused on patient outcomes; "
        "HORIZON provides population-level surveillance rather than individual clinical "
        "data. <strong>ArcGIS dashboards</strong> are visualisation layers over "
        "existing data sources; HORIZON is the data layer itself, with 65+ ingestion "
        "connectors, NATO Admiralty source qualification, and a public API. The key "
        "differences: HORIZON aggregates 65+ sources (not one), provides individual-"
        "level data from the Oxford Kraemer Lab CC0 line list, applies audit-grade "
        "source qualification to every record, and exposes a fully open JSON/NDJSON "
        "API under CC BY 4.0.",
    ),
    (
        "Where can I download hantavirus data?",
        "All HORIZON data is free and open under CC BY 4.0. "
        "<a href=\"/api/v1/cases\">JSON API</a> — paginated case records with full "
        "provenance. "
        "<a href=\"/api/v1/cases/bulk/ndjson\">Bulk NDJSON</a> — streaming export, "
        "no cursor limit. "
        "<a href=\"/api/v1/sources\">Source registry</a> — all 65+ sources with NATO "
        "ratings and telemetry. "
        "<a href=\"/api/v1/incidents\">Incident ontology</a> — structured outbreak "
        "entities. "
        "<a href=\"/CITATION.cff\">CITATION.cff</a> — machine-readable citation for "
        "academic use. No API key or registration required.",
    ),
]


def render_faq_body() -> str:
    parts: list[str] = [
        '<p class="lead">Frequently asked questions about hantavirus, the MV Hondius cluster, and the HORIZON surveillance platform.</p>',
    ]
    for q, a in FAQ_ENTRIES:
        parts.append(
            f'<h2>{esc(q)}</h2>\n<div>{a}</div>'
        )
    parts.append('<p><a href="/hantavirus">← Back to hantavirus overview</a></p>')
    parts.append(_CTA_LIVE_MAP)
    return "".join(parts)


def render_serotype_body(s: dict[str, str]) -> str:
    """Render the body of a /hantavirus/{slug} page from a SEROTYPES entry."""
    extra_links = ""
    if s.get("wikipedia"):
        extra_links += f'<li><a href="{esc(s["wikipedia"])}" rel="external">Wikipedia: {esc(s["name"])}</a></li>'
    if s.get("wikidata"):
        extra_links += f'<li><a href="https://www.wikidata.org/wiki/{esc(s["wikidata"])}" rel="external">Wikidata</a></li>'
    return f"""
<p class="lead">{esc(s["summary"])}</p>

{_NOT_MEDICAL_ADVICE}

<table class="facts">
<tr><th>Virus code</th><td><strong>{esc(s["code"])}</strong></td></tr>
<tr><th>Full name</th><td>{esc(s["name"])}</td></tr>
<tr><th>Clinical syndrome</th><td>{esc(s["syndrome"])}</td></tr>
<tr><th>ICD-10 code</th><td>{esc(s["icd"])}</td></tr>
<tr><th>Reservoir species</th><td>{esc(s["reservoir"])}</td></tr>
<tr><th>Endemic regions</th><td>{esc(s["endemic"])}</td></tr>
<tr><th>Case-fatality rate</th><td>{esc(s["cfr"])}</td></tr>
<tr><th>Person-to-person</th><td>{esc(s["p2p"])}</td></tr>
</table>

<h2>About {esc(s["name"])}</h2>
<p>{esc(s["summary"])}</p>

<h2>Surveillance and outbreaks</h2>
<p>
HORIZON ingests every WHO Disease Outbreak News bulletin, ECDC weekly
Communicable Disease Threats Report, CDC HAN advisory, PAHO update,
and peer-reviewed publication that mentions {esc(s["code"])}.
Browse the <a href="/articles">live article feed</a> or hit the
<a href="/api/v1/cases">JSON API</a> for the raw data. Active incidents
involving this serotype appear on the
<a href="/">live outbreak map</a>.
</p>

<h2>Authoritative sources</h2>
<ul>
<li><a href="https://www.cdc.gov/hantavirus/" rel="external">CDC Hantavirus</a></li>
<li><a href="https://www.who.int/news-room/fact-sheets/detail/hantavirus-disease" rel="external">WHO Hantavirus fact sheet</a></li>
<li><a href="https://www.ecdc.europa.eu/en/infectious-disease-topics/hantavirus-infection" rel="external">ECDC Hantavirus surveillance</a></li>
{extra_links}
</ul>

<h2>Related serotypes</h2>
{_related_serotypes_grid(exclude_slug=s["slug"])}

<p><a href="/hantavirus">← All hantavirus topics</a></p>
{_CTA_LIVE_MAP}
"""
