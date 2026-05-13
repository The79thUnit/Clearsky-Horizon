import { useState } from 'react'
import { API_BASE } from '../api'

interface ExportItem {
  label: string
  filename: string
  path: string
  description: string
}

const EXPORTS: ExportItem[] = [
  { label: 'Cases',    filename: 'horizon-cases.json',    path: '/api/v1/cases?limit=500',      description: 'All ingested case reports with NATO score, pipeline confidence, and ICD 206 SRC.' },
  { label: 'Sources',  filename: 'horizon-sources.json',  path: '/api/v1/sources',              description: 'Source registry with tier, NATO defaults, current freshness, and total ingestion count.' },
  { label: 'Clusters', filename: 'horizon-clusters.json', path: '/api/v1/clusters',             description: 'Auto-detected outbreak clusters: country, serotype, case count, fatalities, date range.' },
  { label: 'Events',   filename: 'horizon-events.json',   path: '/api/v1/meta/events?limit=200', description: 'Chronological event feed (cases, fatalities, statements, medevacs, milestones).' },
  { label: 'Stats',    filename: 'horizon-stats.json',    path: '/api/v1/meta/stats',           description: 'Aggregate counters + top serotypes + top countries.' },
]

async function downloadJSON(filename: string, path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, { headers: { accept: 'application/json' } })
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  const data = await res.json()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function ExportPanel() {
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  const handleExport = async (item: ExportItem) => {
    setError(null)
    setDownloading(item.filename)
    try {
      await downloadJSON(item.filename, item.path)
    } catch (e: unknown) {
      setError(`${item.label}: ${String(e)}`)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <section className="export-panel">
      <h3>Data export</h3>
      <p className="export-blurb">
        All HORIZON data is freely available under <strong>CC BY 4.0</strong>. Attribute as:
        <em> HORIZON, 79th Unit Limited (2026), accessed [date].</em> No registration
        required. No tracking. Files are stable JSON conformant to the OpenAPI 3.x schema
        at <code>/api/openapi.json</code>.
      </p>
      <div className="export-buttons">
        {EXPORTS.map((item) => (
          <button
            key={item.filename}
            type="button"
            onClick={() => handleExport(item)}
            disabled={downloading === item.filename}
            title={item.description}
          >
            {downloading === item.filename ? '...' : `${item.label} JSON`}
          </button>
        ))}
      </div>
      {error && <div className="export-error">Download failed: {error}</div>}
    </section>
  )
}
