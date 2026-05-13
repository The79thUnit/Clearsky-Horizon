import { useEffect, useState } from 'react'
import type { EntityRecord, IncidentOntology } from '../types'
import { fetchIncidentOntology } from '../api'

interface Props {
  incidentCode: string
}

export default function PatientZeroPanel({ incidentCode }: Props) {
  const [ontology, setOntology] = useState<IncidentOntology | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchIncidentOntology(incidentCode)
      .then(setOntology)
      .catch((e: unknown) => setError(String(e)))
  }, [incidentCode])

  if (error) return null
  if (!ontology) return null

  const persons = ontology.entities.filter((e) => e.entity_type === 'person')
  const excursion = ontology.entities.find((e) => e.entity_type === 'excursion')
  const vessel = ontology.entities.find((e) => e.entity_type === 'vessel')
  const voyage = ontology.entities.find((e) => e.entity_type === 'voyage')
  const ports = ontology.entities.filter((e) => e.entity_type === 'port')

  if (persons.length === 0) return null

  return (
    <section className="patient-zero-panel">
      <header className="pz-header">
        <h3>Patient zero &amp; chain of transmission</h3>
        <span className="pz-source-note">
          {ontology.entities.length} entities, {ontology.relationships.length} relationships
        </span>
      </header>

      {excursion && <ExcursionCard ent={excursion} />}

      <div className="pz-person-row">
        {persons.map((p) => (
          <PersonCard key={p.id} ent={p} />
        ))}
      </div>

      {voyage && vessel && ports.length > 0 && (
        <VoyageTimeline vessel={vessel} voyage={voyage} ports={ports} />
      )}
    </section>
  )
}

function PersonCard({ ent }: { ent: EntityRecord }) {
  const p = ent.properties as Record<string, string | number | null>
  return (
    <article className="pz-person">
      <h4 className="pz-person-label">{ent.public_label}</h4>
      <dl className="pz-attrs">
        <Row k="Sex / age" v={`${p.sex ?? '-'} / ${p.age ?? '-'}`} />
        <Row k="Nationality" v={p.nationality_iso2 ?? '-'} />
        <Row k="Role" v={p.role ?? '-'} />
        <Row k="Case status" v={p.case_status ?? '-'} highlight />
        <Row k="Serotype" v={p.serotype ?? '-'} />
        {p.symptoms_onset && <Row k="Symptoms onset" v={p.symptoms_onset} />}
        {p.symptoms_initial && <Row k="Initial symptoms" v={p.symptoms_initial} />}
        {p.disembarked_at_port && <Row k="Disembarked" v={`${p.disembarked_at_port} on ${p.disembarked_at_date ?? '-'}`} />}
        {p.died_at && <Row k="Died" v={`${p.died_at} (${p.died_location ?? 'unknown'})`} critical />}
        {p.pcr_status && <Row k="PCR status" v={p.pcr_status} />}
      </dl>
      {p.narrative && (
        <p className="pz-narrative">{p.narrative}</p>
      )}
    </article>
  )
}

function ExcursionCard({ ent }: { ent: EntityRecord }) {
  const p = ent.properties as Record<string, string | null>
  return (
    <div className="pz-excursion">
      <span className="pz-excursion-label">Suspected exposure</span>
      <h4>{ent.public_label}</h4>
      <dl className="pz-attrs pz-attrs-row">
        {p.location_name && <Row k="Location" v={p.location_name} />}
        {p.region && <Row k="Region" v={p.region} />}
        {p.activity && <Row k="Activity" v={p.activity} />}
        {p.date_window_start && (
          <Row k="Window" v={`${p.date_window_start} → ${p.date_window_end ?? '-'}`} />
        )}
        {p.suspected_reservoir && <Row k="Reservoir" v={p.suspected_reservoir} />}
        {p.serotype && <Row k="Serotype" v={p.serotype} />}
      </dl>
      {p.notes && <p className="pz-narrative">{p.notes}</p>}
    </div>
  )
}

function VoyageTimeline({
  vessel,
  voyage,
  ports,
}: {
  vessel: EntityRecord
  voyage: EntityRecord
  ports: EntityRecord[]
}) {
  const v = vessel.properties as Record<string, string | number | null>
  const j = voyage.properties as Record<string, string | null>
  return (
    <div className="pz-voyage">
      <header>
        <h4>Voyage: {voyage.public_label}</h4>
        <span className="pz-source-note">
          {vessel.public_label} &middot; IMO {v.imo ?? '-'} &middot; MMSI {v.mmsi ?? '-'} &middot; flag {v.flag_iso2 ?? '-'}
        </span>
      </header>
      <ol className="pz-port-list">
        <li className="pz-port-item">
          <span className="pz-port-date">{j.departed_at ?? '-'}</span>
          <span className="pz-port-name">Depart {j.departed_port}</span>
        </li>
        {ports
          .filter((p) => p.public_label !== j.departed_port && p.public_label !== j.arrived_port)
          .map((p) => (
            <li key={p.id} className="pz-port-item">
              <span className="pz-port-date">port call</span>
              <span className="pz-port-name">{p.public_label}</span>
            </li>
          ))}
        <li className="pz-port-item pz-port-arrived">
          <span className="pz-port-date">{j.arrived_at ?? '-'}</span>
          <span className="pz-port-name">Arrive {j.arrived_port}</span>
        </li>
      </ol>
    </div>
  )
}

function Row({
  k,
  v,
  highlight,
  critical,
}: {
  k: string
  v: string | number | null
  highlight?: boolean
  critical?: boolean
}) {
  return (
    <>
      <dt>{k}</dt>
      <dd className={critical ? 'critical' : highlight ? 'highlight' : ''}>{v ?? '-'}</dd>
    </>
  )
}
