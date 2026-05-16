"""Extended content sections appended to thin SEO pages.

Each `*_EXT` constant is a block of HTML appended below the existing body
in its respective page handler (in `routers/seo.py`). The new content
adds: long-tail keyword coverage, FAQ blocks, comparison tables,
internal cross-links, and visible numeric data so the page competes on
its target query against established medical references.

Each constant typically adds 800-1500 words. Combined with the existing
body, every page ends up at 1800-3000 words — past Google's apparent
quality threshold for medical content.

Schema additions (FAQPage, HowTo, Speakable, LiveBlogPosting, etc.) are
defined in `_FAQ_*` lists below and rendered into JSON-LD at the
page-handler level.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# /hantavirus/symptoms — extended
# ---------------------------------------------------------------------------

SYMPTOMS_EXT = """
<h2>Hantavirus symptom timeline — what to expect day by day</h2>
<p>Patients and clinicians frequently ask for a calendar-style view of how
hantavirus disease unfolds. The pattern below is based on consolidated CDC,
WHO, and ECDC clinical-course descriptions for Hantavirus Pulmonary Syndrome
(HPS) caused by Sin Nombre virus and Andes virus, and Haemorrhagic Fever
with Renal Syndrome (HFRS) caused by Hantaan, Puumala, and Dobrava-Belgrade
virus. Individual courses vary widely.</p>
<table class="facts">
<thead><tr><th>Day post-exposure</th><th>HPS course</th><th>HFRS course</th></tr></thead>
<tbody>
<tr><th>0-6</th><td>Asymptomatic incubation. No detectable illness.</td><td>Asymptomatic incubation.</td></tr>
<tr><th>7-21</th><td>Possible mild fever in some cases; usually still asymptomatic.</td><td>Asymptomatic. Mean incubation 12-21 days.</td></tr>
<tr><th>21-35</th><td>Most patients become symptomatic. Sudden fever &gt;38.5°C, severe muscle pain in thighs and lower back, headache, GI upset.</td><td>Febrile phase begins. Headache, fever, abdominal pain, conjunctival haemorrhage, petechial rash.</td></tr>
<tr><th>+3 to +5 days from onset</th><td>Prodrome continues. Cough may begin. Tachypnoea, mild hypoxia. Blood smear shows thrombocytopenia.</td><td>Hypotensive phase: BP crashes, shock risk, oliguria starts.</td></tr>
<tr><th>+5 to +10 days from onset</th><td><strong>Cardiopulmonary phase.</strong> Rapid-onset non-cardiogenic pulmonary oedema, severe hypoxia, circulatory shock. ICU admission essential. Survival depends on early ECMO availability for severe cases.</td><td>Oliguric phase: AKI, fluid overload, haemorrhagic complications. Dialysis often required.</td></tr>
<tr><th>+10 to +21 days from onset</th><td>Convalescence in survivors. Pulmonary function gradually recovers; some patients have persistent restrictive defects.</td><td>Diuretic phase, then convalescence. Renal function usually recovers but can leave lasting impairment.</td></tr>
<tr><th>Weeks to months</th><td>Chronic fatigue, exercise intolerance, mild persistent restrictive lung physiology. Most survivors return to baseline by 6-12 months.</td><td>Possible persistent hypertension (Puumala). Most patients recover full renal function.</td></tr>
</tbody>
</table>

<h2>Hantavirus symptoms in children</h2>
<p>Paediatric hantavirus is rare but disproportionately severe when it
occurs. CDC case-series data and the Brazilian Ministry of Health 2022 review
indicate children under 16 with HPS:</p>
<ul>
<li>Present with the same prodrome but often more pronounced GI symptoms
(abdominal pain, vomiting), which can be mistaken for acute appendicitis or
gastroenteritis.</li>
<li>Progress to the cardiopulmonary phase faster (median onset day 3 vs day
5 in adults).</li>
<li>Have higher mortality than adults in some series, attributed to lower
cardiac reserve and delayed recognition.</li>
<li>For Andes virus household clusters with paediatric cases, person-to-person
transmission is the suspected route in most paediatric infections.</li>
</ul>
<p>Any child with a febrile illness plus a household exposure to a recently
ill adult who travelled to or lives in an ANDV-endemic area (southern Chile,
Argentina, Magallanes, Aysén) should be evaluated for hantavirus exposure
even if the child has had no direct rodent contact.</p>

<h2>Hantavirus vs flu, COVID-19, and pneumonia — symptom comparison</h2>
<p>The early hantavirus prodrome is virtually indistinguishable from influenza
or COVID-19. The key discriminator is the rapid progression to severe
pulmonary oedema in HPS, or to oliguria and haemorrhage in HFRS. Use the
table below for differential reasoning, but never as a substitute for medical
assessment — see <a href="/hantavirus/vs/covid">hantavirus vs COVID-19</a> and
<a href="/hantavirus/vs/flu">hantavirus vs influenza</a> for fuller pages.</p>
<table class="facts">
<thead><tr><th>Feature</th><th>Hantavirus (HPS)</th><th>Influenza A/B</th><th>COVID-19</th><th>Bacterial pneumonia</th></tr></thead>
<tbody>
<tr><th>Incubation</th><td>1-6 weeks</td><td>1-4 days</td><td>2-14 days</td><td>1-3 days</td></tr>
<tr><th>Onset</th><td>Sudden, severe</td><td>Sudden</td><td>Gradual to sudden</td><td>Gradual</td></tr>
<tr><th>Fever</th><td>High (39-40°C)</td><td>High (38-40°C)</td><td>Moderate-high</td><td>High</td></tr>
<tr><th>Muscle pain</th><td>Severe, thighs/back</td><td>Diffuse</td><td>Variable</td><td>Mild</td></tr>
<tr><th>GI symptoms</th><td>Common, prominent</td><td>Occasional</td><td>Common in some variants</td><td>Rare</td></tr>
<tr><th>Cough</th><td>Late, with hypoxia</td><td>Common, early</td><td>Common, dry</td><td>Productive, early</td></tr>
<tr><th>Thrombocytopenia</th><td><strong>Universal</strong></td><td>Rare</td><td>Mild if any</td><td>Rare</td></tr>
<tr><th>Mortality</th><td>30-50% (HPS)</td><td>&lt;0.1%</td><td>~1%</td><td>5-10% (severe)</td></tr>
</tbody>
</table>

<h2>Self-assessment — when to call emergency services</h2>
<p>If you have a credible recent exposure (travel to MV Hondius itinerary,
rodent-infested cabin/shed cleanout, agricultural work in endemic area) and
develop ANY of the following, treat as a medical emergency and call your
national emergency number (<strong>999</strong> in the UK,
<strong>911</strong> in North America, <strong>112</strong> across the EU,
<strong>000</strong> in Australia, <strong>131</strong> in Argentina):</p>
<ul>
<li>Shortness of breath at rest or on minor exertion.</li>
<li>Chest tightness, pleuritic pain, or air hunger.</li>
<li>Confusion, agitation, or altered mental state.</li>
<li>Lips, fingertips, or face turning blue or grey.</li>
<li>Inability to keep down fluids alongside fever.</li>
<li>Unexplained bleeding (gums, nose, urine, stool).</li>
<li>Marked drop in urine output over 12-24 hours.</li>
</ul>
<p>Mention hantavirus exposure explicitly when speaking to dispatch. Most
emergency medicine clinicians will not consider hantavirus on their initial
differential without that prompt.</p>

<h2>Long-term effects after surviving hantavirus</h2>
<p>Most HPS and HFRS survivors return to baseline function over 6-12 months,
but persistent sequelae are documented:</p>
<ul>
<li><strong>HPS pulmonary sequelae</strong>: reduced diffusing capacity
(DLCO) on pulmonary function testing, mild persistent restrictive pattern.
Most patients regain near-normal exercise tolerance by 12 months.</li>
<li><strong>HFRS renal sequelae</strong>: minor proteinuria can persist for
months. Puumala specifically has been linked to long-term hypertension in
some Scandinavian cohorts.</li>
<li><strong>Post-viral fatigue</strong>: 20-30% of patients describe
prolonged fatigue and exercise intolerance for 3-6 months, regardless of
syndrome.</li>
<li><strong>Psychological sequelae</strong>: ICU-survivor cohorts show
post-traumatic stress symptoms at rates comparable to other severe-illness
ICU stays.</li>
</ul>

<h2>Hantavirus symptom FAQ</h2>
<p>See the dedicated questions <a href="/hantavirus/is-it-contagious">is
hantavirus contagious</a>, <a href="/hantavirus/death-rate">hantavirus
mortality rate</a>, and <a href="/hantavirus/incubation-period">hantavirus
incubation period</a> for the full answers. Quick versions:</p>
<ul>
<li><strong>Can you have hantavirus without a fever?</strong> Rare. Almost
every documented HPS or HFRS case had fever &gt;38°C at presentation.
Atypical afebrile cases have been reported but are exceptional.</li>
<li><strong>How quickly do hantavirus symptoms appear?</strong> 1-8 weeks
after exposure, with most cases presenting 2-4 weeks post-exposure.</li>
<li><strong>What does the hantavirus rash look like?</strong> HPS does not
usually present with a rash. HFRS classically shows petechiae (small
red-purple spots) on the soft palate, axillae, and chest, plus conjunctival
injection that looks like marked redness of the eye whites.</li>
<li><strong>Can hantavirus symptoms come and go?</strong> No. Once the
prodrome begins, the course is steadily worsening over hours to days.
Symptom-free intervals are not typical.</li>
</ul>
"""

FAQ_SYMPTOMS = [
    (
        "What are the first symptoms of hantavirus?",
        "The first symptoms of hantavirus appear 1-8 weeks after exposure and "
        "begin with a flu-like prodrome: high-grade fever (39-40°C), severe muscle "
        "pain especially in the thighs and lower back, headache, fatigue, nausea, "
        "vomiting, and abdominal pain. The prodrome lasts 3-7 days before the "
        "disease progresses to either Hantavirus Pulmonary Syndrome (HPS) or "
        "Haemorrhagic Fever with Renal Syndrome (HFRS) depending on the strain.",
    ),
    (
        "How long after exposure do hantavirus symptoms appear?",
        "Hantavirus symptoms appear 1-8 weeks after exposure, with most cases "
        "becoming symptomatic 2-4 weeks post-exposure. The median incubation period "
        "for Sin Nombre virus is approximately 14 days. Andes virus has a slightly "
        "longer documented range (7-39 days, median 14). Anyone with a recent "
        "credible exposure should self-monitor for up to 45 days to be safe.",
    ),
    (
        "Is hantavirus painful?",
        "Hantavirus prodromal symptoms include severe muscle pain (myalgia) in the "
        "thighs, hips, and lower back that patients consistently describe as worse "
        "than influenza. Headache and abdominal pain are also common. In the late "
        "pulmonary phase of HPS, air hunger and chest tightness are distressing. In "
        "HFRS, retro-orbital pain (behind the eyes) and loin pain are characteristic.",
    ),
    (
        "What is the hantavirus 'triad' on blood smear?",
        "The hantavirus haematological triad is: (1) thrombocytopenia (platelet "
        "count below 150,000/µL), (2) left-shifted white-cell count, and (3) "
        "circulating immunoblasts. When all three are present in a febrile patient "
        "with rapid pulmonary deterioration, hantavirus pulmonary syndrome should be "
        "the leading diagnosis until ruled out.",
    ),
    (
        "Can hantavirus be mistaken for COVID-19?",
        "Yes. The prodromal symptoms of hantavirus and COVID-19 overlap heavily: "
        "fever, fatigue, muscle aches, headache, GI symptoms. The discriminating "
        "features that should prompt hantavirus testing are: rapid progression to "
        "non-cardiogenic pulmonary oedema with hypotension (HPS); thrombocytopenia "
        "on bloods; relevant exposure history (rodent contact, travel to endemic "
        "area, MV Hondius itinerary). HORIZON's symptom-comparison page covers this "
        "in detail.",
    ),
    (
        "Can hantavirus symptoms be mild?",
        "Hantavirus infection can produce a subclinical or mild flu-like illness "
        "that resolves without diagnosis, particularly for Puumala virus (PUUV) "
        "which has a case-fatality rate under 1% and includes a substantial fraction "
        "of mild and asymptomatic infections. For Sin Nombre and Andes virus, "
        "clinically apparent infection is almost always severe.",
    ),
    (
        "Are hantavirus symptoms different in children?",
        "Paediatric hantavirus infection is rare but disproportionately severe. "
        "Children present with the same prodrome but often more prominent GI "
        "symptoms that can be mistaken for appendicitis or gastroenteritis. "
        "Progression to the cardiopulmonary phase is typically faster than in adults "
        "(median day 3 vs day 5), and mortality has historically been higher in some "
        "case series due to lower cardiac reserve and delayed recognition.",
    ),
    (
        "Does hantavirus cause a rash?",
        "HPS rarely causes a rash. HFRS classically presents with petechiae (small "
        "red-purple haemorrhagic spots) on the soft palate, in the axillae, and "
        "across the chest, alongside conjunctival injection that appears as marked "
        "redness of the eye whites. The petechial rash is a key clinical sign "
        "supporting HFRS over other tropical febrile illnesses.",
    ),
    (
        "What symptoms mean I should go to A&E for hantavirus?",
        "Call 999 (UK), 911 (US/Canada), 112 (EU), 000 (Australia), or 131 "
        "(Argentina) if you have credible recent exposure plus any of: shortness "
        "of breath, chest tightness, confusion, blue or grey lips/fingertips, "
        "inability to keep fluids down with fever, unexplained bleeding, or a sharp "
        "drop in urine output. Always mention hantavirus exposure explicitly to "
        "dispatch.",
    ),
    (
        "Do hantavirus survivors recover completely?",
        "Most HPS and HFRS survivors return to baseline function over 6-12 months. "
        "Persistent sequelae are documented: reduced pulmonary diffusing capacity "
        "(DLCO) after HPS, minor proteinuria after HFRS, and post-ICU fatigue or "
        "psychological symptoms in 20-30% of severe cases. Puumala-virus HFRS has "
        "been linked to long-term hypertension in some Scandinavian cohorts.",
    ),
]


# ---------------------------------------------------------------------------
# /hantavirus/transmission — extended
# ---------------------------------------------------------------------------

TRANSMISSION_EXT = """
<h2>How hantavirus is transmitted — full route inventory</h2>
<p>The dominant route for every hantavirus serotype is <strong>inhalation of
aerosolised rodent excreta</strong>. The mechanism is well-characterised:
the virus is shed in rodent urine, faeces, and saliva, which dry on indoor
surfaces; mechanical disturbance (sweeping, vacuuming without HEPA, moving
old furniture, lifting stored items) aerosolises the contaminated dust;
humans inhale the aerosolised particles. A small inoculum is sufficient.</p>
<table class="facts">
<thead><tr><th>Route</th><th>Documented for which serotypes</th><th>Relative frequency</th></tr></thead>
<tbody>
<tr><th>Inhalation of aerosolised excreta</th><td>All serotypes</td><td><strong>Dominant route (estimated &gt;95%)</strong></td></tr>
<tr><th>Direct rodent bite</th><td>SNV, ANDV, SEOV, HTNV</td><td>Rare</td></tr>
<tr><th>Hand-to-mucosa via contaminated surface</th><td>All serotypes</td><td>Documented but uncommon</td></tr>
<tr><th>Contaminated food or water</th><td>Theoretically possible; few documented cases</td><td>Very rare</td></tr>
<tr><th>Person-to-person, household close contact</th><td><strong>Andes virus only</strong></td><td>Rare even for ANDV; well-documented in Argentine and Chilean clusters</td></tr>
<tr><th>Laboratory exposure (needle-stick, droplet)</th><td>All serotypes — BSL-3 pathogen</td><td>Rare; managed under strict containment</td></tr>
<tr><th>Vertical (mother to fetus/newborn)</th><td>ANDV</td><td>Rare; few documented cases during peri-partum maternal viraemia</td></tr>
</tbody>
</table>

<h2>Reservoir species — who carries which strain</h2>
<p>Hantaviruses co-evolved with specific rodent species over millions of
years. The relationship is so tight that the virus phylogeny mirrors the host
phylogeny almost exactly. This means hantavirus risk is fundamentally
geographic: you can only catch the virus where the reservoir species lives.</p>
<table class="facts">
<thead><tr><th>Serotype</th><th>Primary rodent reservoir</th><th>Endemic geography</th></tr></thead>
<tbody>
<tr><th>Sin Nombre (SNV)</th><td>Deer mouse (<em>Peromyscus maniculatus</em>)</td><td>USA, Canada, northern Mexico — particularly the Four Corners region (Arizona, Colorado, New Mexico, Utah)</td></tr>
<tr><th>Andes (ANDV)</th><td>Long-tailed pygmy rice rat (<em>Oligoryzomys longicaudatus</em>)</td><td>Southern Chile and Argentina, Magallanes, Aysén, Patagonia</td></tr>
<tr><th>Puumala (PUUV)</th><td>Bank vole (<em>Myodes glareolus</em>)</td><td>Northern, central, and eastern Europe; Scandinavia (highest incidence in Finland, Sweden, Belgium)</td></tr>
<tr><th>Hantaan (HTNV)</th><td>Striped field mouse (<em>Apodemus agrarius</em>)</td><td>China, Korea, Russian Far East</td></tr>
<tr><th>Seoul (SEOV)</th><td>Brown rat (<em>Rattus norvegicus</em>)</td><td>Worldwide via global shipping; severe disease most often in Asia</td></tr>
<tr><th>Dobrava-Belgrade (DOBV)</th><td>Yellow-necked mouse (<em>Apodemus flavicollis</em>)</td><td>Balkans, central and eastern Europe</td></tr>
<tr><th>Laguna Negra (LANV)</th><td>Vesper mouse (<em>Calomys laucha</em>)</td><td>Paraguay, Bolivia, Argentina, Brazil</td></tr>
<tr><th>Choclo (CHOV)</th><td>Costa Rican pygmy rice rat (<em>Oligoryzomys fulvescens</em>)</td><td>Panama</td></tr>
<tr><th>Bayou (BAYV)</th><td>Marsh rice rat (<em>Oryzomys palustris</em>)</td><td>Southeastern USA</td></tr>
<tr><th>Black Creek Canal (BCCV)</th><td>Cotton rat (<em>Sigmodon hispidus</em>)</td><td>Florida, southeastern USA</td></tr>
</tbody>
</table>

<h2>Andes virus person-to-person transmission — the special case</h2>
<p>Andes virus is the <strong>only orthohantavirus with documented
human-to-human transmission</strong>. The mechanism remains under
investigation; current evidence supports respiratory droplet and direct
contact during the acute prodromal and cardiopulmonary phases. The 1996
Argentine outbreak in El Bolsón, the 2018 Epuyén outbreak, and the 2026 MV
Hondius cluster all show clear within-household secondary transmission
chains, with secondary cases typically presenting 14-25 days after the
primary case.</p>
<p>Practical implications:</p>
<ul>
<li>Patients with confirmed or suspected ANDV-HPS must be cared for under
droplet and contact precautions, with negative-pressure isolation where
available.</li>
<li>Healthcare workers attending ANDV-HPS patients should use FFP3/N95
respirators, eye protection, gowns, and gloves.</li>
<li>Household contacts of confirmed cases should self-isolate from
vulnerable people (children, elderly, immunocompromised) until cleared by
public-health follow-up.</li>
<li>Routine social and workplace contact does not require restriction for
asymptomatic contacts.</li>
<li>The MV Hondius 2026 cluster prompted the UK Health Security Agency
(UKHSA) and ECDC to update clinical guidance on ANDV contact tracing.</li>
</ul>

<h2>What is NOT a hantavirus transmission route</h2>
<p>Despite persistent online misinformation, hantavirus is NOT transmitted
by:</p>
<ul>
<li><strong>Mosquito or tick bites.</strong> Hantaviruses are not
arthropod-borne. Vector-borne haemorrhagic fevers (dengue, Crimean-Congo,
Rift Valley) are entirely separate viral families.</li>
<li><strong>Domestic pets.</strong> Dogs, cats, hamsters, guinea pigs, and
rabbits are not hantavirus reservoirs. The myth that pet hamsters carry
hantavirus is false — pet hamsters can rarely carry Seoul virus if exposed
to wild brown rats, but this requires unusual circumstances.</li>
<li><strong>Air conditioning systems.</strong> Hantaviruses do not survive
or replicate in HVAC ducting. Aerosol transmission requires a rodent-fouled
source (excreta), proximity, and disturbance.</li>
<li><strong>Sexual contact (other than ANDV close-contact transmission,
which is not specifically sexual).</strong> No documented hantavirus
serotype is sexually transmitted in the conventional sense.</li>
<li><strong>Blood donation.</strong> Hantavirus is not listed as a
transfusion-transmissible pathogen in any major blood-service screening
panel. Asymptomatic viraemia is too brief for routine blood-supply concern.</li>
<li><strong>Drinking water (public supply).</strong> Municipal water
treatment readily inactivates the virus. Risk would be limited to severely
contaminated raw water sources.</li>
</ul>

<h2>Hantavirus survival outside the host</h2>
<p>Hantavirus survival in the environment depends sharply on conditions.
Laboratory studies indicate:</p>
<ul>
<li>In dried rodent excreta at room temperature, the virus remains viable
for approximately <strong>2-3 days</strong>.</li>
<li>In cool, moist, dark conditions (rodent-fouled basements, sheds,
cabins), viability can extend to <strong>over a week</strong>.</li>
<li>UV light (direct sunlight) inactivates the virus within hours.</li>
<li>Heating to 60°C for 30 minutes inactivates it reliably.</li>
<li>10% bleach solution (1 part household bleach to 9 parts water) is the
CDC-recommended disinfectant for contaminated surfaces.</li>
<li>70% ethanol and standard quaternary-ammonium disinfectants are also
effective.</li>
</ul>

<h2>Travel and transmission risk by region</h2>
<p>Use HORIZON's <a href="/countries">country pages</a> for current
authoritative-source case counts and risk assessments. A summary of where
travellers are at elevated risk:</p>
<ul>
<li><strong>USA — Four Corners region</strong> (Arizona, Colorado, New
Mexico, Utah). Sin Nombre virus. Risk peaks in spring and summer when deer
mice populations are high.</li>
<li><strong>Chile and Argentina — southern Patagonia</strong> (Magallanes,
Aysén, Neuquén, Río Negro). Andes virus. Risk year-round but peaks in
summer (December-March) with peak rodent activity.</li>
<li><strong>Scandinavia — Finland, Sweden, Norway</strong>. Puumala virus.
Risk peaks in autumn and winter when bank voles enter buildings.</li>
<li><strong>Germany, Belgium, Netherlands, France</strong>. Puumala virus,
cyclical outbreak years driven by oak/beech mast cycles affecting bank
vole populations.</li>
<li><strong>China, Korea</strong>. Hantaan virus, seasonal peak in late
autumn during rice harvest.</li>
<li><strong>Russian Far East</strong>. Hantaan and Seoul virus.</li>
<li><strong>Balkans — Serbia, Bosnia, Croatia, Slovenia</strong>.
Dobrava-Belgrade and Puumala virus.</li>
<li><strong>Paraguay, Bolivia, Brazil northern Argentina</strong>. Laguna
Negra and Andes virus.</li>
</ul>
"""

FAQ_TRANSMISSION = [
    (
        "Is hantavirus contagious between people?",
        "With one exception, hantaviruses do not transmit between people. The "
        "exception is Andes virus (ANDV), endemic to southern South America, which "
        "has documented person-to-person transmission via close household contact "
        "during the acute illness. All other hantaviruses — Sin Nombre, Puumala, "
        "Hantaan, Seoul, Dobrava-Belgrade — are rodent-to-human only.",
    ),
    (
        "How do you catch hantavirus from a rodent?",
        "The primary route is inhaling aerosolised dust contaminated with rodent "
        "urine, faeces, or saliva. This typically happens in enclosed spaces "
        "(sheds, cabins, barns, basements) when contaminated dust is disturbed by "
        "sweeping, vacuuming without a HEPA filter, moving stored items, or "
        "renovating. Direct rodent bites and contaminated food/water are minor "
        "secondary routes.",
    ),
    (
        "Can you catch hantavirus from a hamster or pet?",
        "Pet hamsters, guinea pigs, dogs, cats, and rabbits do not carry hantavirus "
        "under normal circumstances and are not reservoirs. The only documented "
        "exception is pet brown rats or pet hamsters that have been exposed to wild "
        "brown rats carrying Seoul virus — these cases are extremely rare and have "
        "been documented mainly in the UK and US among rat-breeder communities.",
    ),
    (
        "Can mosquitoes spread hantavirus?",
        "No. Hantaviruses are not arthropod-borne. Mosquitoes, ticks, fleas, and "
        "midges do not carry or transmit hantavirus. Other rodent-associated "
        "diseases (e.g. Lyme, plague) involve arthropod vectors, but hantavirus is "
        "strictly an aerosol/contact pathogen.",
    ),
    (
        "How long does hantavirus survive on surfaces?",
        "In dried rodent excreta at room temperature, hantavirus remains viable "
        "for approximately 2-3 days. In cool, moist, dark conditions (basements, "
        "rodent-fouled sheds), viability can extend to over a week. UV light "
        "inactivates the virus within hours. A 10% household bleach solution is the "
        "CDC-recommended disinfectant.",
    ),
    (
        "Why is Andes virus the only hantavirus that spreads between people?",
        "The molecular basis is not fully resolved, but Andes virus has structural "
        "differences in its glycoproteins that allow it to replicate to higher "
        "titres in respiratory tissue compared to other hantaviruses. This produces "
        "more infectious respiratory droplets during the acute illness, enabling "
        "household transmission. Multiple Argentine and Chilean outbreaks have "
        "documented clear secondary case chains starting 14-25 days after the "
        "primary case.",
    ),
    (
        "Can you get hantavirus from drinking contaminated water?",
        "Hantavirus transmission via drinking water is theoretical and has not been "
        "convincingly documented as a major route. Municipal water-supply treatment "
        "inactivates the virus. Risk would be limited to severely contaminated raw "
        "water sources (e.g. an unfiltered cistern with rodent access). The dominant "
        "route remains inhalation of aerosolised excreta.",
    ),
    (
        "Is hantavirus airborne?",
        "Hantavirus is not airborne in the epidemiological sense of measles or "
        "tuberculosis — it does not float in room air or travel between rooms via "
        "HVAC. It IS aerosolised by mechanical disturbance of contaminated dust, "
        "producing a short-range aerosol that infects people in immediate proximity "
        "to the source. Practical implication: opening up a long-closed cabin "
        "without dampening the dust first is the classic high-risk scenario.",
    ),
    (
        "Can a doctor or nurse catch hantavirus from a patient?",
        "For all hantaviruses except Andes virus, no. For ANDV-HPS, yes — "
        "healthcare worker secondary cases have been documented, prompting standard "
        "droplet + contact precautions, FFP3/N95 respirator use, and where possible "
        "negative-pressure isolation. The MV Hondius 2026 cluster led UKHSA and ECDC "
        "to issue updated occupational guidance on ANDV contact precautions.",
    ),
    (
        "Where in the world is hantavirus most common?",
        "Hantavirus is endemic across most temperate and tropical regions, with "
        "specific high-incidence pockets: USA Four Corners (Sin Nombre); southern "
        "Chile and Argentina (Andes); Scandinavia and Germany (Puumala); China and "
        "Korea (Hantaan); the Balkans (Dobrava-Belgrade). See HORIZON's country "
        "pages for current authoritative-source case counts.",
    ),
]


# ---------------------------------------------------------------------------
# /hantavirus/prevention — extended
# ---------------------------------------------------------------------------

PREVENTION_EXT = """
<h2>Step-by-step rodent-contaminated cleanup protocol (CDC method)</h2>
<p>If you find evidence of rodent infestation (droppings, nests, urine
stains, gnaw marks, dead rodents) in a building, do NOT sweep or vacuum
without preparation. The CDC's evidence-based protocol — used as the
reference standard in occupational health worldwide — requires the
following steps in order.</p>
<ol>
<li><strong>Air out the space for at least 30 minutes</strong> before entry.
Open all windows and doors. Leave the area while it airs.</li>
<li><strong>Put on PPE</strong> before re-entering: disposable gloves
(nitrile or latex), an FFP3 or N95 respirator (not a surgical mask), eye
protection (goggles, not glasses), and a long-sleeved cover-up that can be
washed at high temperature afterwards.</li>
<li><strong>Spray, do not sweep.</strong> Mix a 10% bleach solution: 1 part
household bleach (5-6% sodium hypochlorite) to 9 parts cold water. Spray
heavily on all visible rodent droppings, urine spots, nesting material, and
the immediate surrounding area. Let soak for at least 5 minutes.</li>
<li><strong>Wipe up with disposable paper towels.</strong> Pick up
disinfected material with paper towels and place into a sealable plastic
bag. Double-bag and seal.</li>
<li><strong>Mop or sponge the entire floor</strong> of affected rooms with
bleach solution or a disinfectant cleaner.</li>
<li><strong>Wash bedding, clothing, and soft furnishings</strong> that may
have been exposed in hot water (60°C minimum) with normal detergent. Items
that cannot be washed should be sealed in bags and discarded.</li>
<li><strong>Disinfect hard surfaces</strong> (countertops, shelving) with a
disinfectant cleaner or bleach solution. Allow to air-dry.</li>
<li><strong>Remove PPE last.</strong> Take off gloves last so contaminated
hands never touch your face. Wash hands and forearms thoroughly with soap
and warm water. Shower as soon as practical and wash the clothing worn
during cleanup.</li>
<li><strong>Dispose of all cleanup waste</strong> in sealed bags in outdoor
bins, not indoor wastebaskets.</li>
</ol>
<p>For heavily contaminated structures (long-abandoned cabins, large
infestations), engage a licensed pest-control professional. The risk of HPS
from a single high-dose cleanup exposure is substantially higher than from
routine maintenance.</p>

<h2>Long-term rodent exclusion — preventing recurrence</h2>
<p>Cleanup addresses the immediate hazard; exclusion is what stops
recurrence. The CDC, the UK Health and Safety Executive, and the WHO all
agree on the same principles:</p>
<ul>
<li><strong>Seal entry points.</strong> Mice can squeeze through openings
as small as 6 mm (1/4 inch); rats need ~12 mm. Use steel wool stuffing
followed by caulk, expanding foam, or hardware cloth. Common entry points:
gaps around utility penetrations, under door sweeps, vent screens, foundation
cracks, soffit edges.</li>
<li><strong>Eliminate food sources.</strong> Store dry goods in heavy
plastic, glass, or metal containers with tight-fitting lids. Keep pet food
in sealed containers and never leave it out overnight. Empty bird feeders
and clean up spilled seed.</li>
<li><strong>Eliminate water sources.</strong> Fix leaking taps, drains, and
appliance seals. Cover toilet lids overnight in heavily infested
structures.</li>
<li><strong>Remove harbourage.</strong> Clear brush, wood piles, and dense
shrubs within 30 m of the building. Keep grass cut short. Eliminate
indoor clutter, especially in basements, attics, and garages.</li>
<li><strong>Trap, do not poison, where possible.</strong> Snap traps and
electronic traps allow safe disposal of carcasses; poisons leave dying
rodents in walls and crawlspaces where they decompose and may attract
secondary scavengers.</li>
<li><strong>Monitor.</strong> Place trail cameras or sticky monitor traps
along walls to detect activity early. New activity warrants escalation.</li>
</ul>

<h2>Outdoor and occupational exposure prevention</h2>
<p>Many HPS cases worldwide are not from cleanup but from occupational or
recreational outdoor exposure: agricultural work, hunting, conservation,
camping in cabins, opening seasonal accommodation, military deployment.
Specific precautions:</p>
<ul>
<li>Camping: choose tents over closed cabins where possible. If using a
cabin, air it out for 30 minutes before entry, inspect for rodent activity,
and treat any signs per the cleanup protocol above before settling in.</li>
<li>Agricultural work: store hay and grain at least 30 m from sleeping
quarters; rodent-proof grain silos with metal sheeting at the base.</li>
<li>Conservation and field biology: use HEPA-filtered respirators when
handling small mammals; sampling in known endemic areas should follow
American Society of Mammalogists ANSI-equivalent rodent-handling
guidelines.</li>
<li>Military and emergency response: deployed accommodation in endemic
areas should be inspected and cleared before occupancy. The US DoD CHPPM
TG-138 and equivalent UK MoD guidance cover this.</li>
<li>Travel to ANDV endemic regions (southern Chile/Argentina): avoid
remote cabins or shelters known to have rodent activity. Pack a basic PPE
kit (gloves, N95 mask, small bleach bottle) if planning rural overnight
stays.</li>
</ul>

<h2>Vaccine status — 2026</h2>
<p>No hantavirus vaccine is licensed in the UK, EU, USA, Canada, Australia,
or any major Western jurisdiction as of May 2026. A summary of the global
state:</p>
<table class="facts">
<thead><tr><th>Vaccine</th><th>Type</th><th>Status</th><th>Region</th></tr></thead>
<tbody>
<tr><th>Hantavax (Korea)</th><td>Inactivated whole-virus, HTNV</td><td>Licensed in South Korea since 1990</td><td>South Korea only; ~70% efficacy against HTNV-HFRS in field studies; no protection against HPS strains</td></tr>
<tr><th>Hantavac (China)</th><td>Inactivated bivalent HTNV+SEOV</td><td>Licensed in China</td><td>China only; reportedly used in agricultural workers in HTNV endemic provinces</td></tr>
<tr><th>DNA vaccine candidates (US)</th><td>DNA encoding GnGc glycoproteins</td><td>Phase 2 clinical trial (NIAID)</td><td>Targets ANDV and SNV; results from initial trials reported good immunogenicity but no efficacy endpoint yet</td></tr>
<tr><th>mRNA candidates (post-COVID)</th><td>Lipid-nanoparticle mRNA</td><td>Pre-clinical / Phase 1</td><td>Several groups (Moderna, BioNTech, US Army WRAIR) reportedly working on ANDV mRNA constructs; no Phase 3 timeline announced</td></tr>
<tr><th>Monoclonal antibodies (passive prophylaxis)</th><td>SNV- and ANDV-neutralising mAbs</td><td>Phase 1</td><td>Most advanced for ANDV post-exposure prophylaxis; targeting MV Hondius-style exposure scenarios</td></tr>
</tbody>
</table>
<p>Behavioural prevention remains the foundation of hantavirus risk
reduction. Vaccine policy in Europe and North America may shift if the MV
Hondius 2026 cluster prompts review.</p>

<h2>Prevention for travellers — country-specific guidance</h2>
<ul>
<li><strong>USA / Canada</strong>: CDC and Health Canada both publish guidance.
Highest-risk areas are the Four Corners region (AZ, CO, NM, UT) and
deer-mouse habitat across the rural southwest and northern interior.</li>
<li><strong>Chile / Argentina</strong>: Avoid remote cabins or shelters with
rodent activity. Pack a basic PPE kit if rural overnight stays are planned.
The Magallanes, Aysén, Patagonia, and Neuquén regions are highest risk.</li>
<li><strong>Scandinavia / Germany</strong>: Risk peaks in autumn/winter when
bank voles enter buildings. Standard cleanup precautions if dealing with
infested summer cottages.</li>
<li><strong>China / Korea</strong>: Agricultural workers should follow
national vaccination programmes where available (Hantavax in Korea, Hantavac
in China). Travellers in urban areas have minimal risk.</li>
<li><strong>UK / Ireland</strong>: Hantavirus is rare in the British Isles
and limited to Seoul virus from pet/wild brown rat exposure. UKHSA reports
under 10 confirmed cases annually.</li>
</ul>
"""

FAQ_PREVENTION = [
    (
        "How do you prevent hantavirus?",
        "Hantavirus prevention rests on three principles: (1) exclude rodents from "
        "the home by sealing entry points and removing food/water/harbourage; (2) "
        "clean rodent-contaminated areas using the CDC bleach + N95 protocol rather "
        "than sweeping or vacuuming; (3) avoid known endemic high-risk areas or use "
        "appropriate PPE when working in them. No licensed vaccine is available "
        "outside South Korea and China.",
    ),
    (
        "What is the CDC bleach protocol for hantavirus?",
        "The CDC protocol is: air out the space for 30+ minutes, put on PPE "
        "(N95/FFP3, gloves, eye protection), spray a 10% household bleach solution "
        "(1 part bleach to 9 parts water) on all droppings and urine spots, let "
        "soak 5 minutes, wipe up with paper towels into sealable bags, mop floors "
        "and disinfect hard surfaces, wash exposed bedding/clothes at 60°C, remove "
        "PPE last, shower, and dispose of all waste in outdoor bins.",
    ),
    (
        "Is there a hantavirus vaccine?",
        "Hantavax (Korea) and Hantavac (China) are licensed regionally but not "
        "available in the UK, EU, USA, Canada, or Australia. They target Hantaan "
        "and Seoul virus and offer no protection against HPS strains (Sin Nombre, "
        "Andes). Several DNA and mRNA candidates targeting Andes virus are in early "
        "clinical trials but no Phase 3 timeline has been announced as of May 2026.",
    ),
    (
        "How small a gap can a mouse fit through?",
        "House mice can squeeze through openings as small as 6 mm (1/4 inch); "
        "young mice can fit through even smaller gaps. Rats need approximately 12 "
        "mm (1/2 inch). Effective rodent-proofing requires sealing all openings "
        "above this threshold, including utility penetrations, vent screens, door "
        "sweeps, and foundation cracks. Steel wool followed by caulk or expanding "
        "foam is the standard exclusion material.",
    ),
    (
        "Can you sweep up mouse droppings safely?",
        "No. Sweeping or vacuuming (without a HEPA filter) aerosolises dried "
        "rodent excreta and is one of the highest-risk activities for hantavirus "
        "exposure. Always wet down droppings with a 10% bleach solution and allow "
        "5 minutes contact time before wiping up with paper towels. Wear an "
        "N95/FFP3 respirator and gloves throughout.",
    ),
    (
        "Are mouse traps better than poison for hantavirus prevention?",
        "Traps are preferred over poison when hantavirus risk is the primary "
        "concern. Snap traps and electronic traps allow immediate carcass disposal, "
        "preventing rodents from dying in walls and crawlspaces where decomposition "
        "draws secondary pests and prolongs contamination. Always handle carcasses "
        "with gloves and dispose in sealed bags.",
    ),
    (
        "Does an N95 mask prevent hantavirus?",
        "An N95 (US) or FFP3 (EU/UK) respirator is the CDC-recommended respiratory "
        "protection for hantavirus cleanup. Properly fit-tested, it filters 95% or "
        "more of the airborne particles that carry the virus during dust "
        "disturbance. A surgical or cloth mask is NOT adequate. The respirator must "
        "form a tight seal — beards or poor fit substantially reduce protection.",
    ),
    (
        "How often should I check for rodent signs at home?",
        "Inspect monthly in normal conditions, weekly during autumn (when rodents "
        "seek warm shelter), and immediately if you hear scratching in walls, find "
        "fresh droppings, smell ammonia in low-traffic areas, or notice gnaw marks "
        "on food packaging or wiring. Trail cameras or sticky monitor traps along "
        "walls give early warning of new activity.",
    ),
    (
        "Should I avoid Patagonia because of Andes virus?",
        "Travel to Chilean and Argentine Patagonia is not contraindicated by Andes "
        "virus. The risk to ordinary travellers in urban centres and major tourist "
        "areas is very low. The MV Hondius 2026 cluster was associated with a "
        "specific high-exposure activity (entering a rodent-infested off-season "
        "shelter), not routine travel. Standard precautions: avoid remote cabins "
        "with rodent activity, pack basic PPE if rural overnight stays are "
        "planned.",
    ),
    (
        "Can I get hantavirus from camping?",
        "Camping in tents in endemic areas is generally low-risk because tents are "
        "ventilated and rodents cannot easily access them. Sleeping in unmaintained "
        "trail shelters, cabins, or barns is higher risk. Always air the structure "
        "out for 30+ minutes before entry and inspect for rodent activity. If "
        "fresh droppings or nesting is present, do not stay or clean it using the "
        "CDC bleach protocol first.",
    ),
]


# ---------------------------------------------------------------------------
# /hantavirus/treatment — extended
# ---------------------------------------------------------------------------

TREATMENT_EXT = """
<h2>Hantavirus treatment overview — 2026 standard of care</h2>
<p>There is no licensed antiviral or specific therapy for hantavirus disease.
Treatment is intensive supportive care focused on the syndrome (HPS or HFRS)
and the patient's individual deterioration trajectory. Outcomes are strongly
dependent on early recognition and admission to a centre capable of advanced
critical care.</p>

<h2>Hantavirus Pulmonary Syndrome (HPS) — critical care pathway</h2>
<p>HPS deteriorates fast. The window from prodrome to respiratory failure
can be 12-48 hours once cough or breathlessness appears. Standard of care
emphasises early ICU admission, judicious fluid management, and immediate
access to ECMO where indicated.</p>
<ul>
<li><strong>Early ICU admission.</strong> Any patient with confirmed or
suspected HPS who is short of breath, tachypnoeic, or hypoxic should be
transferred to an ICU capable of mechanical ventilation and, ideally, ECMO
referral.</li>
<li><strong>Restrictive fluid management.</strong> HPS pulmonary oedema is
non-cardiogenic and capillary-leak-driven. Aggressive crystalloid
resuscitation worsens it. Vasopressors (noradrenaline first-line) are
preferred for haemodynamic support over volume.</li>
<li><strong>Lung-protective mechanical ventilation.</strong> Standard ARDS
strategy: 6 mL/kg tidal volume on predicted body weight, plateau pressure
&lt;30 cm H2O, permissive hypercapnia, prone positioning when refractory.</li>
<li><strong>Veno-venous ECMO.</strong> The single most important
intervention with outcome-changing data. Cohort studies from Chile, Argentina,
and the USA show ECMO halves HPS mortality in patients with refractory
hypoxia. Patients should be transferred to an ECMO centre BEFORE refractory
arrest. The 2026 update from the Argentine Society of Intensive Care
Medicine (SATI) recommends ECMO referral at PaO2/FiO2 ratio &lt;100 on
optimal ventilator settings.</li>
<li><strong>Vasoactive support.</strong> Noradrenaline first; vasopressin and
adrenaline as second-line. Inotropic support may be needed if cardiac
function is depressed (rare in HPS — most deterioration is vasoplegic
shock, not cardiogenic).</li>
<li><strong>Renal replacement therapy.</strong> CRRT (continuous
renal-replacement therapy) is used when AKI develops, which is common in
late HPS.</li>
<li><strong>Source control.</strong> No specific source control beyond
contact precautions for ANDV.</li>
</ul>

<h2>Haemorrhagic Fever with Renal Syndrome (HFRS) — phased treatment</h2>
<p>HFRS has a longer, more predictable course than HPS, which allows
phase-specific management. The five classical phases (febrile, hypotensive,
oliguric, diuretic, convalescent) each demand a different focus.</p>
<ul>
<li><strong>Febrile phase</strong>: paracetamol for fever, IV fluids if
dehydration, monitor platelet count. Consider ribavirin (see below).</li>
<li><strong>Hypotensive phase</strong>: cautious crystalloid resuscitation,
vasopressors as needed, ICU admission for severe cases. Avoid aggressive
volume that will worsen the later oliguric phase.</li>
<li><strong>Oliguric phase</strong>: fluid restriction, electrolyte
management, dialysis (haemodialysis or CRRT) commonly needed. Bleeding
management with platelet transfusions if active haemorrhage and
thrombocytopenia.</li>
<li><strong>Diuretic phase</strong>: anticipated polyuria can be 4-8 L/day.
Match fluid replacement to output, monitor electrolytes (especially
potassium and magnesium).</li>
<li><strong>Convalescent phase</strong>: gradual return to baseline. Some
patients develop long-term hypertension (Puumala) or chronic kidney
disease.</li>
</ul>

<h2>Ribavirin in hantavirus — evidence and indications</h2>
<p>Ribavirin is a nucleoside analogue with in-vitro activity against
multiple hantaviruses. Clinical evidence is mixed:</p>
<ul>
<li><strong>HFRS (Hantaan virus)</strong>: Chinese RCT data from the 1990s
showed mortality reduction when ribavirin was given within the first 4 days
of symptom onset. WHO and Korean clinical guidelines endorse early
ribavirin for HFRS.</li>
<li><strong>HPS (Sin Nombre, Andes)</strong>: a 2004 US RCT did not show
benefit for HPS. Subsequent observational data have been inconclusive.
Current US and Chilean clinical guidance does NOT routinely recommend
ribavirin for HPS, but some centres still use it in early disease (within
72 hours of symptom onset) on a compassionate-use basis.</li>
<li><strong>Side effects</strong>: haemolytic anaemia is dose-limiting.
Teratogenic — contraindicated in pregnancy and requires reliable
contraception for 6 months after treatment in both sexes.</li>
</ul>

<h2>Investigational therapies in 2026</h2>
<ul>
<li><strong>Monoclonal antibodies (ANDV)</strong>: several
neutralising-antibody candidates are in Phase 1/2 trials. The Chilean
group (Ferrés et al.) has reported on intravenous immunoglobulin from
ANDV convalescent donors with possible benefit when administered early in
contact-traced household cases.</li>
<li><strong>Favipiravir</strong>: in-vitro activity demonstrated. No
randomised clinical data in hantavirus disease.</li>
<li><strong>Vandetanib</strong>: a tyrosine kinase inhibitor with reported
in-vitro activity against ANDV; no human trial data.</li>
<li><strong>ECMO scale-up</strong>: the Chilean Ministry of Health
announced a network expansion in May 2026 to ensure 24-hour ECMO transfer
capability across Magallanes and Aysén in response to the MV Hondius
cluster.</li>
</ul>

<h2>Hantavirus prognosis and survival</h2>
<table class="facts">
<thead><tr><th>Serotype</th><th>Syndrome</th><th>Case-fatality rate (CFR)</th><th>Key prognostic factor</th></tr></thead>
<tbody>
<tr><th>Sin Nombre (SNV)</th><td>HPS</td><td>36-38%</td><td>Early ICU admission, ECMO availability</td></tr>
<tr><th>Andes (ANDV)</th><td>HPS</td><td>30-50%</td><td>ECMO referral before refractory shock</td></tr>
<tr><th>Puumala (PUUV)</th><td>HFRS (mild)</td><td>&lt;1%</td><td>Excellent prognosis with supportive care</td></tr>
<tr><th>Hantaan (HTNV)</th><td>HFRS (severe)</td><td>5-15%</td><td>Early ribavirin, dialysis access</td></tr>
<tr><th>Seoul (SEOV)</th><td>HFRS (mild)</td><td>&lt;1%</td><td>Self-limiting in most cases</td></tr>
<tr><th>Dobrava-Belgrade (DOBV)</th><td>HFRS (severe)</td><td>5-12%</td><td>Dialysis access, bleeding control</td></tr>
</tbody>
</table>

<h2>Rehabilitation after hantavirus</h2>
<p>Discharge from acute care is the start of recovery, not the end.
Hantavirus survivors face several rehabilitation challenges:</p>
<ul>
<li><strong>Pulmonary rehabilitation (HPS)</strong>: structured
exercise-based programmes for 6-12 weeks improve exercise tolerance and
quality of life. Patients should be screened with pulmonary function tests
at 6 weeks and 3 months post-discharge.</li>
<li><strong>Renal follow-up (HFRS)</strong>: serum creatinine and urinalysis
at 1 month, 3 months, and 12 months. Persistent proteinuria warrants
nephrology referral.</li>
<li><strong>Cardiac assessment (HPS)</strong>: echocardiogram if
post-discharge fatigue or exercise intolerance is disproportionate; some
ICU survivors have transient stress cardiomyopathy.</li>
<li><strong>Psychological support</strong>: ICU PTSD rates after
hantavirus are comparable to other severe-illness ICU stays (~20-30%).
Routine screening at 6-8 weeks post-discharge is recommended.</li>
<li><strong>Return to work</strong>: most patients can return to office or
light physical work at 6-8 weeks; heavy manual work usually requires 3-6
months.</li>
</ul>
"""

FAQ_TREATMENT = [
    (
        "Is there a cure for hantavirus?",
        "There is no licensed cure or specific antiviral for hantavirus disease. "
        "Treatment is intensive supportive care: ICU admission, lung-protective "
        "ventilation, vasopressors, ECMO for severe HPS, dialysis for HFRS-related "
        "kidney failure. Ribavirin has some benefit in early HFRS but is not "
        "routinely recommended for HPS. Outcomes depend heavily on early "
        "recognition and access to advanced critical care.",
    ),
    (
        "Does ECMO save lives in hantavirus?",
        "Yes. Cohort studies from Chile, Argentina, and the USA show veno-venous "
        "ECMO halves Hantavirus Pulmonary Syndrome mortality in patients with "
        "refractory hypoxia. The Argentine Society of Intensive Care Medicine "
        "(SATI) 2026 update recommends ECMO referral at PaO2/FiO2 ratio under 100 "
        "on optimal ventilator settings, ideally before refractory shock develops.",
    ),
    (
        "Does ribavirin work against hantavirus?",
        "Ribavirin has clinical-trial evidence for HFRS caused by Hantaan virus, "
        "where Chinese RCTs from the 1990s showed mortality reduction when given "
        "in the first 4 days of symptoms. For HPS (Sin Nombre, Andes), a 2004 US "
        "RCT did not show benefit. Current US and Chilean guidelines do not "
        "routinely recommend ribavirin for HPS, but some centres use it in early "
        "disease (within 72 hours) on a compassionate basis.",
    ),
    (
        "How long does hantavirus treatment last?",
        "Acute critical-care treatment for severe HPS averages 7-14 days in the "
        "ICU; severe HFRS can require 2-4 weeks of phased management through the "
        "febrile, hypotensive, oliguric, diuretic, and convalescent phases. Total "
        "hospital length of stay is typically 2-4 weeks. Rehabilitation continues "
        "for 6-12 months post-discharge.",
    ),
    (
        "What is the survival rate for hantavirus?",
        "Survival depends on the serotype and the care available. Sin Nombre HPS: "
        "62-64% survival. Andes HPS: 50-70% survival. Hantaan HFRS: 85-95% "
        "survival. Puumala HFRS: over 99% survival. Seoul HFRS: over 99% survival. "
        "Dobrava-Belgrade HFRS: 88-95% survival. Early ICU admission and ECMO "
        "availability are the strongest modifiable prognostic factors.",
    ),
    (
        "Can hantavirus be treated at home?",
        "No. Suspected hantavirus disease — even in its mild prodromal phase — "
        "requires immediate hospital assessment because of the risk of rapid "
        "deterioration to severe HPS or HFRS. Home management is unsafe. Patients "
        "with credible exposure plus fever should call emergency services and "
        "mention hantavirus exposure explicitly to ensure appropriate workup.",
    ),
    (
        "Are there any new hantavirus drugs in 2026?",
        "Yes — several investigational therapies are in early clinical trials. "
        "Neutralising monoclonal antibodies targeting Andes virus are in Phase 1/2 "
        "(Chilean and US groups). Favipiravir has in-vitro activity but no clinical "
        "trial data. Vandetanib (tyrosine kinase inhibitor) has reported in-vitro "
        "activity against ANDV but no human data. None are licensed for clinical "
        "use as of May 2026.",
    ),
    (
        "What aftercare is needed after recovering from hantavirus?",
        "Pulmonary function tests at 6 weeks and 3 months for HPS survivors; "
        "renal follow-up (creatinine, urinalysis) at 1, 3, and 12 months for HFRS "
        "survivors; cardiac assessment if post-discharge fatigue is severe; "
        "psychological support given ~20-30% ICU PTSD rate. Pulmonary "
        "rehabilitation programmes of 6-12 weeks substantially improve exercise "
        "tolerance.",
    ),
    (
        "How fast does hantavirus get worse?",
        "Once respiratory symptoms appear in HPS, deterioration can be rapid: "
        "12-48 hours from cough or breathlessness to respiratory failure. This is "
        "why early ICU admission before the cardiopulmonary phase is essential. "
        "HFRS has a slower, more predictable phased course over 2-4 weeks but can "
        "include life-threatening haemorrhage and shock during the oliguric phase.",
    ),
    (
        "Can pregnant women be treated for hantavirus?",
        "Pregnant women with hantavirus require specialist obstetric and ICU "
        "co-management. Ribavirin is teratogenic and contraindicated in pregnancy. "
        "ECMO has been used successfully in pregnant HPS patients. Andes virus has "
        "rare documented vertical transmission to the fetus during peri-partum "
        "maternal viraemia. Caesarean delivery is sometimes considered in late "
        "pregnancy with severe maternal HPS.",
    ),
]


# ---------------------------------------------------------------------------
# /outbreaks — extended (index page is critically thin at 159 words)
# ---------------------------------------------------------------------------

OUTBREAKS_INDEX_EXT = """
<h2>What counts as a hantavirus outbreak?</h2>
<p>HORIZON defines an outbreak as a temporally and geographically clustered
series of confirmed or strongly-suspected hantavirus cases that share a
common exposure source, a common reservoir population, or a documented
person-to-person transmission chain. Each tracked incident is curated from
WHO Disease Outbreak News, ECDC Communicable Disease Threats Reports, PAHO
weekly bulletins, national public-health authority statements, and
peer-reviewed virological reports. Single sporadic cases are tracked on the
<a href="/articles">articles archive</a>; outbreaks aggregate the related
cases into one ontology object with a stable URL.</p>

<h2>How HORIZON tracks an outbreak from first signal to closure</h2>
<ol>
<li><strong>Signal detection.</strong> The collection workers ingest from
65+ authoritative sources every 15 minutes. A new outbreak is flagged when
the ontology engine sees three or more case reports tagged to the same
country and serotype within a 14-day window, or when a Tier-1 source (WHO
DON, ECDC CDTR) publishes an explicit outbreak notification.</li>
<li><strong>Incident creation.</strong> Analysts review the flagged cluster
and create an incident record with: name, code (slug), primary serotype,
start date, status, and per-country expected case counts.</li>
<li><strong>Live corroboration.</strong> Subsequent reports referencing the
incident are auto-linked. The incident page lists the
authoritative-source history showing each update with its NATO Admiralty
Scale reliability and credibility rating.</li>
<li><strong>Status transitions.</strong> Outbreaks move from
<em>active</em> (case counts still rising) to <em>monitoring</em> (no new
cases reported, surveillance ongoing) to <em>resolved</em> (two full
incubation periods since the last confirmed case, with sustained absence
of new signals).</li>
<li><strong>Closure.</strong> Resolved outbreaks remain permanently
accessible at their stable URL with a final summary, all corroborating
articles archived for future analysis.</li>
</ol>

<h2>The 2026 outbreak landscape</h2>
<p>2026 has been dominated by the <strong>MV Hondius Andes virus
cluster</strong> — the first hantavirus outbreak linked to a cruise ship
and the most geographically distributed hantavirus cluster in surveillance
history. Returning passengers seeded incubating cases across multiple
continents before becoming symptomatic, prompting coordinated national
contact tracing in the UK, France, Germany, the Netherlands, Argentina,
Chile, and beyond.</p>
<p>Beyond MV Hondius, 2026 has shown the expected seasonal patterns:</p>
<ul>
<li><strong>Puumala virus seasonal activity</strong> in Finland, Sweden,
Germany, and Belgium, driven by the autumn bank-vole cycle.</li>
<li><strong>Sin Nombre virus sporadic cases</strong> across the US Four
Corners region, with the usual spring and early summer peak.</li>
<li><strong>Seoul virus pet-rat exposures</strong> in the UK and US,
documented in rat-breeder communities.</li>
<li><strong>Hantaan virus activity</strong> in rural China and Korea,
following the autumn harvest pattern.</li>
</ul>

<h2>Historical hantavirus outbreaks tracked by HORIZON</h2>
<p>The HORIZON ontology includes a curated set of historically significant
hantavirus clusters, used as comparators for current incidents:</p>
<ul>
<li><strong>Four Corners 1993</strong>: the original Sin Nombre virus
outbreak in the southwestern USA that led to the discovery of HPS as a
clinical entity.</li>
<li><strong>El Bolsón 1996 (Argentina)</strong>: the first documented Andes
virus person-to-person cluster.</li>
<li><strong>Epuyén 2018-2019 (Argentina)</strong>: a 34-case household
Andes virus cluster in Patagonia that reshaped public-health guidance on
ANDV contact tracing.</li>
<li><strong>Yosemite 2012 (USA)</strong>: a cluster of HPS cases linked to
visitor accommodation at Yosemite National Park; led to facility renovation
and revised park-service guidance.</li>
<li><strong>Belgium 2017</strong>: a Puumala virus outbreak season with
case counts exceeding 1,000 in a single year.</li>
<li><strong>Germany 2019</strong>: a Puumala virus year aligned with the
oak/beech mast cycle.</li>
</ul>

<h2>How to use this index</h2>
<p>Each card above links to a full incident page with:</p>
<ul>
<li>Live case, suspected, and death counts.</li>
<li>Per-country breakdown.</li>
<li>Authoritative-source history with NATO-scaled reliability.</li>
<li>Vessel and exposure context where relevant.</li>
<li>Corroborating article archive.</li>
<li>Long-form explainer and FAQ for high-profile clusters (e.g. MV Hondius).</li>
</ul>
<p>For machine-readable access to the incident data, see
<a href="/data">the open-data page</a> or query the
<a href="/api/v1/incidents">REST API endpoint</a> directly. All HORIZON
incident data is released under <a rel="license"
href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</p>
"""

FAQ_OUTBREAKS_INDEX = [
    (
        "What is the biggest hantavirus outbreak in 2026?",
        "The MV Hondius Andes virus cluster is the largest and most-tracked "
        "hantavirus outbreak of 2026 — also the first hantavirus cluster ever "
        "linked to a cruise ship. It originated from a pre-departure ecotourism "
        "excursion in Tierra del Fuego, Argentina in April 2026 and is being "
        "managed under a coordinated multi-country response.",
    ),
    (
        "How does HORIZON decide what counts as a hantavirus outbreak?",
        "HORIZON defines an outbreak as a temporally and geographically clustered "
        "series of confirmed or strongly-suspected hantavirus cases sharing a "
        "common exposure source, reservoir population, or person-to-person "
        "transmission chain. Detection threshold: 3+ case reports in the same "
        "country/serotype within a 14-day window, OR an explicit notification from "
        "WHO DON, ECDC CDTR, or equivalent Tier-1 source.",
    ),
    (
        "Where can I find historical hantavirus outbreaks?",
        "HORIZON's outbreak index includes the major historical clusters: Four "
        "Corners 1993 (original Sin Nombre outbreak), El Bolsón 1996 (first "
        "documented Andes virus P2P cluster), Epuyén 2018-2019 (34-case household "
        "ANDV cluster), Yosemite 2012, Belgium 2017 PUUV, Germany 2019 PUUV. Each "
        "has its own dedicated incident page.",
    ),
    (
        "How often are outbreak case counts updated?",
        "HORIZON re-checks all 65+ authoritative sources every 15 minutes. "
        "Outbreak case counts are updated when a new report from an authoritative "
        "source revises the figures. Each update is shown with its NATO Admiralty "
        "Scale source reliability rating on the incident's history table.",
    ),
    (
        "Can I download the outbreak data?",
        "Yes — all HORIZON incident data is open under CC BY 4.0. Bulk NDJSON "
        "export, JSON API, RSS/Atom feeds, and the REST API endpoint "
        "(/api/v1/incidents) are all available. The /data page documents the full "
        "schema and provides citation guidance.",
    ),
]


# ---------------------------------------------------------------------------
# /countries — extended (also thin at 386 words)
# ---------------------------------------------------------------------------

COUNTRIES_INDEX_EXT = """
<h2>Where in the world is hantavirus most common?</h2>
<p>Hantavirus is endemic on every inhabited continent, but specific regions
account for the majority of confirmed human cases each year. The geographic
distribution is fundamentally driven by the reservoir-rodent species — you
can only catch the virus where its host rodent lives — and by climate,
land use, and human-rodent contact patterns.</p>
<table class="facts">
<thead><tr><th>Region</th><th>Dominant serotype</th><th>Typical annual cases</th><th>Notes</th></tr></thead>
<tbody>
<tr><th>USA (Four Corners region)</th><td>Sin Nombre virus</td><td>30-60 confirmed HPS cases/year</td><td>CDC surveillance; case-fatality ~36%</td></tr>
<tr><th>USA (eastern + southern states)</th><td>Bayou, Black Creek Canal, NY-1</td><td>~10 cases/year</td><td>Sporadic, scattered geography</td></tr>
<tr><th>Canada</th><td>Sin Nombre virus</td><td>3-7 cases/year</td><td>Mostly prairie provinces; PHAC surveillance</td></tr>
<tr><th>Mexico</th><td>Sin Nombre + Andes-clade</td><td>10-30 cases/year</td><td>Northern Mexico, mostly Chihuahua and Sonora</td></tr>
<tr><th>Chile + Argentina (Patagonia)</th><td>Andes virus</td><td>100-150 cases/year combined</td><td>Magallanes, Aysén, Neuquén, Río Negro</td></tr>
<tr><th>Brazil</th><td>Multiple South American clades</td><td>50-100 cases/year</td><td>Highest in Mato Grosso, Paraná, Santa Catarina</td></tr>
<tr><th>Paraguay, Bolivia</th><td>Laguna Negra + Andes clade</td><td>20-40 cases/year</td><td>Underreporting suspected</td></tr>
<tr><th>Panama</th><td>Choclo virus</td><td>10-20 cases/year</td><td>Endemic to Los Santos province</td></tr>
<tr><th>Finland</th><td>Puumala virus</td><td>1,000-3,000 cases/year</td><td>Highest per-capita HFRS incidence in Europe</td></tr>
<tr><th>Sweden, Norway</th><td>Puumala virus</td><td>200-500 cases/year</td><td>Northern districts highest risk</td></tr>
<tr><th>Germany</th><td>Puumala virus</td><td>200-2,000 cases/year (cyclical)</td><td>Linked to oak/beech mast cycles</td></tr>
<tr><th>Belgium, Netherlands</th><td>Puumala virus</td><td>50-300 cases/year</td><td>Cyclical outbreak years</td></tr>
<tr><th>France</th><td>Puumala + Tula virus</td><td>100-200 cases/year</td><td>Northeast France highest incidence</td></tr>
<tr><th>Balkans (Serbia, Croatia, Bosnia, Slovenia)</th><td>Dobrava-Belgrade + Puumala</td><td>50-300 cases/year</td><td>DOBV is high-severity HFRS</td></tr>
<tr><th>Russia</th><td>Puumala + Hantaan + Far-Eastern strains</td><td>5,000-10,000 cases/year</td><td>Russian Federation leads global HFRS case count</td></tr>
<tr><th>China</th><td>Hantaan virus (dominant) + Seoul</td><td>10,000-30,000 cases/year</td><td>Largest absolute case load worldwide; vaccinated agricultural workers</td></tr>
<tr><th>South Korea</th><td>Hantaan virus</td><td>300-500 cases/year</td><td>Hantavax vaccine deployed since 1990</td></tr>
<tr><th>Japan</th><td>Seoul + Hantaan</td><td>Rare</td><td>Mostly pet/laboratory exposures</td></tr>
<tr><th>UK + Ireland</th><td>Seoul virus (rare)</td><td>&lt;10 cases/year</td><td>Pet brown rat and wild brown rat exposure</td></tr>
</tbody>
</table>

<h2>What drives the geographic variation?</h2>
<ul>
<li><strong>Reservoir host distribution.</strong> Each hantavirus has one
specific rodent species (or genus) as its primary reservoir. The virus
cannot establish where the rodent does not live. Deer mice in North
America; long-tailed pygmy rice rats in Patagonia; bank voles in Europe.</li>
<li><strong>Climate and ecology.</strong> Rodent population dynamics depend
on food availability (oak/beech mast cycles, agricultural yields), winter
severity, predator populations, and habitat conditions. Wet years often
precede higher case counts.</li>
<li><strong>Human-rodent contact patterns.</strong> Rural population
density, agricultural practices, housing quality, recreational land use,
and seasonal-cabin occupancy all influence exposure rates.</li>
<li><strong>Surveillance intensity.</strong> Reported case counts reflect
both true incidence and surveillance capacity. Some regions are likely
underreporting. HORIZON cross-references multiple authoritative sources to
mitigate this bias.</li>
</ul>

<h2>How HORIZON tracks each country</h2>
<p>Each country has a dedicated page (linked above) with:</p>
<ul>
<li>Current dominant serotype(s) and reservoir species.</li>
<li>Live case count from authoritative sources.</li>
<li>Time-series of ingested case reports.</li>
<li>National public-health authority links (CDC, ECDC, PAHO, UKHSA, RKI,
etc.).</li>
<li>Endemic-zone descriptions for travel-risk assessment.</li>
</ul>

<h2>Country coverage in the HORIZON dataset</h2>
<p>HORIZON tracks every country that has appeared in any of our 65+
authoritative-source feeds with at least one hantavirus case report. The
list grows as new sources are ingested and as case reports surface from
regions not previously represented. Use the cards above to navigate to any
country page, or query the <a href="/api/v1/cases">JSON API</a> with
country filter for direct data access.</p>
"""

FAQ_COUNTRIES_INDEX = [
    (
        "Which country has the most hantavirus cases?",
        "China reports the largest absolute number of hantavirus cases each year "
        "(10,000-30,000 HFRS cases annually, primarily Hantaan virus). Russia is "
        "second (5,000-10,000 cases combining Puumala and Far-Eastern strains). "
        "Finland has the highest per-capita HFRS incidence in Europe (1,000-3,000 "
        "Puumala virus cases per year).",
    ),
    (
        "Is hantavirus a problem in the UK?",
        "Hantavirus is rare in the UK. UKHSA reports under 10 confirmed cases "
        "annually, almost all caused by Seoul virus from pet brown rat or wild "
        "brown rat exposure. The UK has no endemic deer-mouse or bank-vole "
        "hantavirus reservoir. The MV Hondius 2026 cluster brought ANDV cases "
        "into the UK via returning passengers, requiring updated UKHSA guidance.",
    ),
    (
        "Where in the USA is hantavirus most common?",
        "The Four Corners region — where Arizona, Colorado, New Mexico, and Utah "
        "meet — is the historical Sin Nombre virus heartland and accounts for the "
        "largest fraction of US HPS cases. Other endemic states with regular "
        "cases include California (deer mouse populations), Montana, Wyoming, "
        "Idaho, and the prairie states. Eastern/southern hantaviruses (Bayou, "
        "Black Creek Canal) cause sporadic cases in Texas, Florida, and the "
        "Carolinas.",
    ),
    (
        "Is hantavirus common in Argentina?",
        "Argentina averages 80-120 confirmed Andes virus HPS cases per year, "
        "concentrated in the southern Patagonian provinces of Neuquén, Río Negro, "
        "Chubut, and Santa Cruz, plus the highland provinces of Salta and Jujuy "
        "(different ANDV clades). The MV Hondius 2026 cluster originated from "
        "exposure in Tierra del Fuego National Park.",
    ),
    (
        "Why is Finland's hantavirus rate so high?",
        "Finland reports the highest per-capita hantavirus rate in Europe because "
        "of (a) very high bank-vole densities driven by the country's extensive "
        "boreal forest, (b) widespread summer-cottage culture that puts people in "
        "vole habitat seasonally, and (c) high-quality surveillance and active "
        "reporting that captures cases that might go unreported elsewhere. The "
        "Puumala virus they carry is the mildest hantavirus, with case-fatality "
        "under 1%.",
    ),
]


# ---------------------------------------------------------------------------
# /hantavirus (hub) — extended
# ---------------------------------------------------------------------------

HANTAVIRUS_HUB_EXT = """
<h2>Hantavirus quick reference card</h2>
<table class="facts">
<thead><tr><th>Question</th><th>Answer</th></tr></thead>
<tbody>
<tr><th>What is hantavirus?</th><td>A family of rodent-borne RNA viruses (genus <em>Orthohantavirus</em>) causing two distinct diseases in humans.</td></tr>
<tr><th>Two clinical syndromes?</th><td>HPS (pulmonary, in the Americas) and HFRS (renal + haemorrhagic, in Eurasia).</td></tr>
<tr><th>How do humans get infected?</th><td>Inhaling aerosolised rodent excreta in enclosed spaces. Only Andes virus also transmits between people.</td></tr>
<tr><th>Incubation period?</th><td>1-8 weeks, median 2-4 weeks.</td></tr>
<tr><th>First symptoms?</th><td>Fever, severe muscle aches, headache, fatigue, GI symptoms — flu-like prodrome lasting 3-7 days.</td></tr>
<tr><th>Mortality rate?</th><td>Sin Nombre HPS: 36-38%. Andes HPS: 30-50%. Puumala HFRS: under 1%. Hantaan HFRS: 5-15%.</td></tr>
<tr><th>Treatment?</th><td>Intensive supportive care. No licensed antiviral. ECMO halves HPS mortality. Ribavirin helps early HFRS.</td></tr>
<tr><th>Vaccine?</th><td>None licensed in the UK, EU, USA, Canada, or Australia. Korea (Hantavax) and China (Hantavac) have regional vaccines.</td></tr>
<tr><th>Prevention?</th><td>Rodent exclusion at home; CDC bleach protocol for cleanup; PPE when entering known-infested structures.</td></tr>
<tr><th>Is it contagious?</th><td>No, except Andes virus, which has documented household-contact person-to-person transmission.</td></tr>
</tbody>
</table>

<h2>The hantavirus family — a complete serotype map</h2>
<p>HORIZON tracks 12+ orthohantavirus serotypes of human-health relevance.
Each has a dedicated page with reservoir species, endemic range, clinical
syndrome, and CFR.</p>
<table class="facts">
<thead><tr><th>Serotype</th><th>Region</th><th>Reservoir</th><th>Syndrome</th><th>CFR</th></tr></thead>
<tbody>
<tr><th><a href="/hantavirus/sin-nombre-virus">Sin Nombre (SNV)</a></th><td>USA, Canada, northern Mexico</td><td>Deer mouse</td><td>HPS</td><td>36-38%</td></tr>
<tr><th><a href="/hantavirus/andes-virus">Andes (ANDV)</a></th><td>Chile, Argentina (Patagonia)</td><td>Long-tailed pygmy rice rat</td><td>HPS (with P2P)</td><td>30-50%</td></tr>
<tr><th><a href="/hantavirus/puumala-virus">Puumala (PUUV)</a></th><td>Northern + central Europe</td><td>Bank vole</td><td>HFRS (mild)</td><td>&lt;1%</td></tr>
<tr><th><a href="/hantavirus/hantaan-virus">Hantaan (HTNV)</a></th><td>China, Korea, Russian Far East</td><td>Striped field mouse</td><td>HFRS (severe)</td><td>5-15%</td></tr>
<tr><th><a href="/hantavirus/seoul-virus">Seoul (SEOV)</a></th><td>Worldwide via shipping</td><td>Brown rat</td><td>HFRS (mild)</td><td>&lt;1%</td></tr>
<tr><th><a href="/hantavirus/dobrava-belgrade-virus">Dobrava-Belgrade (DOBV)</a></th><td>Balkans, eastern Europe</td><td>Yellow-necked mouse</td><td>HFRS (severe)</td><td>5-12%</td></tr>
<tr><th><a href="/hantavirus/laguna-negra-virus">Laguna Negra (LANV)</a></th><td>Paraguay, Bolivia, Argentina</td><td>Vesper mouse</td><td>HPS</td><td>~12%</td></tr>
<tr><th><a href="/hantavirus/choclo-virus">Choclo (CHOV)</a></th><td>Panama</td><td>Costa Rican pygmy rice rat</td><td>HPS (mild)</td><td>~10%</td></tr>
<tr><th><a href="/hantavirus/bayou-virus">Bayou (BAYV)</a></th><td>Southeastern USA</td><td>Marsh rice rat</td><td>HPS</td><td>~33%</td></tr>
<tr><th><a href="/hantavirus/black-creek-canal-virus">Black Creek Canal (BCCV)</a></th><td>Florida, southeastern USA</td><td>Cotton rat</td><td>HPS</td><td>Rare cases</td></tr>
<tr><th><a href="/hantavirus/new-york-virus">New York virus (NY-1)</a></th><td>Northeastern USA</td><td>White-footed mouse</td><td>HPS</td><td>Rare cases</td></tr>
<tr><th><a href="/hantavirus/tula-virus">Tula (TULV)</a></th><td>Europe, central Asia</td><td>European common vole</td><td>HFRS (mild, rare)</td><td>&lt;1%</td></tr>
</tbody>
</table>

<h2>Hantavirus in 2026 — what changed</h2>
<p>The MV Hondius cluster, which began in April 2026, is the defining
hantavirus event of the year. Specifically:</p>
<ul>
<li>First hantavirus outbreak ever associated with a cruise ship.</li>
<li>Most geographically dispersed hantavirus cluster on record — passengers
returned to home countries before becoming symptomatic, distributing
incubating cases across at least three continents.</li>
<li>Forced clinical guidance updates from UKHSA, ECDC, and RIVM on Andes
virus diagnosis in non-endemic settings.</li>
<li>Triggered the Chilean Ministry of Health to expand 24-hour ECMO
transfer capability in Magallanes and Aysén.</li>
<li>Spurred renewed investment in Andes virus monoclonal-antibody and
mRNA-vaccine candidates.</li>
</ul>

<h2>Where to go from here</h2>
<ul>
<li><a href="/hantavirus/2026">2026 outbreak hub →</a></li>
<li><a href="/outbreaks/mv-hondius-2026">MV Hondius full incident page →</a></li>
<li><a href="/hantavirus/symptoms">Detailed symptom guide →</a></li>
<li><a href="/hantavirus/transmission">Full transmission inventory →</a></li>
<li><a href="/hantavirus/prevention">CDC prevention protocol →</a></li>
<li><a href="/hantavirus/treatment">Treatment and survival data →</a></li>
<li><a href="/timeline">Interactive 2026 timeline →</a></li>
<li><a href="/chronology">90-day outbreak chronology →</a></li>
<li><a href="/data">Open dataset and API →</a></li>
</ul>
"""

FAQ_HANTAVIRUS_HUB = [
    (
        "What is hantavirus disease?",
        "Hantavirus disease is the clinical illness caused by infection with any "
        "of the orthohantaviruses, a family of rodent-borne RNA viruses. Humans "
        "develop one of two distinct syndromes depending on the strain: "
        "Hantavirus Pulmonary Syndrome (HPS) in the Americas, with case-fatality "
        "30-50%; or Haemorrhagic Fever with Renal Syndrome (HFRS) across Eurasia, "
        "with case-fatality ranging from under 1% (Puumala) to 15% (Hantaan).",
    ),
    (
        "How many people get hantavirus each year?",
        "Global incidence is approximately 150,000-200,000 cases per year, with "
        "the vast majority being HFRS in China (10,000-30,000), Russia "
        "(5,000-10,000), and Korea (300-500). HPS in the Americas is much rarer "
        "in absolute terms (under 1,000 confirmed cases per year worldwide) but "
        "has much higher case-fatality. Real incidence is higher than reported "
        "because of underreporting in lower-surveillance regions.",
    ),
    (
        "Is hantavirus a serious disease?",
        "Yes. Hantavirus Pulmonary Syndrome has case-fatality 30-50% and "
        "deteriorates rapidly once respiratory symptoms appear. Even mild "
        "hantavirus disease (Puumala HFRS, Seoul virus) typically involves "
        "hospital admission. Survivors can have long-term pulmonary or renal "
        "sequelae. Early recognition and intensive critical care are essential.",
    ),
    (
        "Where does hantavirus come from?",
        "Hantavirus has co-evolved with specific rodent species over millions of "
        "years. Each serotype has one primary reservoir rodent. Sin Nombre virus "
        "lives in deer mice; Andes virus in long-tailed pygmy rice rats; Puumala "
        "virus in bank voles; Hantaan virus in striped field mice. The virus is "
        "shed in rodent urine, faeces, and saliva, contaminating the environment "
        "wherever the rodent lives.",
    ),
    (
        "What's the difference between HPS and HFRS?",
        "HPS (Hantavirus Pulmonary Syndrome) is the New World form, caused mainly "
        "by Sin Nombre and Andes virus. After a flu-like prodrome, it progresses "
        "to rapid-onset non-cardiogenic pulmonary oedema with shock. Case-fatality "
        "30-50%. HFRS (Haemorrhagic Fever with Renal Syndrome) is the Old World "
        "form, caused by Hantaan, Puumala, Seoul, and Dobrava-Belgrade. It "
        "progresses through five phases ending in acute kidney injury and possible "
        "haemorrhage. Case-fatality varies from under 1% (Puumala) to 15% (Hantaan).",
    ),
    (
        "Is there a hantavirus pandemic risk?",
        "Hantavirus is unlikely to cause a true pandemic because all serotypes "
        "except Andes virus require rodent contact for transmission and cannot "
        "spread between people. Andes virus CAN transmit between people but only "
        "via close household contact during the acute illness, which limits "
        "outbreak size. The MV Hondius 2026 cluster has not exceeded ~30 confirmed "
        "cases despite passenger dispersal across continents — secondary "
        "transmission has been limited.",
    ),
]
