import { useEffect, useState } from 'react'
import type { CaseList as CaseListType, CaseRecord } from '../types'
import { fetchCases } from '../api'

function confidenceColor(conf: number): string {
  if (conf >= 0.85) return '#00e87a'
  if (conf >= 0.65) return '#2d7ff9'
  if (conf >= 0.45) return '#f59e0b'
  return '#ef4444'
}

function CaseCard({ c }: { c: CaseRecord }) {
  return (
    <article className="case-card">
      <header className="case-badges">
        <span className="badge badge-nato">{c.nato_reliability}{c.nato_credibility}</span>
        <span className="badge badge-source">{c.source_code}</span>
        {c.serotype_code && <span className="badge badge-serotype">{c.serotype_code}</span>}
        {c.country_iso2 && <span className="badge badge-country">{c.country_iso2}</span>}
        {c.region && <span className="badge badge-region">{c.region}</span>}
      </header>
      <h3>{c.title}</h3>
      {c.summary && (
        <p className="summary">
          {c.summary.slice(0, 280)}
          {c.summary.length > 280 ? '...' : ''}
        </p>
      )}
      <div className="case-meta">
        <div className="confidence">
          <span className="confidence-label">Pipeline</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{
                width: `${c.pipeline_confidence * 100}%`,
                background: confidenceColor(c.pipeline_confidence),
              }}
            />
          </div>
          <span className="confidence-value">{(c.pipeline_confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="confidence">
          {(() => {
            const isAuto = c.analyst_id === 'HORIZON-AUTO-SCORER/1.0'
            const isHuman = c.analyst_confidence !== null && !isAuto
            return (
              <>
                <span className="confidence-label" title={isAuto ? 'Machine pre-qualification (NATO Admiralty band). Pending human review.' : isHuman ? 'Human analyst reviewed' : 'Awaiting analyst review'}>
                  {isHuman ? 'Analyst' : isAuto ? 'Pre-qual' : 'Analyst'}
                </span>
                <div className="confidence-bar">
                  {c.analyst_confidence !== null && (
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${c.analyst_confidence * 100}%`,
                        background: isHuman ? '#00e87a' : '#f59e0b',
                      }}
                    />
                  )}
                </div>
                <span className="confidence-value" style={{ color: isHuman ? '#00e87a' : isAuto ? '#f59e0b' : undefined }}>
                  {isHuman
                    ? `${(c.analyst_confidence! * 100).toFixed(0)}%`
                    : isAuto
                    ? `${(c.analyst_confidence! * 100).toFixed(0)}% auto`
                    : 'pending'}
                </span>
              </>
            )
          })()}
        </div>
      </div>
      <footer className="case-footer">
        <a className="src-link" href={c.raw_url} target="_blank" rel="noopener noreferrer">
          source
        </a>
        <pre className="src-citation">{c.src_citation}</pre>
      </footer>
    </article>
  )
}

export default function CaseList() {
  const [data, setData] = useState<CaseListType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCases()
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
  }, [])

  if (error) {
    return (
      <div className="alert">
        <strong>Error:</strong> {error}
        <p>Check that the API is reachable at the configured base URL.</p>
      </div>
    )
  }
  if (!data) return <div className="loading">Loading cases...</div>
  if (data.items.length === 0) {
    return (
      <div className="empty">
        <h2>No cases ingested yet.</h2>
        <p>The worker polls ProMED every 15 minutes. Records will appear here once they arrive.</p>
        <p>
          Force an immediate fetch from a shell:
          <br />
          <code>docker compose exec worker celery -A horizon_worker.celery_app call horizon_worker.tasks.ingest.fetch_source --args='["promed-rss"]'</code>
        </p>
      </div>
    )
  }

  return (
    <section className="case-list">
      <div className="counts">
        <div className="counter">
          <span className="count-value">{data.total}</span>
          <span className="count-label">Records ingested</span>
        </div>
      </div>
      <div className="case-grid">
        {data.items.map((c) => (
          <CaseCard key={c.id} c={c} />
        ))}
      </div>
    </section>
  )
}
