/**
 * OntologyGraph — branching visualisation of an incident's transmission tree.
 *
 * Columns: exposure → persons → vessel/voyage → ports
 *
 * Layout rules:
 *   - Orthogonal (right-angle) edges so they don't cut through node boxes.
 *   - Persons ordered by case_status priority (probable index first, then
 *     confirmed, etc.) rather than alphabetically by label.
 *   - Ports ordered chronologically along the voyage track.
 *   - Edge labels drawn in white-pill backgrounds so they read against
 *     node + connector overlap.
 *   - Redundant edge labels suppressed (an arrow from a Voyage to a Port
 *     in the port-call relationship reads obviously).
 */

import { useEffect, useState } from 'react'
import type { EntityRecord, IncidentOntology, RelationshipRecord } from '../types'
import { fetchIncidentOntology } from '../api'

interface Props {
  incidentCode: string
}

interface NodePos {
  ent: EntityRecord
  x: number
  y: number
  w: number
  h: number
}

const NODE_W = 220
const NODE_H = 84
const COL_GAP = 60
const ROW_GAP = 28

// Column index by entity type.
const COL: Record<string, number> = {
  excursion: 0,
  person: 1,
  vessel: 2,
  voyage: 2,
  port: 3,
  port_call: 3,
}

// Person order priority (lower = higher in the column).
const PERSON_ORDER = (p: Record<string, string | number | null>): number => {
  const status = String(p.case_status ?? '')
  // Patient zero / index probable goes on top, then confirmed, then others
  if (status === 'probable') return 0
  if (status === 'confirmed') return 1
  return 2
}

// Port chronological order along the voyage.
const PORT_ORDER: Record<string, number> = {
  Ushuaia: 0,
  'Saint Helena': 1,
  'Cape Town': 2,
  'Tenerife (Santa Cruz)': 3,
}

// Edge label suppression: keep ONLY the rel_types that add real intelligence.
// Everything else (attended, in_voyage, vessel, port-call kinds) is obvious
// from the connection's geometry and direction.
//
// Currently only `transmitted_to` is kept, because human-to-human transmission
// is the one non-obvious fact a doctrine reader needs to register fast.
const KEEP_LABEL: Set<string> = new Set([
  'transmitted_to',
])

export default function OntologyGraph({ incidentCode }: Props) {
  const [ontology, setOntology] = useState<IncidentOntology | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchIncidentOntology(incidentCode)
      .then(setOntology)
      .catch((e: unknown) => setError(String(e)))
  }, [incidentCode])

  if (error) return <div className="ontology-graph-error">graph error: {error}</div>
  if (!ontology) return <div className="ontology-graph-loading">loading transmission graph…</div>

  const layout = layoutNodes(ontology.entities)
  const maxX = Math.max(...layout.map((n) => n.x + n.w), 0)
  const maxY = Math.max(...layout.map((n) => n.y + n.h), 0)
  const width = maxX + 60
  const height = maxY + 50

  return (
    <section className="ontology-graph">
      <header className="ontology-graph-head">
        <h3>Transmission graph &middot; how the cluster branched</h3>
        <span className="ontology-graph-meta">
          {ontology.entities.length} entities &middot; {ontology.relationships.length} edges
        </span>
      </header>

      <div className="ontology-graph-legend">
        <span className="og-legend-key og-key-excursion">exposure</span>
        <span className="og-legend-key og-key-person">person</span>
        <span className="og-legend-key og-key-vessel">vessel</span>
        <span className="og-legend-key og-key-voyage">voyage</span>
        <span className="og-legend-key og-key-port">port</span>
        <span className="og-legend-key og-key-transmission">P2P transmission</span>
      </div>

      <div className="ontology-graph-svg-wrap">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="Transmission ontology graph"
        >
          <defs>
            <marker
              id="arrow-edge"
              viewBox="0 0 10 10"
              refX="9" refY="5"
              markerWidth="7" markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#111114" />
            </marker>
            <marker
              id="arrow-transmission"
              viewBox="0 0 10 10"
              refX="9" refY="5"
              markerWidth="8" markerHeight="8"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#cf1f1f" />
            </marker>
          </defs>

          {/* edges first (so nodes paint over them) */}
          {ontology.relationships.map((r, i) => (
            <EdgePath
              key={r.id}
              rel={r}
              layout={layout}
              edgeIndex={i}
              allRels={ontology.relationships}
            />
          ))}

          {/* nodes */}
          {layout.map((n) => (
            <NodeBox key={n.ent.id} node={n} />
          ))}
        </svg>
      </div>

      <p className="ontology-graph-caption">
        Grey arrows = directional relationships (read in the direction of the
        arrow: e.g. Person → Excursion = attended, Person → Voyage = travelled
        on, Voyage → Port = port called). The red arrow marks the documented
        person-to-person transmission — Andes virus is the only orthohantavirus
        with confirmed P2P spread, which is how a rodent-borne disease moved
        through the cruise after the initial environmental exposure on land.
      </p>
    </section>
  )
}

function layoutNodes(entities: EntityRecord[]): NodePos[] {
  // Group by column, then order within column.
  const byCol: Record<number, EntityRecord[]> = { 0: [], 1: [], 2: [], 3: [] }
  for (const e of entities) {
    const c = COL[e.entity_type] ?? 3
    byCol[c].push(e)
  }

  // Order column 1 (persons) by case_status priority.
  byCol[1].sort((a, b) => {
    const ap = a.properties as Record<string, string | number | null>
    const bp = b.properties as Record<string, string | number | null>
    return PERSON_ORDER(ap) - PERSON_ORDER(bp)
  })

  // Order column 2: vessel first, then voyage.
  byCol[2].sort((a, b) => {
    const av = a.entity_type === 'vessel' ? 0 : 1
    const bv = b.entity_type === 'vessel' ? 0 : 1
    return av - bv
  })

  // Order column 3 (ports) chronologically along the voyage.
  byCol[3].sort((a, b) => {
    return (PORT_ORDER[a.public_label ?? ''] ?? 99) - (PORT_ORDER[b.public_label ?? ''] ?? 99)
  })

  const out: NodePos[] = []
  for (const cs of Object.keys(byCol)) {
    const c = Number(cs)
    const entries = byCol[c]
    entries.forEach((ent, i) => {
      const x = 30 + c * (NODE_W + COL_GAP)
      const y = 30 + i * (NODE_H + ROW_GAP)
      out.push({ ent, x, y, w: NODE_W, h: NODE_H })
    })
  }
  return out
}

function NodeBox({ node }: { node: NodePos }) {
  const t = node.ent.entity_type
  const label = node.ent.public_label ?? `(${t})`
  const props = node.ent.properties as Record<string, string | number | null>
  let line2 = ''
  let line3 = ''
  if (t === 'person') {
    line2 = `${props.sex ?? '?'} / ${props.age ?? '?'}`
    line3 = String(props.case_status ?? '')
  } else if (t === 'vessel') {
    line2 = `IMO ${props.imo ?? '-'}`
    line3 = `MMSI ${props.mmsi ?? '-'}`
  } else if (t === 'port') {
    line2 = String(props.country_iso2 ?? '')
  } else if (t === 'voyage') {
    line2 = `${props.departed_at ?? '-'} → ${props.arrived_at ?? '-'}`
  } else if (t === 'excursion') {
    line2 = String(props.location_name ?? '')
  }

  return (
    <g transform={`translate(${node.x}, ${node.y})`} className={`og-node-group og-${t}`}>
      <rect width={node.w} height={node.h} className={`og-node og-node-${t}`} rx={0} ry={0} />
      <text x={14} y={20} className="og-node-type">
        {t.toUpperCase()}
      </text>
      <text x={14} y={42} className="og-node-label">
        {truncate(label, 28)}
      </text>
      {line2 && (
        <text x={14} y={60} className="og-node-sub">
          {truncate(line2, 32)}
        </text>
      )}
      {line3 && (
        <text x={14} y={75} className="og-node-sub">
          {line3}
        </text>
      )}
    </g>
  )
}

/**
 * Orthogonal edge with smart routing:
 *   - Same column → short vertical line INSIDE the column, between rows.
 *     Label centred horizontally on the line, inside the row gap.
 *   - Different columns → L-route. Parallel edges sharing a source or
 *     destination node fan out to distinct entry/exit anchors so they
 *     don't overlap.
 *   - Labels suppressed unless rel_type is in KEEP_LABEL set.
 */
function EdgePath({
  rel,
  layout,
  edgeIndex,
  allRels,
}: {
  rel: RelationshipRecord
  layout: NodePos[]
  edgeIndex: number
  allRels: RelationshipRecord[]
}) {
  const src = layout.find((n) => n.ent.id === rel.src_id)
  const dst = layout.find((n) => n.ent.id === rel.dst_id)
  if (!src || !dst) return null

  const isTransmission = rel.rel_type === 'transmitted_to'
  const labelText = KEEP_LABEL.has(rel.rel_type)
    ? rel.rel_type.replace(/_/g, ' ').toLowerCase()
    : ''

  const sameCol = src.x === dst.x

  // Compute anchor offsets so parallel edges fan out.
  //   For source: count how many edges leave from this src; assign each a
  //   distinct fraction down the right (or left) face of the node.
  //   Same for destination's left (or right) face.
  const srcEdges = allRels.filter((r) => r.src_id === rel.src_id)
  const dstEdges = allRels.filter((r) => r.dst_id === rel.dst_id)
  const srcRank = srcEdges.findIndex((r) => r.id === rel.id)
  const dstRank = dstEdges.findIndex((r) => r.id === rel.id)
  const srcFrac = srcEdges.length === 1 ? 0.5 : (srcRank + 1) / (srcEdges.length + 1)
  const dstFrac = dstEdges.length === 1 ? 0.5 : (dstRank + 1) / (dstEdges.length + 1)

  let path: string
  let labelX = 0
  let labelY = 0
  let labelAnchor: 'start' | 'middle' | 'end' = 'middle'

  if (sameCol) {
    // Vertical inside-column route (between two stacked rows).
    // Start at bottom of src, end at top of dst (or reversed).
    const goingDown = src.y < dst.y
    const x = src.x + src.w / 2
    const yStart = goingDown ? src.y + src.h : src.y
    const yEnd = goingDown ? dst.y : dst.y + dst.h
    path = `M ${x} ${yStart} L ${x} ${yEnd}`
    labelX = x
    labelY = (yStart + yEnd) / 2 + 3 // small drop so the pill is centred
    labelAnchor = 'middle'
  } else {
    // Direction (LTR or RTL) — handle both.
    const leftToRight = src.x < dst.x
    const x1 = leftToRight ? src.x + src.w : src.x
    const x2 = leftToRight ? dst.x : dst.x + dst.w
    const y1 = src.y + srcFrac * src.h
    const y2 = dst.y + dstFrac * dst.h
    const midX = (x1 + x2) / 2
    path = `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`
    labelX = midX
    // Place label on the vertical segment, vertically centred between y1/y2.
    labelY = (y1 + y2) / 2 + 3
    labelAnchor = 'middle'
  }

  const edgeClass = `og-edge${isTransmission ? ' og-edge-transmission' : ''}`

  return (
    <g className={edgeClass}>
      <path
        d={path}
        fill="none"
        markerEnd={`url(#${isTransmission ? 'arrow-transmission' : 'arrow-edge'})`}
      />
      {labelText && (
        <EdgeLabel
          x={labelX}
          y={labelY}
          text={labelText}
          accent={isTransmission}
          anchor={labelAnchor}
        />
      )}
    </g>
  )
  void edgeIndex
}

/** Pill-backed text label for an edge. Reads cleanly against any background. */
function EdgeLabel({
  x,
  y,
  text,
  accent,
  anchor,
}: {
  x: number
  y: number
  text: string
  accent: boolean
  anchor: 'start' | 'middle' | 'end'
}) {
  // Crude width estimate based on character count (monospace 9px ~5.5px/char)
  const padX = 6
  const padY = 3
  const charW = 5.4
  const w = text.length * charW + padX * 2
  const h = 13
  let rectX = x - w / 2
  if (anchor === 'start') rectX = x
  else if (anchor === 'end') rectX = x - w

  return (
    <g className={`og-edge-label-group${accent ? ' og-edge-label-accent' : ''}`}>
      <rect
        x={rectX}
        y={y - h + padY}
        width={w}
        height={h}
        className="og-edge-label-bg"
      />
      <text
        x={x}
        y={y}
        textAnchor={anchor}
        className="og-edge-label-text"
      >
        {text}
      </text>
    </g>
  )
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s
}
