import { useEffect, useMemo, useState } from 'react'
import type { CaseRecord } from '../types'
import { fetchCases } from '../api'
import { useTick } from '../hooks/useLiveTick'
import { getCountryFlag } from '../data/countries'

const WINDOW_DAYS = 90

interface LaneDot {
  case: CaseRecord
  ts: number
}

interface Lane {
  serotype: string
  dots: LaneDot[]
}

function formatDate(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10)
}

function shortDate(ms: number): string {
  return new Date(ms).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
  })
}

export default function Timeline() {
  const [cases, setCases] = useState<CaseRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const [hovered, setHovered] = useState<{ case: CaseRecord; x: number; y: number } | null>(null)
  const tick = useTick()

  useEffect(() => {
    fetchCases(200)
      .then((r) => setCases(r.items))
      .catch((e: unknown) => setError(String(e)))
  }, [tick.ts])

  const { lanes, range } = useMemo(() => {
    const now = Date.now()
    const cutoff = now - WINDOW_DAYS * 86_400_000
    const inWindow: LaneDot[] = []
    for (const c of cases) {
      const raw = c.reported_date ?? c.ingested_at
      if (!raw) continue
      const ts = new Date(raw).getTime()
      if (!Number.isFinite(ts) || ts < cutoff || ts > now + 86_400_000) continue
      inWindow.push({ case: c, ts })
    }

    // Group by serotype, lane order = first-occurrence
    const order: string[] = []
    const map = new Map<string, LaneDot[]>()
    for (const d of inWindow.sort((a, b) => a.ts - b.ts)) {
      const sero = d.case.serotype_code ?? d.case.serotype_text ?? 'UNKNOWN'
      if (!map.has(sero)) {
        order.push(sero)
        map.set(sero, [])
      }
      map.get(sero)!.push(d)
    }
    const lanes: Lane[] = order.map((s) => ({ serotype: s, dots: map.get(s)! }))
    return { lanes, range: { start: cutoff, end: now } }
  }, [cases])

  if (error) return <div className="timeline-error">timeline error: {error}</div>

  const totalCases = lanes.reduce((s, l) => s + l.dots.length, 0)

  // Layout constants
  const W = 1400
  const LANE_LABEL_W = 64
  const LANE_COUNT_W = 60
  const PAD_X = 16
  const ROW_HEIGHT = 28
  const TOP_AXIS = 22
  const BOTTOM_AXIS = 26
  const trackLeft = PAD_X + LANE_LABEL_W + 8
  const trackRight = W - PAD_X - LANE_COUNT_W - 8
  const trackWidth = trackRight - trackLeft
  const trackHeight = Math.max(ROW_HEIGHT, lanes.length * ROW_HEIGHT)
  const H = TOP_AXIS + trackHeight + BOTTOM_AXIS

  const xAt = (ts: number) =>
    trackLeft + (trackWidth * (ts - range.start)) / (range.end - range.start)

  // Tick positions every ~14 days
  const ticks: number[] = []
  for (let t = range.start; t <= range.end; t += 14 * 86_400_000) ticks.push(t)
  const todayX = xAt(range.end)

  if (lanes.length === 0) {
    return (
      <section className="timeline-section">
        <div className="timeline-header">
          <h3>Last {WINDOW_DAYS} days</h3>
          <span className="timeline-meta">0 records / no serotypes</span>
        </div>
        <div className="timeline-empty">No records ingested in the last {WINDOW_DAYS} days.</div>
      </section>
    )
  }

  return (
    <section className="timeline-section">
      <div className="timeline-header">
        <h3>Last {WINDOW_DAYS} days</h3>
        <span className="timeline-meta">
          {totalCases} records / {lanes.length} serotype{lanes.length === 1 ? '' : 's'}
        </span>
      </div>
      <div className="timeline-svg-wrap">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" className="timeline-svg">
          {/* Top tick marks + labels */}
          {ticks.map((t, i) => (
            <g key={`tick-${i}`}>
              <line
                x1={xAt(t)}
                x2={xAt(t)}
                y1={TOP_AXIS - 6}
                y2={TOP_AXIS + trackHeight}
                stroke="rgba(17,17,20,0.06)"
                strokeWidth={1}
              />
              <text
                x={xAt(t)}
                y={TOP_AXIS - 10}
                fill="rgba(17,17,20,0.55)"
                fontSize={10}
                fontFamily="JetBrains Mono, ui-monospace, monospace"
                textAnchor="middle"
              >
                {shortDate(t)}
              </text>
            </g>
          ))}

          {/* Lanes */}
          {lanes.map((lane, laneIdx) => {
            const yCenter = TOP_AXIS + laneIdx * ROW_HEIGHT + ROW_HEIGHT / 2
            return (
              <g key={`lane-${lane.serotype}`}>
                {/* Lane label (left) */}
                <text
                  x={PAD_X}
                  y={yCenter + 4}
                  fill="#111114"
                  fontSize={11}
                  fontWeight={600}
                  fontFamily="JetBrains Mono, monospace"
                >
                  {lane.serotype}
                </text>

                {/* Lane track */}
                <line
                  x1={trackLeft}
                  x2={trackRight}
                  y1={yCenter}
                  y2={yCenter}
                  stroke="rgba(17,17,20,0.15)"
                  strokeWidth={1}
                />

                {/* Lane count (right) */}
                <text
                  x={W - PAD_X}
                  y={yCenter + 4}
                  fill="#111114"
                  fontSize={11}
                  fontWeight={600}
                  fontFamily="JetBrains Mono, monospace"
                  textAnchor="end"
                  style={{ fontVariantNumeric: 'tabular-nums' }}
                >
                  {lane.dots.length}
                </text>

                {/* Dots: small filled squares */}
                {lane.dots.map((d, i) => {
                  const x = xAt(d.ts)
                  return (
                    <rect
                      key={`${d.case.id}-${i}`}
                      x={x - 4.5}
                      y={yCenter - 4.5}
                      width={9}
                      height={9}
                      fill="#cf1f1f"
                      stroke="#f1efe9"
                      strokeWidth={1.5}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHovered({ case: d.case, x, y: yCenter })}
                      onMouseLeave={() => setHovered(null)}
                    />
                  )
                })}
              </g>
            )
          })}

          {/* Today marker */}
          <line
            x1={todayX}
            x2={todayX}
            y1={TOP_AXIS - 4}
            y2={TOP_AXIS + trackHeight + 4}
            stroke="#111114"
            strokeWidth={1.5}
          />
          <text
            x={todayX}
            y={TOP_AXIS + trackHeight + 18}
            fill="#111114"
            fontSize={9}
            fontWeight={600}
            fontFamily="JetBrains Mono, monospace"
            letterSpacing="0.08em"
            textAnchor="middle"
          >
            TODAY
          </text>

          {/* Bottom rule */}
          <line
            x1={trackLeft}
            x2={trackRight}
            y1={TOP_AXIS + trackHeight + 1}
            y2={TOP_AXIS + trackHeight + 1}
            stroke="#111114"
            strokeWidth={1}
          />
        </svg>

        {hovered && (() => {
          // Flip the tooltip below the marker when it sits in the top
          // third of the timeline, so it can't be clipped by the section
          // edge. Same horizontal-clamping logic prevents it from spilling
          // off the left/right sides.
          const placeBelow = hovered.y < H * 0.45
          const xPct = (hovered.x / W) * 100
          const leftClamped = Math.max(15, Math.min(85, xPct))
          return (
          <div
            className={`timeline-tooltip${placeBelow ? ' below' : ' above'}`}
            style={{
              left: `${leftClamped}%`,
              top: `${(hovered.y / H) * 100}%`,
            }}
          >
            <div className="tooltip-line">
              {getCountryFlag(hovered.case.country_iso2)}{' '}
              <strong>{hovered.case.title.slice(0, 100)}</strong>
            </div>
            <div className="tooltip-sub">
              {hovered.case.serotype_code ?? 'unknown'} ·{' '}
              {hovered.case.reported_date ?? formatDate(new Date(hovered.case.ingested_at).getTime())} ·
              confidence {(hovered.case.pipeline_confidence * 100).toFixed(0)}%
            </div>
          </div>
          )
        })()}
      </div>
    </section>
  )
}
