import { useEffect, useState } from 'react'
import type { StatsResponse } from '../types'
import { fetchStats } from '../api'
import { useTick } from '../hooks/useLiveTick'

export default function StatsHero() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const tick = useTick()

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((e: unknown) => setError(String(e)))
  }, [tick.ts])

  if (error) return <div className="hero-error">stats error: {error}</div>

  const totalCases =
    (stats?.total_confirmed_cases_authoritative ?? 0) +
    (stats?.total_suspected_cases_authoritative ?? 0)

  return (
    <section className="stats-hero">
      <div className="hero-counters">
        <Counter
          label="Total cases"
          sublabel="confirmed + probable"
          value={stats ? totalCases : undefined}
          accent
        />
        <Counter
          label="Confirmed"
          sublabel="PCR / lab positive"
          value={stats?.total_confirmed_cases_authoritative}
        />
        <Counter
          label="Probable"
          sublabel="awaiting lab"
          value={stats?.total_suspected_cases_authoritative}
        />
        <Counter
          label="Deaths"
          sublabel="authoritative"
          value={stats?.total_deaths_authoritative}
          critical
        />
        <Counter
          label="Active incidents"
          sublabel="open outbreaks"
          value={stats?.total_active_incidents}
        />
        <Counter
          label="Reports ingested"
          sublabel="source articles"
          value={stats?.total_reports_ingested}
        />
        <Counter
          label="Sources live"
          sublabel="connectors active"
          value={stats?.total_sources_enabled}
        />
      </div>
      <p className="hero-disclaimer">
        Confirmed / suspected / deaths reflect the latest authoritative count from the
        highest-NATO-rated source per active incident (typically WHO Disease Outbreak
        News). Reports ingested counts source articles, not patients. One outbreak
        reported by ten sources is one incident, not ten cases.
      </p>
    </section>
  )
}

function Counter({
  label,
  sublabel,
  value,
  accent,
  critical,
}: {
  label: string
  sublabel?: string
  value: number | undefined
  accent?: boolean
  critical?: boolean
}) {
  const cls = accent ? ' accent' : critical ? ' critical' : ''
  return (
    <div className={`hero-counter${cls}`}>
      <span className="hero-value">{value ?? '-'}</span>
      <span className="hero-label">{label}</span>
      {sublabel && <span className="hero-sublabel">{sublabel}</span>}
    </div>
  )
}
