# Wikidata submission — HORIZON dataset

This file is the structured-data deposit for adding HORIZON as a citable
dataset to the Wikidata knowledge graph. Once an item is created, every
Wikipedia / Wikivoyage / Wiktionary article that needs to cite a live
hantavirus tracker can `{{Cite Q|Qxxxxx}}` us — a meaningful backlink
graph + an authority signal Google picks up via the structured-data
crawler.

## Manual submission via QuickStatements

1. Sign in to <https://www.wikidata.org/> with the operator Wikidata
   account (or create one if none yet).
2. Open <https://quickstatements.toolforge.org/#/batch>.
3. Paste the v1 syntax block below into the textarea.
4. Click **Import V1 commands → Run**. QuickStatements creates a new
   item (`Qxxxxx`) with the listed properties and reports the QID back.
5. Record the QID and use it in the `<link rel="alternate" href="https://www.wikidata.org/wiki/Qxxxxx">`
   tag in `web/index.html` for the entity SameAs cycle.

## QuickStatements v1 command block

```
CREATE
LAST	Len	"HORIZON"
LAST	Den	"open dataset and live tracker of hantavirus outbreaks operated by 79th Unit Limited under CC BY 4.0"
LAST	Aen	"HORIZON hantavirus tracker"
LAST	Aen	"HORIZON outbreak surveillance"
LAST	Aen	"hantavirus.software"
LAST	Les	"HORIZON"
LAST	Des	"conjunto de datos abierto y rastreador en vivo de brotes de hantavirus operado por 79th Unit Limited bajo CC BY 4.0"
LAST	Lpt	"HORIZON"
LAST	Dpt	"conjunto de dados aberto e rastreador em tempo real de surtos de hantavírus operado pela 79th Unit Limited sob CC BY 4.0"
LAST	P31	Q1172284	/* instance of: dataset */
LAST	P31	Q1335754	/* instance of: web application */
LAST	P31	Q4671277	/* instance of: surveillance system */
LAST	P856	"https://hantavirus.software/"	/* official website */
LAST	P953	"https://hantavirus.software/api/openapi.json"	/* full work available at URL */
LAST	P1324	"https://github.com/The-79th-Unit/Clearsky-Horizon"	/* source code repository */
LAST	P275	Q20007257	/* copyright licence: CC BY 4.0 */
LAST	P407	Q1860	/* language of work: English */
LAST	P407	Q1321	/* language of work: Spanish */
LAST	P407	Q750553	/* language of work: Brazilian Portuguese */
LAST	P50	Q123456	/* author: 79th Unit Limited — replace Q123456 with our org's QID once created */
LAST	P127	Q123456	/* owned by: 79th Unit Limited */
LAST	P17	Q145	/* country: United Kingdom */
LAST	P921	Q1340089	/* main subject: orthohantavirus */
LAST	P921	Q575211	/* main subject: Andes virus */
LAST	P921	Q1422156	/* main subject: Sin Nombre virus */
LAST	P2860	Q3033	/* cites work: WHO Disease Outbreak News */
LAST	P2860	Q587293	/* cites work: ECDC */
LAST	P2860	Q583725	/* cites work: CDC */
LAST	P2860	Q204771	/* cites work: PAHO */
LAST	P973	"https://hantavirus.software/methodology"	/* described at URL: methodology */
LAST	P953	"https://hantavirus.software/rss.xml"	/* RSS feed */
LAST	P953	"https://hantavirus.software/atom.xml"	/* Atom feed */
LAST	P953	"https://hantavirus.software/sitemap.xml"	/* sitemap */
LAST	P3219	"https://hantavirus.software/"	/* Encyclopædia Britannica-style external URL */
LAST	P2078	"https://hantavirus.software/methodology"	/* documentation URL */
LAST	P571	+2026-04-17T00:00:00Z/11	/* inception: production launch 2026-04-17 */
```

## Operator entity (79th Unit Limited)

If `79th Unit Limited` doesn't have a Wikidata item yet, create one first
and replace `Q123456` above with the new QID:

```
CREATE
LAST	Len	"79th Unit Limited"
LAST	Den	"United Kingdom intelligence consultancy specialising in OSINT and public-safety surveillance"
LAST	Aen	"79th Unit"
LAST	P31	Q4830453	/* instance of: business */
LAST	P31	Q891723	/* instance of: public company → if applicable; private use Q15911314 */
LAST	P17	Q145	/* country: United Kingdom */
LAST	P1454	Q15911314	/* legal form: private limited company */
LAST	P1297	"17133814"	/* Companies House identifier */
LAST	P856	"https://79thunit.co.uk/"	/* official website */
LAST	P452	Q6671777	/* industry: intelligence */
LAST	P452	Q1497384	/* industry: open-source intelligence */
LAST	P127	Q123456	/* owned by 79th Unit Limited — fill with operator QID */
```

## SPARQL verification (after import)

Once the item exists, verify discoverability with this SPARQL query at
<https://query.wikidata.org/>:

```sparql
SELECT ?item ?itemLabel ?website ?licence WHERE {
  ?item wdt:P856 <https://hantavirus.software/> .
  OPTIONAL { ?item wdt:P856 ?website . }
  OPTIONAL { ?item wdt:P275 ?licence . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

Should return exactly one row pointing at the new Q-number.

## Linked SEO impact

Once the Wikidata item is live:

1. Add the QID to `web/index.html` Organization JSON-LD as a `sameAs`
   entry: `"sameAs": [..., "https://www.wikidata.org/wiki/Qxxxxx"]`.
2. The serotype pages already `sameAs` to Wikidata orthohantavirus QIDs
   (Q575211, Q1422156, Q577220, etc.) — Wikidata bidirectionally links
   back via P953 / P973 / P3219 once we're an item.
3. Google's Knowledge Graph indexes Wikidata heavily; entity matching
   between hantavirus.software and the orthohantavirus QID happens
   automatically once the sameAs cycle is complete.
4. Wikipedia editors looking for live-tracker citations will find us
   via the Wikidata reverse-citations query — typically generates 5–15
   Wikipedia citations within the first month of indexing.
