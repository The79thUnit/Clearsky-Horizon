import { useEffect, useState } from 'react'
import type { EventList, EventRecord } from '../types'
import { fetchEvents } from '../api'
import { useTick } from '../hooks/useLiveTick'

function formatLongDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function metaLine(ev: EventRecord): string {
  const parts: string[] = []
  if (ev.serotype_code) parts.push(ev.serotype_code)
  if (ev.country_iso2) parts.push(ev.country_iso2)
  if (ev.source_code) parts.push(ev.source_code)
  return parts.join(' / ')
}

export default function EventTimeline() {
  const [data, setData] = useState<EventList | null>(null)
  const [error, setError] = useState<string | null>(null)
  const tick = useTick()

  useEffect(() => {
    fetchEvents(40)
      .then(setData)
      .catch((e: unknown) => setError(String(e)))
  }, [tick.ts])

  if (error) return <div className="event-timeline-error">events error: {error}</div>

  return (
    <section className="event-timeline-section">
      <div className="event-timeline-head">
        <h3>Chronology</h3>
        <span className="event-timeline-meta">
          {data ? `${data.total} / 30 days` : 'loading'}
        </span>
      </div>

      {data && data.items.length === 0 && (
        <div className="event-timeline-empty">
          No significant events in the last 30 days.
        </div>
      )}

      {data && data.items.length > 0 && (
        <ol className="event-timeline">
          {data.items.map((ev) => (
            <li key={ev.id} className={`event-row severity-${ev.severity}`}>
              <div className="event-date">
                <time dateTime={ev.occurred_at}>{formatLongDate(ev.occurred_at)}</time>
              </div>
              <div className="event-body">
                <h4 className="event-title">{ev.title}</h4>
                {ev.summary && <p className="event-summary">{ev.summary}</p>}
                <div className="event-meta">
                  <span className="event-meta-line">{metaLine(ev)}</span>
                  {ev.source_url && (
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="event-source-link"
                    >
                      source
                    </a>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
