import { useEffect, useState } from 'react'
import type { SourceList } from '../types'
import { fetchSources } from '../api'

const TIER_LABELS: Record<number, string> = {
  1: 'Official authority',
  2: 'Aggregator',
  3: 'News + social',
  4: 'Academic',
  5: 'Sequence record',
  6: 'Ecological',
  7: 'Derivative',
}

function relativeAge(iso: string | null): string {
  if (!iso) return 'never'
  const ms = Date.now() - new Date(iso).getTime()
  const min = Math.round(ms / 60_000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min}m ago`
  const hr = Math.round(min / 60)
  if (hr < 48) return `${hr}h ago`
  return `${Math.round(hr / 24)}d ago`
}

export default function SourceQualityTable() {
  const [data, setData] = useState<SourceList | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSources()
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
  }, [])

  if (error) return <div className="alert">Error: {error}</div>
  if (!data) return <div className="loading">Loading sources...</div>

  const enabledCount = data.items.filter((s) => s.enabled).length

  return (
    <section className="sources">
      <p className="lead">
        {data.items.length} {data.items.length === 1 ? 'source' : 'sources'} registered
        across 7 tiers, {enabledCount} currently enabled. Each row shows
        last-fetch result, HTTP status, response latency and total reports ingested.
        Source URLs and tiers are open and auditable.
      </p>
      <table className="sources-table">
        <thead>
          <tr>
            <th>Tier</th>
            <th>Code</th>
            <th>Name</th>
            <th>NATO</th>
            <th>Status</th>
            <th>Last fetch</th>
            <th>HTTP</th>
            <th>Latency</th>
            <th>Total ingested</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((s) => (
            <tr key={s.id} className={s.enabled ? 'row-enabled' : 'row-disabled'}>
              <td>
                <span className="tier-badge" title={TIER_LABELS[s.tier]}>
                  T{s.tier}
                </span>
              </td>
              <td className="code">{s.code}</td>
              <td>{s.name}</td>
              <td>
                <span className="nato-badge">
                  {s.nato_reliability}
                  {s.nato_credibility}
                </span>
              </td>
              <td>
                <span className={s.enabled ? 'enabled-dot' : 'disabled-dot'}>
                  {s.enabled ? 'live' : 'gated'}
                </span>
              </td>
              <td>{relativeAge(s.last_fetched_at)}</td>
              <td>{s.last_http_status ?? '-'}</td>
              <td>{s.last_latency_ms !== null ? `${s.last_latency_ms}ms` : '-'}</td>
              <td className="number">{s.total_items_ingested}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
