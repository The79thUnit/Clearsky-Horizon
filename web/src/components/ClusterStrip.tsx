import { useEffect, useState } from 'react'
import type { ClusterList } from '../types'
import { fetchClusters } from '../api'
import { useTick } from '../hooks/useLiveTick'

export default function ClusterStrip() {
  const [data, setData] = useState<ClusterList | null>(null)
  const [error, setError] = useState<string | null>(null)
  const tick = useTick()

  useEffect(() => {
    fetchClusters()
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
  }, [tick.ts])

  if (error) return <div className="cluster-strip-error">clusters error: {error}</div>
  if (!data || data.items.length === 0) {
    return (
      <section className="cluster-strip">
        <h3 className="strip-heading">Active clusters</h3>
        <div className="event-timeline-empty">No clusters detected.</div>
      </section>
    )
  }

  return (
    <section className="cluster-strip">
      <header className="cluster-strip-head">
        <h3 className="strip-heading">Reporting signals &middot; {data.total}</h3>
        <p className="cluster-strip-blurb">
          Auto-grouped by country, serotype, and time-window. Each count is
          <strong> source records ingested</strong> (news articles, ProMED, CDC HAN,
          PubMed, etc.) <em>not</em> confirmed patient cases. One outbreak picked up
          by N sources reads as N records.
        </p>
      </header>
      <div className="cluster-grid">
        {data.items.map((c) => {
          const meta: string[] = []
          if (c.serotype_code) meta.push(c.serotype_code)
          if (c.country_iso2) meta.push(c.country_iso2)
          if (c.region) meta.push(c.region)

          // Rewrite "X hantavirus cluster YYYY-MM-DD" → "X hantavirus signal YYYY-MM-DD"
          // to make it clear this is a reporting signal, not a confirmed outbreak.
          const friendlyName = c.name.replace(/ cluster /, ' signal ')

          return (
            <article key={c.id} className="cluster-card">
              <h4 className="cluster-name">{friendlyName}</h4>
              <div className="cluster-stats">
                <div className="cluster-stat">
                  <span className="stat-value">{c.case_count}</span>
                  <span className="stat-label">records</span>
                </div>
                {c.death_count > 0 && (
                  <div className="cluster-stat critical">
                    <span className="stat-value">{c.death_count}</span>
                    <span className="stat-label">deaths reported</span>
                  </div>
                )}
              </div>
              <div className="cluster-meta">
                <span className="cluster-meta-line">{meta.join(' / ')}</span>
                {(c.started_at || c.ended_at) && (
                  <span className="cluster-dates">
                    {c.started_at}
                    {c.ended_at && c.ended_at !== c.started_at ? ` – ${c.ended_at}` : ''}
                  </span>
                )}
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
