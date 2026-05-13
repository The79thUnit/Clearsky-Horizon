import { useEffect, useState } from 'react'
import type { IncidentRecord } from '../types'
import { fetchIncidents } from '../api'
import { useTick } from '../hooks/useLiveTick'
import { COUNTRIES } from '../data/countries'
import OntologyGraph from './OntologyGraph'
import PatientZeroPanel from './PatientZeroPanel'

export default function IncidentBanner() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const tick = useTick()

  useEffect(() => {
    fetchIncidents()
      .then((r) => setIncidents(r.items))
      .catch((e: unknown) => setError(String(e)))
  }, [tick.ts])

  if (error || incidents.length === 0) return null

  return (
    <section className="incident-banner">
      <div className="incident-banner-header">
        <h2>Active outbreak incidents</h2>
        <span className="incident-count-pill">{incidents.length}</span>
      </div>
      <div className="incident-card-row">
        {incidents.map((inc) => (
          <IncidentCard key={inc.id} inc={inc} />
        ))}
      </div>
    </section>
  )
}

function IncidentCard({ inc }: { inc: IncidentRecord }) {
  // Collapsed by default. Click anywhere on the header row to expand.
  const [expanded, setExpanded] = useState(false)
  const countriesWithCases = inc.countries.filter(
    (c) => c.confirmed_count + c.suspected_count + c.deaths > 0,
  )

  return (
    <article className={`incident-card${expanded ? ' expanded' : ' collapsed'}`}>
      <button
        type="button"
        className="incident-card-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((x) => !x)}
        title={expanded ? 'Click to collapse' : 'Click to open the full dossier'}
      >
        <span className={`incident-status incident-status-${inc.status}`}>{inc.status}</span>
        {inc.serotype_code && <span className="incident-serotype">{inc.serotype_code}</span>}

        <h3 className="incident-toggle-name">{inc.name}</h3>

        {inc.started_at && (
          <span className="incident-toggle-date">since {inc.started_at}</span>
        )}

        <span className="incident-toggle-spacer" />

        <span className="incident-toggle-stats-row">
          <span className="incident-toggle-stat">
            <span className="incident-toggle-stat-num">{inc.confirmed_cases + inc.suspected_cases}</span>
            <span className="incident-toggle-stat-lbl">cases</span>
          </span>
          <span className="incident-toggle-stat">
            <span className="incident-toggle-stat-num">{inc.confirmed_cases}</span>
            <span className="incident-toggle-stat-lbl">conf</span>
          </span>
          <span className="incident-toggle-stat">
            <span className="incident-toggle-stat-num">{inc.suspected_cases}</span>
            <span className="incident-toggle-stat-lbl">prob</span>
          </span>
          <span className="incident-toggle-stat critical">
            <span className="incident-toggle-stat-num">{inc.deaths}</span>
            <span className="incident-toggle-stat-lbl">deaths</span>
          </span>
        </span>

        <span
          className={`incident-toggle-chevron${expanded ? ' open' : ' pulse'}`}
          aria-hidden="true"
        >
          {expanded ? '×' : '+'}
        </span>
      </button>

      {expanded && (
        <div className="incident-card-body">
          {inc.primary_vessel_name && (
            <p className="incident-vessel">
              <span className="incident-key">Vessel</span>{' '}
              <span className="iv-frag iv-frag-first">{inc.primary_vessel_name}</span>
              {inc.primary_vessel_imo && (
                <span className="iv-frag">IMO {inc.primary_vessel_imo}</span>
              )}
              {inc.primary_vessel_mmsi && (
                <span className="iv-frag">MMSI {inc.primary_vessel_mmsi}</span>
              )}
              {inc.primary_vessel_flag && (
                <span className="iv-frag">flag {inc.primary_vessel_flag}</span>
              )}
            </p>
          )}

          {inc.primary_location_name && (
            <p className="incident-origin">
              <span className="incident-key">Origin</span>{' '}
              <span className="iv-frag iv-frag-first">{inc.primary_location_name}</span>
            </p>
          )}

          {inc.summary && <p className="incident-summary">{inc.summary}</p>}

          <div className="incident-numbers">
            <Stat label="Confirmed" value={inc.confirmed_cases} accent />
            <Stat label="Suspected" value={inc.suspected_cases} />
            <Stat label="Deaths" value={inc.deaths} critical />
            <Stat label="Recovered" value={inc.recovered} />
          </div>

          {inc.authority_source_code && inc.authority_reported_at && (
            <p className="incident-attribution">
              Authority: <strong>{inc.authority_source_code}</strong> &middot; reported{' '}
              {new Date(inc.authority_reported_at).toISOString().slice(0, 10)} &middot;{' '}
              {inc.corroborating_sources} corroborating source
              {inc.corroborating_sources === 1 ? '' : 's'}
            </p>
          )}

          {countriesWithCases.length > 0 && (
            <table className="incident-countries">
              <thead>
                <tr>
                  <th>Country</th>
                  <th>Confirmed</th>
                  <th>Suspected</th>
                  <th>Deaths</th>
                  <th>First reported</th>
                </tr>
              </thead>
              <tbody>
                {countriesWithCases.map((c) => {
                  const meta = COUNTRIES[c.country_iso2]
                  return (
                    <tr key={c.country_iso2}>
                      <td>{meta ? `${meta.flag} ${meta.name}` : c.country_iso2}</td>
                      <td>{c.confirmed_count}</td>
                      <td>{c.suspected_count}</td>
                      <td>{c.deaths}</td>
                      <td>{c.first_reported_at ?? '-'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}

          <PatientZeroPanel incidentCode={inc.code} />

          <OntologyGraph incidentCode={inc.code} />
        </div>
      )}
    </article>
  )
}

function Stat({
  label,
  value,
  accent,
  critical,
}: {
  label: string
  value: number
  accent?: boolean
  critical?: boolean
}) {
  const cls = accent ? ' accent' : critical ? ' critical' : ''
  return (
    <div className={`incident-stat${cls}`}>
      <span className="incident-stat-value">{value}</span>
      <span className="incident-stat-label">{label}</span>
    </div>
  )
}
