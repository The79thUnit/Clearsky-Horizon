/**
 * Resources — curated authoritative reference links for hantavirus.
 *
 * Every link below points to an authoritative public health body or
 * peer-reviewed reference. We do NOT mirror or reproduce their content here;
 * we link directly to the canonical URL so that the visitor always reads the
 * most current version from the authority itself. This is the right pattern
 * for medical / public-health information: cite, don't paraphrase.
 */

interface Resource {
  org: string
  title: string
  url: string
  blurb: string
  tags: string[]
}

const SECTIONS: { name: string; items: Resource[] }[] = [
  {
    name: 'Active outbreak — MV Hondius cluster (2026)',
    items: [
      {
        org: 'WHO',
        title: 'Disease Outbreak News 2026-DON600 — Andes hantavirus, MV Hondius',
        url: 'https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON600',
        blurb: 'Authoritative situation report. Case definitions, cumulative counts, IHR notification status, recommendations to Member States.',
        tags: ['DON', 'A1'],
      },
      {
        org: 'ECDC',
        title: 'Andes hantavirus outbreak — surveillance and updates',
        url: 'https://www.ecdc.europa.eu/en/infectious-disease-topics/hantavirus-infection/surveillance-and-updates/andes-hantavirus-outbreak',
        blurb: 'European Centre for Disease Prevention and Control surveillance hub. EU/EEA case attribution, contact tracing across Member States.',
        tags: ['surveillance', 'A2'],
      },
      {
        org: 'UKHSA',
        title: 'UKHSA update on the hantavirus cruise ship outbreak',
        url: 'https://www.gov.uk/government/organisations/uk-health-security-agency',
        blurb: 'UK Health Security Agency operational updates. Arrowe Park Hospital isolation arrangements for UK-national passengers.',
        tags: ['UK', 'A1'],
      },
      {
        org: 'PAHO',
        title: 'PAHO Epidemiological Alert — Hantavirus',
        url: 'https://www.paho.org/en/topics/hantavirus',
        blurb: 'Pan American Health Organization hub. Argentina origin investigation, regional response.',
        tags: ['Americas', 'A1'],
      },
    ],
  },
  {
    name: 'CDC clinical & surveillance',
    items: [
      {
        org: 'CDC',
        title: 'CDC Hantavirus Home',
        url: 'https://www.cdc.gov/hantavirus/index.html',
        blurb: 'Centre for Disease Control & Prevention overview: clinical presentation, transmission, prevention, statistics.',
        tags: ['clinical', 'A1'],
      },
      {
        org: 'CDC',
        title: 'CDC Hantavirus Surveillance (Hantavirus Pulmonary Syndrome)',
        url: 'https://www.cdc.gov/hantavirus/php/surveillance/index.html',
        blurb: 'US HPS national surveillance data: case counts by year, state, age, sex. Source data for cumulative US epidemiology.',
        tags: ['surveillance', 'US', 'A1'],
      },
      {
        org: 'CDC',
        title: 'Hantavirus for clinicians',
        url: 'https://www.cdc.gov/hantavirus/hcp/clinical-overview/index.html',
        blurb: 'Diagnostic algorithm, lab testing (IgM ELISA + RT-PCR), supportive care, reporting requirements.',
        tags: ['clinical', 'A1'],
      },
      {
        org: 'CDC EID',
        title: 'CDC Emerging Infectious Diseases journal',
        url: 'https://wwwnc.cdc.gov/eid/',
        blurb: 'CDC peer-reviewed journal of record for emerging infections. Hantavirus papers searchable.',
        tags: ['peer-reviewed', 'A1'],
      },
    ],
  },
  {
    name: 'Virology & reservoir biology',
    items: [
      {
        org: 'ICTV',
        title: 'International Committee on Taxonomy of Viruses — Orthohantavirus',
        url: 'https://ictv.global/taxonomy',
        blurb: 'Authoritative taxonomy of orthohantavirus species. Names: Andes, Sin Nombre, Puumala, Hantaan, Seoul, Dobrava-Belgrade, etc.',
        tags: ['taxonomy', 'A1'],
      },
      {
        org: 'GBIF',
        title: 'Oligoryzomys longicaudatus (long-tailed pygmy rice rat) — GBIF',
        url: 'https://www.gbif.org/species/2438009',
        blurb: 'Global Biodiversity Information Facility records of the natural Andes hantavirus reservoir. Distribution maps across Patagonia.',
        tags: ['reservoir', 'B2'],
      },
      {
        org: 'iNaturalist',
        title: 'Peromyscus maniculatus (deer mouse) — iNaturalist',
        url: 'https://www.inaturalist.org/taxa/46259',
        blurb: 'Citizen-science observations of the Sin Nombre virus reservoir (North America).',
        tags: ['reservoir', 'C3'],
      },
    ],
  },
  {
    name: 'Peer-reviewed literature',
    items: [
      {
        org: 'NIH',
        title: 'PubMed — Hantavirus / Orthohantavirus literature',
        url: 'https://pubmed.ncbi.nlm.nih.gov/?term=hantavirus',
        blurb: 'NCBI biomedical literature index, MeSH-tagged. The starting point for any hantavirus research question.',
        tags: ['peer-reviewed', 'A1'],
      },
      {
        org: 'Eurosurveillance',
        title: 'Eurosurveillance — European communicable disease weekly',
        url: 'https://www.eurosurveillance.org/',
        blurb: 'ECDC peer-reviewed open-access journal. Outbreak case series + epidemiological methods.',
        tags: ['peer-reviewed', 'A1'],
      },
      {
        org: 'Lancet ID',
        title: 'The Lancet Infectious Diseases',
        url: 'https://www.thelancet.com/journals/laninf/',
        blurb: 'Top-tier peer-reviewed infectious disease journal.',
        tags: ['peer-reviewed', 'A1'],
      },
    ],
  },
  {
    name: 'Outbreak intelligence aggregators',
    items: [
      {
        org: 'ProMED',
        title: 'ProMED-mail — International Society for Infectious Diseases',
        url: 'https://promedmail.org/',
        blurb: '24/7 expert-curated outbreak alert system. The "first call" historically for emerging infectious disease signals.',
        tags: ['aggregator', 'B2'],
      },
      {
        org: 'HealthMap',
        title: 'HealthMap (Boston Children\'s Hospital)',
        url: 'https://www.healthmap.org/',
        blurb: 'Automated aggregation of news + ProMED + WHO. Multilingual outbreak monitoring.',
        tags: ['aggregator', 'B2'],
      },
      {
        org: 'CIDRAP',
        title: 'CIDRAP News — University of Minnesota',
        url: 'https://www.cidrap.umn.edu/news-perspective',
        blurb: 'Editorial outbreak coverage and policy analysis. Gold standard for English-language public-health journalism.',
        tags: ['news', 'B2'],
      },
    ],
  },
  {
    name: 'Open data',
    items: [
      {
        org: 'HORIZON',
        title: 'HORIZON open data — /api/v1/',
        url: 'https://hantavirus.software/api/openapi.json',
        blurb: 'Our own open API. Cases, clusters, sources, incidents, ontology. CC BY 4.0. No registration, no rate-limit beyond polite use.',
        tags: ['API', 'open data'],
      },
      {
        org: 'GISAID',
        title: 'GISAID — Global Initiative on Sharing All Influenza Data (and others)',
        url: 'https://gisaid.org/',
        blurb: 'Sequence sharing platform. Login required. Submission-vetted virus genomes including emerging orthohantaviruses.',
        tags: ['sequence', 'A2'],
      },
    ],
  },
]

export default function Resources() {
  return (
    <article className="resources">
      <header className="resources-header">
        <h1>Resources</h1>
        <p className="lead">
          Curated authoritative references for hantavirus. We link directly to the source
          rather than reproduce content here — always read the canonical version from the
          authority that publishes it. Tags identify NATO Admiralty Scale rating where
          applicable.
        </p>
      </header>

      {SECTIONS.map((s) => (
        <section key={s.name} className="resources-section">
          <h2>{s.name}</h2>
          <ul className="resources-list">
            {s.items.map((r) => (
              <li key={r.url} className="resources-item">
                <a className="resources-link" href={r.url} target="_blank" rel="noopener noreferrer">
                  <span className="resources-org">{r.org}</span>
                  <span className="resources-title">{r.title}</span>
                </a>
                <p className="resources-blurb">{r.blurb}</p>
                <div className="resources-tags">
                  {r.tags.map((t) => (
                    <span key={t} className="resources-tag">{t}</span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <footer className="resources-footer">
        <p>
          Missing a source you trust? Email <a href="mailto:HORIZON@79thunit.com">HORIZON@79thunit.com</a>
          with the URL and we will review for inclusion.
        </p>
      </footer>
    </article>
  )
}
