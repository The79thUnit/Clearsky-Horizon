import { useCallback, useEffect, useRef, useState } from 'react'
import maplibregl, { Map as MapLibreMap, Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { IncidentRecord, IncidentOntology, VesselTrackPoint } from '../types'
import { fetchIncidents, fetchIncidentOntology } from '../api'
import { COUNTRIES } from '../data/countries'
import { useTick } from '../hooks/useLiveTick'
import {
  ANDV_PARAMS,
  CITY_POOL_TIERED,
  SIM_FLIGHTS,
  SimCase,
  runFullSim,
  routeArc,
  flightArcProgress,
  caseStatus,
  STATUS_COLOR,
} from '../data/spreadModel'

const SIM_DURATION_MS = 27_000 // 90 simulated days play out over 27 seconds

const MAP_STYLE = {
  version: 8 as const,
  sources: {
    carto: {
      type: 'raster' as const,
      tiles: [
        'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
        'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
        'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    },
  },
  layers: [{ id: 'carto', type: 'raster' as const, source: 'carto' }],
}

function escapeHTML(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    const m: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }
    return m[c] ?? c
  })
}

function countryPinSize(total: number, deaths: number): number {
  return Math.max(22, Math.min(56, 18 + total * 4 + deaths * 4))
}

function popupOffsetForSize(size: number): Record<string, [number, number]> {
  const half = size / 2 + 2
  return {
    center: [0, 0],
    top: [0, half],
    bottom: [0, -half],
    left: [half, 0],
    right: [-half, 0],
    'top-left': [half * 0.6, half],
    'top-right': [-half * 0.6, half],
    'bottom-left': [half * 0.6, -half],
    'bottom-right': [-half * 0.6, -half],
  }
}

export default function WorldMap() {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const loadedRef = useRef(false)
  const [incidents, setIncidents] = useState<IncidentRecord[]>([])
  const [ontology, setOntology] = useState<IncidentOntology | null>(null)
  const [error, setError] = useState<string | null>(null)
  const tick = useTick()

  // Spread simulation state
  const [simActive, setSimActive] = useState(false)
  const [simDay, setSimDay] = useState(0)
  const [simFinished, setSimFinished] = useState(false)
  const [simPaused, setSimPaused] = useState(false)
  const simRafRef = useRef<number | null>(null)
  // Pre-computed stochastic sim output + pre-computed arc coords
  const simCasesRef = useRef<SimCase[]>([])
  // Pre-built arc GeoJSON features (geometry only; opacity updated per-frame)
  const simArcBaseRef = useRef<GeoJSON.Feature<GeoJSON.LineString, Record<string, unknown>>[]>([])

  const startSim = useCallback(() => {
    if (simRafRef.current !== null) cancelAnimationFrame(simRafRef.current)
    // Pre-compute full passenger-population sim (fast, ~1ms)
    simCasesRef.current = runFullSim()
    // Pre-compute arc geometry (route-aware, waypoint-forced for southern Pacific)
    simArcBaseRef.current = SIM_FLIGHTS.map((f) => ({
      type: 'Feature' as const,
      geometry: {
        type: 'LineString' as const,
        coordinates: routeArc([f.origin_lon, f.origin_lat], [f.dest_lon, f.dest_lat]),
      },
      properties: {
        id: f.id,
        kind: f.kind,
        pax_count: f.pax_count,
        flight_day: f.flight_day,
        dest_city: f.dest_city,
        note: f.note,
      },
    }))
    setSimActive(true)
    setSimFinished(false)
    setSimDay(0)
    const startTime = performance.now()
    const tickSim = (now: number) => {
      const elapsed = now - startTime
      const t = Math.min(1, elapsed / SIM_DURATION_MS)
      setSimDay(t * ANDV_PARAMS.projection_days)
      if (t < 1) {
        simRafRef.current = requestAnimationFrame(tickSim)
      } else {
        simRafRef.current = null
        setSimFinished(true)
      }
    }
    simRafRef.current = requestAnimationFrame(tickSim)
  }, [])

  const stopSim = useCallback(() => {
    if (simRafRef.current !== null) cancelAnimationFrame(simRafRef.current)
    simRafRef.current = null
    setSimActive(false)
    setSimFinished(false)
    setSimPaused(false)
    setSimDay(0)
    simCasesRef.current = []
    simArcBaseRef.current = []
    // Tear down all sim layers + sources so nothing lingers on the map
    const map = mapRef.current
    if (map) {
      for (const id of [
        'spread-anchor-pin', 'spread-dot', 'spread-dot-glow',
        'sim-flights', 'sim-flights-glow',
        'sim-cases', 'sim-cases-glow',
      ]) {
        if (map.getLayer(id)) map.removeLayer(id)
      }
      for (const sid of [
        'spread-anchors-src', 'spread-dots-src',
        'sim-flights-src',
        'sim-cases-src',
      ]) {
        if (map.getSource(sid)) map.removeSource(sid)
      }
    }
  }, [])

  // Scrub to a specific day (pauses playback)
  const handleScrub = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (simRafRef.current !== null) {
      cancelAnimationFrame(simRafRef.current)
      simRafRef.current = null
    }
    setSimPaused(true)
    setSimFinished(false)
    setSimDay(Number(e.target.value))
  }, [])

  // Resume playback from current scrubbed position
  const resumeSim = useCallback(() => {
    if (!simActive || simRafRef.current !== null) return
    setSimPaused(false)
    setSimFinished(false)
    const fromDay = simDay
    const totalDays = ANDV_PARAMS.projection_days
    const remaining = totalDays - fromDay
    if (remaining <= 0) { setSimFinished(true); return }
    const remainingMs = (remaining / totalDays) * SIM_DURATION_MS
    const startTime = performance.now()
    const tickSim = (now: number) => {
      const elapsed = now - startTime
      const t = Math.min(1, elapsed / remainingMs)
      setSimDay(fromDay + t * remaining)
      if (t < 1) {
        simRafRef.current = requestAnimationFrame(tickSim)
      } else {
        simRafRef.current = null
        setSimFinished(true)
      }
    }
    simRafRef.current = requestAnimationFrame(tickSim)
  }, [simActive, simDay])

  // Cleanup RAF on unmount
  useEffect(() => {
    return () => {
      if (simRafRef.current !== null) cancelAnimationFrame(simRafRef.current)
    }
  }, [])

  // Init map once
  useEffect(() => {
    if (!containerRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [-30, 0],
      zoom: 1.6,
      attributionControl: false,
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false, visualizePitch: false }), 'top-right')
    map.addControl(new maplibregl.AttributionControl({ compact: true }))
    map.on('load', () => { loadedRef.current = true })
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      loadedRef.current = false
    }
  }, [])

  // Fetch incidents + ontology of the primary incident on every tick.
  // Both state updates happen in the same async continuation so React 18
  // automatic batching collapses them into a single re-render, preventing
  // the marker effect from firing twice (once per setIncidents, once per
  // setOntology) which previously left stale stacked markers on the map.
  useEffect(() => {
    let stale = false
    const run = async () => {
      try {
        const r = await fetchIncidents()
        if (stale) return
        const primary = r.items.find((i) => i.status === 'active') ?? r.items[0]
        const ont = primary ? await fetchIncidentOntology(primary.code) : null
        if (stale) return
        setIncidents(r.items)
        setOntology(ont)
      } catch (e: unknown) {
        if (!stale) setError(String(e))
      }
    }
    run()
    return () => { stale = true }
  }, [tick.ts])

  // Render: vessel track + country pins + special markers (patient zero / death sites)
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const markers: Marker[] = []

    const apply = () => {
      // Clear prior vector layers
      for (const id of [
        'vessel-track', 'vessel-track-glow',
        'vessel-track-projected', 'vessel-track-projected-glow',
        'flight-routes', 'flight-routes-glow',
      ]) {
        if (map.getLayer(id)) map.removeLayer(id)
        if (map.getSource(id)) map.removeSource(id)
      }

      // ---- Flight branches ----------------------------------------------
      // Draw each flight_route entity as a great-circle curve so the
      // repatriation paths are visibly distinct from the sea route.
      if (ontology) {
        const flights = ontology.entities.filter((e) => e.entity_type === 'flight_route')
        if (flights.length > 0) {
          const flightFeatures = flights
            .map((f) => {
              const p = f.properties as Record<string, number | string>
              const oLng = Number(p.origin_lng), oLat = Number(p.origin_lat)
              const dLng = Number(p.dest_lng), dLat = Number(p.dest_lat)
              if (![oLng, oLat, dLng, dLat].every(Number.isFinite)) return null
              return {
                type: 'Feature' as const,
                geometry: {
                  type: 'LineString' as const,
                  coordinates: routeArc([oLng, oLat], [dLng, dLat]),
                },
                properties: {
                  label: f.public_label,
                  confidence: typeof p.confidence === 'number' ? p.confidence : 0.7,
                  purpose: String(p.purpose ?? 'repatriation'),
                },
              }
            })
            .filter((x): x is NonNullable<typeof x> => x !== null)

          if (flightFeatures.length > 0) {
            map.addSource('flight-routes', {
              type: 'geojson',
              data: { type: 'FeatureCollection', features: flightFeatures },
            })
            // Glow underlay (wider, softer)
            map.addLayer({
              id: 'flight-routes-glow',
              type: 'line',
              source: 'flight-routes',
              paint: {
                'line-color': '#cf1f1f',
                'line-width': 3,
                'line-opacity': 0.18,
              },
            })
            // Crisp dashed line on top, opacity scaled by confidence
            map.addLayer({
              id: 'flight-routes',
              type: 'line',
              source: 'flight-routes',
              paint: {
                'line-color': '#cf1f1f',
                'line-width': 1,
                'line-dasharray': [4, 4],
                'line-opacity': [
                  'interpolate', ['linear'], ['get', 'confidence'],
                  0.5, 0.35,
                  1.0, 0.85,
                ],
              },
            })
          }
        }
      }

      // 1) Vessel track polyline from ontology.vessel_track.
      //    Split actual (past) from projected (future) so the projected
      //    segment renders dashed.
      if (ontology && ontology.vessel_track.length >= 2) {
        const nowMs = Date.now()
        const past: VesselTrackPoint[] = []
        const future: VesselTrackPoint[] = []
        for (const p of ontology.vessel_track) {
          if (new Date(p.ts).getTime() > nowMs) future.push(p)
          else past.push(p)
        }
        // Bridge: the last past point continues into the projected segment.
        if (past.length > 0 && future.length > 0) {
          future.unshift(past[past.length - 1])
        }
        const coords = past.map((p: VesselTrackPoint) => [p.lng, p.lat])
        map.addSource('vessel-track', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: { type: 'LineString', coordinates: coords },
          },
        })
        // Wider lighter glow underneath
        map.addLayer({
          id: 'vessel-track-glow',
          type: 'line',
          source: 'vessel-track',
          paint: { 'line-color': '#cf1f1f', 'line-width': 4, 'line-opacity': 0.18 },
        })
        // Crisp narrow line on top
        map.addLayer({
          id: 'vessel-track',
          type: 'line',
          source: 'vessel-track',
          paint: { 'line-color': '#111114', 'line-width': 1.3, 'line-opacity': 0.95 },
        })

        // Projected segment (future track points) rendered dashed so it's
        // visibly distinct from the confirmed route.
        if (future.length >= 2) {
          const futureCoords = future.map((p: VesselTrackPoint) => [p.lng, p.lat])
          map.addSource('vessel-track-projected', {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: { type: 'LineString', coordinates: futureCoords },
            },
          })
          map.addLayer({
            id: 'vessel-track-projected-glow',
            type: 'line',
            source: 'vessel-track-projected',
            paint: { 'line-color': '#cf1f1f', 'line-width': 4, 'line-opacity': 0.10 },
          })
          map.addLayer({
            id: 'vessel-track-projected',
            type: 'line',
            source: 'vessel-track-projected',
            paint: {
              'line-color': '#111114',
              'line-width': 1.3,
              'line-opacity': 0.55,
              'line-dasharray': [3, 3],
            },
          })
        }
      }

      // 2) Case-location pins — anchored to the SPECIFIC CITY where each
      //    country's cases are clinically managed / where the index death
      //    occurred. This is more accurate than dropping the count badge
      //    on a country centroid (e.g. middle of the USA for one east-coast
      //    case). Confidence per anchor is stated in the popup so viewers
      //    know whether the city is the actual reported location or a
      //    documented proxy.
      //
      //    Source for each anchor:
      //      NL → Amsterdam       HIGH   patient zero + spouse, NL repat hub
      //      FR → Paris           MED    repatriation hub; exact case city
      //                                  not disclosed by WHO/ECDC
      //      US → Boston (proxy)  LOW    US case city not disclosed; Boston
      //                                  used as east-coast hospital proxy
      //      ZA → Cape Town       HIGH   Groote Schuur Hospital = medevac
      //                                  destination + recorded death site
      const CASE_ANCHOR: Record<
        string,
        { lat: number; lng: number; city: string; confidence: number; provenance: string }
      > = {
        NL: {
          lat: 52.3676, lng: 4.9041, city: 'Amsterdam',
          confidence: 1.0,
          provenance: 'Patient zero + spouse Dutch nationals — AMC/LUMC isolation catchment (WHO DON 600)',
        },
        FR: {
          lat: 48.8566, lng: 2.3522, city: 'Paris',
          confidence: 0.7,
          provenance: 'French passenger repatriated — Bichat-Claude Bernard ID centre; exact city undisclosed',
        },
        US: {
          lat: 42.3601, lng: -71.0589, city: 'Boston (proxy)',
          confidence: 0.5,
          provenance: 'US passenger — exact city not in WHO/ECDC release; east-coast tertiary-care proxy',
        },
        ZA: {
          lat: -33.9396, lng: 18.4644, city: 'Cape Town (Groote Schuur Hospital)',
          confidence: 1.0,
          provenance: 'Medevac destination from St Helena; site of victim 2 death (PCR-confirmed)',
        },
        ES: {
          lat: 28.4682, lng: -16.2546, city: 'Santa Cruz de Tenerife',
          confidence: 0.8,
          provenance: 'Auto-detected via 3-source corroboration (Al Jazeera, AOL, others); ES case likely discovered in Tenerife post-disembark',
        },
      }

      for (const inc of incidents) {
        for (const c of inc.countries) {
          const total = c.confirmed_count + c.suspected_count + c.deaths
          if (total === 0) continue
          // Prefer the actual case-anchor city; fall back to country
          // centroid only if no anchor is configured for the country.
          const anchor = CASE_ANCHOR[c.country_iso2]
          const fallback = COUNTRIES[c.country_iso2]
          if (!anchor && !fallback) continue
          const pos = anchor
            ? { lat: anchor.lat, lng: anchor.lng }
            : { lat: fallback.lat, lng: fallback.lng }
          const countryName = fallback ? fallback.name : c.country_iso2

          const size = countryPinSize(total, c.deaths)
          const el = document.createElement('div')
          el.className = `map-pin${c.deaths > 0 ? ' has-death' : c.confirmed_count > 0 ? ' has-case' : ' has-suspected'}`
          el.style.width = `${size}px`
          el.style.height = `${size}px`
          el.textContent = String(total)

          const confPct = anchor ? `${Math.round(anchor.confidence * 100)}%` : '—'
          const cityLine = anchor
            ? `<div class="map-popup-berth">${escapeHTML(anchor.city)} &middot; <span class="map-popup-conf">${confPct} confidence</span></div>`
            : `<div class="map-popup-berth">Country centroid (no city-level data)</div>`
          const provenance = anchor
            ? `<div class="map-popup-source-detail">${escapeHTML(anchor.provenance)}</div>`
            : ''

          const popup = new maplibregl.Popup({
            offset: popupOffsetForSize(size) as never,
            closeButton: false,
            className: 'horizon-map-popup',
          }).setHTML(`
            <div class="map-popup">
              <div class="map-popup-title">${escapeHTML(countryName)}</div>
              <div class="map-popup-sub">${escapeHTML(inc.name)}</div>
              ${cityLine}
              <div class="map-popup-coords">${pos.lat.toFixed(4)}, ${pos.lng.toFixed(4)}</div>
              <ul class="map-popup-list">
                <li>${c.confirmed_count} confirmed</li>
                <li>${c.suspected_count} suspected</li>
                <li>${c.deaths} ${c.deaths === 1 ? 'death' : 'deaths'}</li>
              </ul>
              ${provenance}
            </div>
          `)
          markers.push(
            new maplibregl.Marker({ element: el })
              .setLngLat([pos.lng, pos.lat])
              .setPopup(popup)
              .addTo(map),
          )
        }
      }

      // 3) Patient-zero marker at Ushuaia (suspected exposure)
      if (ontology) {
        const excursion = ontology.entities.find((e) => e.entity_type === 'excursion')
        const ports = ontology.entities.filter((e) => e.entity_type === 'port')
        const ushuaia = ports.find((p) => (p.public_label ?? '').toLowerCase().startsWith('ushuaia'))
        if (excursion && ushuaia) {
          const props = ushuaia.properties as Record<string, number>
          const exc = excursion.properties as Record<string, string>
          const el = document.createElement('div')
          el.className = 'trace-pin trace-patient-zero'
          el.setAttribute('data-label', 'PATIENT ZERO')
          const popup = new maplibregl.Popup({
            offset: popupOffsetForSize(14) as never,
            closeButton: false,
            className: 'horizon-map-popup',
          }).setHTML(`
            <div class="map-popup">
              <div class="map-popup-title">Suspected exposure</div>
              <div class="map-popup-sub">${escapeHTML(excursion.public_label ?? '')}</div>
              <p class="map-popup-narrative">${escapeHTML(exc.notes ?? '')}</p>
            </div>
          `)
          if (typeof props.lat === 'number' && typeof props.lng === 'number') {
            markers.push(
              new maplibregl.Marker({ element: el })
                .setLngLat([props.lng, props.lat])
                .setPopup(popup)
                .addTo(map),
            )
          }
        }

        // Port-call dots — each popup shows vessel + arrival/departure data
        // pulled from the relationships table. Edges of types
        // departed_from / port_called / arrived_at / medevac_destination
        // carry { at: 'YYYY-MM-DD', note?: string } properties; we look those
        // up per port to compose a rich popup.
        const vessel = ontology.entities.find((e) => e.entity_type === 'vessel')
        const vProps = (vessel?.properties ?? {}) as Record<string, string | number>

        // Relationship-type → human label for the popup
        const REL_LABEL: Record<string, string> = {
          departed_from: 'Departed',
          arrived_at: 'Arrived',
          port_called: 'Port called',
          medevac_destination: 'Medevac destination',
          planned_arrival: 'Planned arrival',
        }

        // For each port, find every relationship connecting vessel → port.
        const relsForPort = (portId: string) =>
          ontology.relationships.filter(
            (r) => r.dst_id === portId && REL_LABEL[r.rel_type],
          )

        for (const port of ports) {
          const p = port.properties as Record<string, string | number | boolean>
          if (typeof p.lat !== 'number' || typeof p.lng !== 'number') continue
          if ((port.public_label ?? '').toLowerCase().startsWith('ushuaia')) continue
          // Skip projected port — it has its own dedicated marker block above
          if (p.projected === true) continue

          const el = document.createElement('div')
          el.className = 'trace-waypoint'

          const rels = relsForPort(port.id)
          const eventLines = rels
            .map((r) => {
              const rp = (r.properties ?? {}) as Record<string, string | number | boolean>
              const at = rp.at ? escapeHTML(String(rp.at)) : '-'
              // Build a compact metadata blob: dates + counts + note.
              const bits: string[] = []
              if (typeof rp.disembarked === 'number' && rp.disembarked > 0) {
                bits.push(`<strong>${rp.disembarked}</strong> disembarked`)
              }
              if (typeof rp.evacuated === 'number' && rp.evacuated > 0) {
                bits.push(`<strong>${rp.evacuated}</strong> evacuated`)
              }
              if (typeof rp.evac_pcr_positive === 'number' && rp.evac_pcr_positive > 0) {
                bits.push(
                  `<strong>${rp.evac_pcr_positive}</strong> PCR-confirmed post-evac`,
                )
              }
              if (rp.flown_home === true) bits.push('flown home')
              if (rp.includes_body === true) bits.push('inc. body of victim 1')
              if (rp.departed_at) bits.push(`departed ${escapeHTML(String(rp.departed_at))}`)
              const metaLine = bits.length
                ? `<div class="map-popup-evac">${bits.join(' &middot; ')}</div>`
                : ''
              const note = rp.note
                ? `<div class="map-popup-note">${escapeHTML(String(rp.note))}</div>`
                : ''
              const confPct =
                typeof r.confidence === 'number'
                  ? ` <span class="map-popup-conf">${Math.round(r.confidence * 100)}%</span>`
                  : ''
              return (
                `<li>` +
                `<strong>${REL_LABEL[r.rel_type]}</strong> ${at}${confPct}` +
                `${metaLine}${note}` +
                `</li>`
              )
            })
            .join('')

          const popup = new maplibregl.Popup({
            offset: popupOffsetForSize(8) as never,
            closeButton: false,
            className: 'horizon-map-popup',
          }).setHTML(`
            <div class="map-popup map-popup-port">
              <div class="map-popup-title">${escapeHTML(port.public_label ?? '')}</div>
              <div class="map-popup-sub">
                ${escapeHTML(String(p.country_iso2 ?? ''))}
                ${p.unlocode ? ' &middot; ' + escapeHTML(String(p.unlocode)) : ''}
              </div>
              <div class="map-popup-coords">
                ${(+p.lat).toFixed(4)}, ${(+p.lng).toFixed(4)}
              </div>
              ${eventLines ? `<ul class="map-popup-events">${eventLines}</ul>` : ''}
              ${
                vessel
                  ? `<div class="map-popup-vessel-line">
                       Vessel ${escapeHTML(String(vessel.public_label ?? ''))}
                       &middot; IMO ${escapeHTML(String(vProps.imo ?? '-'))}
                       &middot; MMSI ${escapeHTML(String(vProps.mmsi ?? '-'))}
                     </div>`
                  : ''
              }
            </div>
          `)
          markers.push(
            new maplibregl.Marker({ element: el })
              .setLngLat([p.lng, p.lat])
              .setPopup(popup)
              .addTo(map),
          )
        }

        // ============================================================
        // CANVAS-RENDERED MARKERS (death, projected, current position)
        // ============================================================
        // These render as MapLibre paint layers inside the map canvas
        // instead of HTML overlays. They are physically welded to the
        // map geometry and cannot drift relative to basemap features at
        // any zoom level. Popups are bound via click handlers, not
        // marker.setPopup().

        // Tear down any previous incarnation of these layers/sources
        for (const id of [
          'death-events-glow', 'death-events',
          'projected-port-outline', 'projected-port-fill',
          'current-position-pulse', 'current-position-core',
        ]) {
          if (map.getLayer(id)) map.removeLayer(id)
        }
        for (const sid of ['death-events-src', 'projected-port-src', 'current-position-src']) {
          if (map.getSource(sid)) map.removeSource(sid)
        }

        // ---- DEATH EVENTS layer -------------------------------------
        const deathEvents = ontology.entities.filter(
          (e) => e.entity_type === 'death_event',
        )
        if (deathEvents.length > 0) {
          const features = deathEvents
            .map((d) => {
              const dp = d.properties as Record<string, string | number | boolean | null>
              if (typeof dp.lat !== 'number' || typeof dp.lng !== 'number') return null
              return {
                type: 'Feature' as const,
                geometry: { type: 'Point' as const, coordinates: [Number(dp.lng), Number(dp.lat)] },
                properties: {
                  label: d.public_label ?? 'Death event',
                  occurred_at: String(dp.occurred_at ?? '-'),
                  location_type: String(dp.location_type ?? '-'),
                  subject: String(dp.subject ?? '-'),
                  pcr_confirmed: dp.pcr_confirmed,
                  confidence: typeof dp.confidence === 'number' ? dp.confidence : 1.0,
                  source: String(dp.source ?? '-'),
                  popup_kind: 'death',
                },
              }
            })
            .filter((x): x is NonNullable<typeof x> => x !== null)

          map.addSource('death-events-src', { type: 'geojson', data: { type: 'FeatureCollection', features } })
          // Subtle red ring beneath (visual emphasis)
          map.addLayer({
            id: 'death-events-glow',
            type: 'circle',
            source: 'death-events-src',
            paint: {
              'circle-color': '#cf1f1f',
              'circle-opacity': 0.15,
              'circle-radius': 12,
            },
          })
          // Solid black square… well, circle (MapLibre paint layer doesn't do squares natively)
          // with red stroke. Distinctive vs other markers.
          map.addLayer({
            id: 'death-events',
            type: 'circle',
            source: 'death-events-src',
            paint: {
              'circle-color': '#111114',
              'circle-stroke-color': '#cf1f1f',
              'circle-stroke-width': 2,
              'circle-radius': 6,
              'circle-pitch-alignment': 'map',
            },
          })
        }

        // ---- PROJECTED port (Rotterdam) layer -----------------------
        const projectedPorts = ports.filter((p) => {
          const pp = p.properties as Record<string, unknown>
          return pp.projected === true
        })
        if (projectedPorts.length > 0) {
          const features = projectedPorts
            .map((port) => {
              const pp = port.properties as Record<string, number | string | boolean>
              if (typeof pp.lat !== 'number' || typeof pp.lng !== 'number') return null
              return {
                type: 'Feature' as const,
                geometry: { type: 'Point' as const, coordinates: [Number(pp.lng), Number(pp.lat)] },
                properties: {
                  label: port.public_label ?? '',
                  country_iso2: String(pp.country_iso2 ?? ''),
                  unlocode: String(pp.unlocode ?? ''),
                  popup_kind: 'projected',
                },
              }
            })
            .filter((x): x is NonNullable<typeof x> => x !== null)

          map.addSource('projected-port-src', { type: 'geojson', data: { type: 'FeatureCollection', features } })
          map.addLayer({
            id: 'projected-port-fill',
            type: 'circle',
            source: 'projected-port-src',
            paint: {
              'circle-color': '#f1efe9',
              'circle-radius': 8,
              'circle-stroke-color': '#111114',
              'circle-stroke-width': 2,
              'circle-pitch-alignment': 'map',
            },
          })
          // Dashed effect approximated with an outer thinner stroke
          map.addLayer({
            id: 'projected-port-outline',
            type: 'circle',
            source: 'projected-port-src',
            paint: {
              'circle-color': 'transparent',
              'circle-radius': 12,
              'circle-stroke-color': '#111114',
              'circle-stroke-width': 1,
              'circle-stroke-opacity': 0.45,
            },
          })
        }

        // ---- CURRENT POSITION layer ---------------------------------
        const nowMs = Date.now()
        const pastTrack = ontology.vessel_track.filter(
          (p) => new Date(p.ts).getTime() <= nowMs,
        )
        if (pastTrack.length > 0) {
          const latest: VesselTrackPoint = pastTrack[pastTrack.length - 1]
          const currentSource = String(latest.source ?? 'port_call')
          const currentTs = latest.ts

          // Find berthed port if within 0.5° of any port coordinate
          let berthedAt: string | null = null
          for (const port of ports) {
            const pp = port.properties as Record<string, number>
            if (
              typeof pp.lat === 'number' &&
              typeof pp.lng === 'number' &&
              Math.abs(pp.lat - latest.lat) < 0.5 &&
              Math.abs(pp.lng - latest.lng) < 0.5
            ) {
              berthedAt = port.public_label ?? null
              break
            }
          }

          map.addSource('current-position-src', {
            type: 'geojson',
            data: {
              type: 'Feature',
              geometry: { type: 'Point', coordinates: [latest.lng, latest.lat] },
              properties: {
                source: currentSource,
                ts: currentTs,
                berthed_at: berthedAt ?? '',
                popup_kind: 'current',
              },
            },
          })
          // Animated pulse ring (outer)
          map.addLayer({
            id: 'current-position-pulse',
            type: 'circle',
            source: 'current-position-src',
            paint: {
              'circle-color': '#cf1f1f',
              'circle-radius': 14,
              'circle-opacity': 0.35,
              'circle-stroke-color': '#cf1f1f',
              'circle-stroke-width': 1.5,
              'circle-stroke-opacity': 0.7,
            },
          })
          // Solid core dot — the actual anchor
          map.addLayer({
            id: 'current-position-core',
            type: 'circle',
            source: 'current-position-src',
            paint: {
              'circle-color': '#cf1f1f',
              'circle-radius': 5,
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 2,
              'circle-pitch-alignment': 'map',
            },
          })

          // Pulse animation: drive the outer radius/opacity via JS rAF
          // (cleaner than a CSS animation that can't live inside a canvas layer)
          let raf = 0
          const start = performance.now()
          const animatePulse = (t: number) => {
            const elapsed = (t - start) / 1000
            const period = 1.8
            const phase = (elapsed % period) / period   // 0..1
            const radius = 14 + phase * 24             // 14 → 38
            const opacity = (1 - phase) * 0.35
            if (map.getLayer('current-position-pulse')) {
              map.setPaintProperty('current-position-pulse', 'circle-radius', radius)
              map.setPaintProperty('current-position-pulse', 'circle-opacity', opacity)
            }
            raf = requestAnimationFrame(animatePulse)
          }
          raf = requestAnimationFrame(animatePulse)
          // Store cancel ref on the map so cleanup can stop it
          ;(map as unknown as { __cppRaf?: number }).__cppRaf = raf
        }

        // ---- Click handlers: bind popups to the canvas circles -------
        const popupSingleton = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: false,
          className: 'horizon-map-popup',
        })

        const onClickDeath = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
          const f = e.features && e.features[0]
          if (!f) return
          const p = f.properties as Record<string, string | number | boolean | null>
          const conf = typeof p.confidence === 'number' ? p.confidence : Number(p.confidence ?? 1)
          const pcr = p.pcr_confirmed
          popupSingleton
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="map-popup map-popup-death">
                <div class="map-popup-eyebrow">Fatality</div>
                <div class="map-popup-title">${escapeHTML(String(p.label ?? 'Death event'))}</div>
                <div class="map-popup-berth">${escapeHTML(String(p.occurred_at ?? '-'))} &middot; ${escapeHTML(String(p.location_type ?? '-'))}</div>
                <div class="map-popup-coords">${e.lngLat.lat.toFixed(4)}, ${e.lngLat.lng.toFixed(4)}</div>
                <div class="map-popup-vessel-line">Subject: ${escapeHTML(String(p.subject ?? '-'))}</div>
                <div class="map-popup-vessel-line">PCR confirmed: ${pcr === true || pcr === 'true' ? 'yes' : pcr === false || pcr === 'false' ? 'no' : 'unknown'}</div>
                <div class="map-popup-source">confidence ${(conf * 100).toFixed(0)}% &middot; source: ${escapeHTML(String(p.source ?? '-'))}</div>
              </div>
            `)
            .addTo(map)
        }

        const onClickProjected = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
          const f = e.features && e.features[0]
          if (!f) return
          const p = f.properties as Record<string, string>
          popupSingleton
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="map-popup map-popup-projected">
                <div class="map-popup-eyebrow">Projected endpoint</div>
                <div class="map-popup-title">${escapeHTML(String(p.label ?? ''))}</div>
                <div class="map-popup-sub">${escapeHTML(String(p.country_iso2 ?? ''))}${p.unlocode ? ' &middot; ' + escapeHTML(String(p.unlocode)) : ''}</div>
                <div class="map-popup-vessel-line">Estimated arrival: <strong>2026-05-17</strong></div>
                <div class="map-popup-vessel-line">Action: remaining crew &amp; medical staff disembark; ship to be decontaminated</div>
                <div class="map-popup-source">source: CNN 2026-05-08 (estimated)</div>
              </div>
            `)
            .addTo(map)
        }

        const onClickCurrent = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
          const f = e.features && e.features[0]
          if (!f) return
          const p = f.properties as Record<string, string>
          const SOURCE_LABEL: Record<string, string> = {
            aisstream:      '🟢 LIVE — aisstream.io',
            marinetraffic:  '🟢 LIVE — Kpler / MarineTraffic',
            myshiptracking: '🟢 LIVE — myshiptracking.com',
            manual:         '🟡 EST — dead-reckoning from schedule',
            port_call:      '⚪ STALE — last scheduled port call',
          }
          const src = String(p.source ?? 'port_call')
          const label = SOURCE_LABEL[src] ?? `source: ${escapeHTML(src)}`
          const tsDate = new Date(p.ts || Date.now())
          const tsHuman = tsDate.toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
          const ageMs = Date.now() - tsDate.getTime()
          const ageHours = Math.floor(ageMs / 3_600_000)
          popupSingleton
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="map-popup map-popup-current">
                <div class="map-popup-eyebrow">${src === 'manual' ? 'Estimated position' : src === 'port_call' ? 'Last scheduled position' : 'Live position'}</div>
                <div class="map-popup-title">${vessel ? escapeHTML(String(vessel.public_label ?? '')) : 'Vessel'}</div>
                ${p.berthed_at ? `<div class="map-popup-berth">At ${escapeHTML(String(p.berthed_at))}</div>` : `<div class="map-popup-berth">At sea</div>`}
                <div class="map-popup-coords">${e.lngLat.lat.toFixed(4)}, ${e.lngLat.lng.toFixed(4)}</div>
                <div class="map-popup-ts"><strong>${tsHuman}</strong> <span class="map-popup-age">${ageHours === 0 ? 'just now' : `${ageHours}h ago`}</span></div>
                ${vessel ? `<dl class="map-popup-vessel">
                  <dt>IMO</dt><dd>${escapeHTML(String(vProps.imo ?? '-'))}</dd>
                  <dt>MMSI</dt><dd>${escapeHTML(String(vProps.mmsi ?? '-'))}</dd>
                  <dt>Flag</dt><dd>${escapeHTML(String(vProps.flag_iso2 ?? '-'))}</dd>
                  <dt>Type</dt><dd>${escapeHTML(String(vProps.type ?? '-'))}</dd>
                  <dt>Length</dt><dd>${escapeHTML(String(vProps.length_m ?? '-'))} m</dd>
                  <dt>Operator</dt><dd>${escapeHTML(String(vProps.operator ?? '-'))}</dd>
                </dl>` : ''}
                <div class="map-popup-source"><strong>${label}</strong></div>
              </div>
            `)
            .addTo(map)
        }

        for (const layerId of ['death-events', 'projected-port-fill', 'current-position-core']) {
          if (!map.getLayer(layerId)) continue
          map.on('click', layerId, layerId === 'death-events' ? onClickDeath : layerId === 'projected-port-fill' ? onClickProjected : onClickCurrent)
          map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer' })
          map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = '' })
        }
      }
    }

    // Guard against the effect running twice before the map loads (e.g. if
    // React fires the effect before the 'load' event and then again on the
    // next state update). Without this, both calls register map.once('load')
    // and both fire when the map loads, stacking duplicate markers.
    let cancelled = false
    const guardedApply = () => { if (!cancelled) apply() }
    if (loadedRef.current) guardedApply()
    else map.once('load', guardedApply)

    return () => {
      cancelled = true
      markers.forEach((m) => m.remove())
      // Cancel the current-position pulse animation rAF
      const m = mapRef.current as unknown as { __cppRaf?: number } | null
      if (m && typeof m.__cppRaf === 'number') {
        cancelAnimationFrame(m.__cppRaf)
        m.__cppRaf = undefined
      }
    }
  }, [incidents, ontology])

  // Spread-simulation render — v3 stochastic model.
  //
  // Layer inventory (all cleared by stopSim):
  //   sim-flights-src / sim-flights-glow / sim-flights
  //     Great-circle arcs from each origin port to each repatriation destination.
  //     Animated: arcs draw in as the sim day reaches their flight_day.
  //     Pre-Day-0 arcs (SH/Tristan dispersals) are fully visible from Day 0.
  //   sim-cases-src / sim-cases-glow / sim-cases
  //     One dot per SimCase. Colour by status: amber=incubating, red=symptomatic,
  //     dark-red=critical, green=recovered, gray=dead.
  //     Cases appear (opacity 0→1 over 2 days) at their day_symptoms.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const applySpread = () => {
      if (!simActive) return

      // ---- Flight arcs -----------------------------------------------
      // Update opacity per-feature based on arc progress at current simDay.
      const baseOpacity: Record<string, number> = {
        confirmed_case:      0.90,
        exposure_monitoring: 0.65,
        crew_repatriation:   0.35,
        early_disembark:     0.50,
      }
      const flightFeatures = simArcBaseRef.current.map((f) => {
        const fp = f.properties as { flight_day: number; kind: string }
        const progress = flightArcProgress(fp.flight_day, simDay)
        const targetOp = baseOpacity[fp.kind] ?? 0.5
        return {
          ...f,
          properties: { ...f.properties, opacity: progress * targetOp },
        }
      })
      const flightData: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: flightFeatures,
      }
      const flSrc = map.getSource('sim-flights-src') as maplibregl.GeoJSONSource | undefined
      if (flSrc) {
        flSrc.setData(flightData)
      } else {
        map.addSource('sim-flights-src', { type: 'geojson', data: flightData })
        // Soft wide glow
        map.addLayer({
          id: 'sim-flights-glow',
          type: 'line',
          source: 'sim-flights-src',
          paint: {
            'line-color': ['case',
              ['==', ['get', 'kind'], 'confirmed_case'],      '#ef4444',
              ['==', ['get', 'kind'], 'exposure_monitoring'], '#f59e0b',
              ['==', ['get', 'kind'], 'early_disembark'],     '#f97316',
              '#94a3b8',
            ],
            'line-width': 4,
            'line-opacity': ['*', ['get', 'opacity'], 0.30],
            'line-blur': 2,
          },
        })
        // Crisp line on top
        map.addLayer({
          id: 'sim-flights',
          type: 'line',
          source: 'sim-flights-src',
          paint: {
            'line-color': ['case',
              ['==', ['get', 'kind'], 'confirmed_case'],      '#ef4444',
              ['==', ['get', 'kind'], 'exposure_monitoring'], '#f59e0b',
              ['==', ['get', 'kind'], 'early_disembark'],     '#f97316',
              '#94a3b8',
            ],
            'line-width': 1.2,
            'line-dasharray': [5, 4],
            'line-opacity': ['get', 'opacity'],
          },
        })
      }

      // ---- Case dots -----------------------------------------------
      // Two visual populations:
      //   Amber (monitoring=false, infected=false): passengers under observation.
      //     Appear at day_exposed; fade out as 42-day window closes.
      //   Purple (infected=true): cases in the stochastic chain.
      //     Appear at day_symptoms; colour by status; pulse when active.
      const caseFeatures = simCasesRef.current
        .filter((c) => {
          // CRITICAL FIX: Validate coordinates are on land, not in ocean
          // Reject cases >2.5° from any known city (indicates jitter pushed into sea)
          if (CITY_POOL_TIERED) {
            const allCities = Object.values(CITY_POOL_TIERED).flat()
            const nearCity = allCities.some(city =>
              Math.abs(city.coords[1] - c.lat) < 2.5 && Math.abs(city.coords[0] - c.lon) < 2.5
            )
            if (!nearCity) return false // Filter out sea dots
          }

          if (!c.infected) {
            // Monitoring dot: show from landing day to end of monitoring + 3-day fade tail
            return c.day_exposed <= simDay && simDay < c.day_exposed + 45
          }
          // Infected case: start appearing 2 days before symptom onset
          return c.day_symptoms <= simDay + 2
        })
        .map((c) => {
          const status = caseStatus(c, simDay)
          const color = STATUS_COLOR[status]
          let opacity: number
          let radius: number
          let glow_radius: number
          let glow_opacity: number

          if (!c.infected) {
            // Monitoring dot: small amber, fade in at landing then out near 42d mark
            const fadeIn   = Math.max(0, Math.min(1, (simDay - c.day_exposed) / 2))
            const monEnd   = c.day_exposed + 42
            const fadeOut  = status === 'cleared' ? 0
              : simDay >= monEnd - 3 ? Math.max(0, (monEnd - simDay) / 3)
              : 1
            opacity      = fadeIn * fadeOut
            radius       = 2.5
            glow_radius  = 5
            glow_opacity = opacity * 0.12
          } else {
            // Infected case: purple spectrum, larger, subtle pulse when active
            const fadeIn  = Math.max(0, Math.min(1, (simDay - c.day_symptoms) / 2))
            const pulse   = (status === 'symptomatic' || status === 'critical')
              ? 1 + 0.15 * Math.sin(simDay * 0.8 + c.lon)
              : 1
            opacity      = fadeIn
            radius       = (status === 'dead' || status === 'recovered' ? 3.5 : 5) * pulse
            glow_radius  = (status === 'dead' || status === 'recovered' ? 7 : 12) * pulse
            glow_opacity = fadeIn * (status === 'incubating' ? 0.20 : 0.35)
          }

          return {
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [c.lon, c.lat] },
            properties: {
              id:          c.id,
              color,
              opacity,
              radius,
              glow_radius,
              glow_opacity,
              infected:    c.infected ? 1 : 0,
              note:        c.note,
            },
          }
        })
      const caseData: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: caseFeatures,
      }
      const csSrc = map.getSource('sim-cases-src') as maplibregl.GeoJSONSource | undefined
      if (csSrc) {
        csSrc.setData(caseData)
      } else {
        map.addSource('sim-cases-src', { type: 'geojson', data: caseData })
        // Glow halo
        map.addLayer({
          id: 'sim-cases-glow',
          type: 'circle',
          source: 'sim-cases-src',
          paint: {
            'circle-color': ['get', 'color'],
            'circle-radius': ['get', 'glow_radius'],
            'circle-opacity': ['get', 'glow_opacity'],
            'circle-blur': 0.7,
          },
        })
        // Crisp core dot
        map.addLayer({
          id: 'sim-cases',
          type: 'circle',
          source: 'sim-cases-src',
          paint: {
            'circle-color': ['get', 'color'],
            'circle-radius': ['get', 'radius'],
            'circle-opacity': ['get', 'opacity'],
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 0.8,
            'circle-stroke-opacity': ['*', ['get', 'opacity'], 0.6],
            'circle-pitch-alignment': 'map',
          },
        })
        // Click popup: every simulated dot must clearly label itself
        const simPopup = new maplibregl.Popup({
          closeButton: true,
          closeOnClick: false,
          className: 'horizon-map-popup',
        })
        map.on('click', 'sim-cases', (e) => {
          const f = e.features && e.features[0]
          if (!f) return
          const p = f.properties as Record<string, string | number>
          const isInfected = Number(p.infected) === 1
          simPopup
            .setLngLat(e.lngLat)
            .setHTML(isInfected ? `
              <div class="map-popup map-popup-sim">
                <div class="map-popup-sim-warning">⚠ SIMULATED EXPOSURE RISK</div>
                <div class="map-popup-sim-disclaimer">NOT A CONFIRMED CASE</div>
                <div class="map-popup-berth">${escapeHTML(String(p.note ?? ''))}</div>
                <div class="map-popup-source">
                  ANDV branching process &middot;
                  R<sub>eff</sub>=0.9/1.2 adaptive (high/standard-resource; density-adjusted) &middot;
                  incubation median 18d (Castillo EID 2012)
                </div>
                <div class="map-popup-sim-footer">
                  Generated by a mathematical model seeded from confirmed MV Hondius
                  cases only. Does not represent a confirmed, probable, or suspected case.
                </div>
              </div>
            ` : `
              <div class="map-popup map-popup-sim">
                <div class="map-popup-sim-warning">⚠ MONITORING — NOT A CASE</div>
                <div class="map-popup-sim-disclaimer">SIMULATED EXPOSURE CONTACT</div>
                <div class="map-popup-berth">${escapeHTML(String(p.note ?? ''))}</div>
                <div class="map-popup-source">
                  Under 42-day public-health observation &middot; no infection in this model run
                </div>
                <div class="map-popup-sim-footer">
                  Represents a passenger under monitoring. Not a confirmed,
                  probable, or suspected case. Stochastic — outcome varies by run.
                </div>
              </div>
            `)
            .addTo(map)
        })
        map.on('mouseenter', 'sim-cases', () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', 'sim-cases', () => { map.getCanvas().style.cursor = '' })
        // Flight arc tooltip
        map.on('click', 'sim-flights', (e) => {
          const f = e.features && e.features[0]
          if (!f) return
          const p = f.properties as Record<string, string | number>
          const kindLabel: Record<string, string> = {
            confirmed_case: '🔴 Confirmed-case route',
            exposure_monitoring: '🟡 Exposure-monitoring repatriation',
            crew_repatriation: '⚪ Crew repatriation',
            early_disembark: '🟠 Pre-declaration dispersal',
          }
          simPopup
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="map-popup map-popup-sim">
                <div class="map-popup-title">${escapeHTML(String(p.dest_city ?? ''))}</div>
                <div class="map-popup-berth">${kindLabel[String(p.kind)] ?? String(p.kind)}</div>
                <div class="map-popup-vessel-line">${escapeHTML(String(p.note ?? ''))}</div>
                <div class="map-popup-sim-footer">
                  These flight arcs show real documented dispersal routes from
                  official government repatriation records (WHO DON 600, CNN, NL MFA).
                  They are displayed in the simulation layer for context.
                </div>
              </div>
            `)
            .addTo(map)
        })
        map.on('mouseenter', 'sim-flights', () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', 'sim-flights', () => { map.getCanvas().style.cursor = '' })
      }
    }

    if (loadedRef.current) applySpread()
    else map.once('load', applySpread)

    return () => {
      // Layers persist while sim is active; cleared on stopSim.
    }
  }, [simActive, simDay])

  if (error) return <div className="world-map-error">Map data error: {error}</div>

  const totalAcross = incidents.reduce(
    (a, i) => a + i.confirmed_cases + i.suspected_cases + i.deaths,
    0,
  )
  const trackPoints = ontology?.vessel_track.length ?? 0

  return (
    <section className="world-map-section">
      <div className="world-map-header">
        <h3>Outbreak map &middot; vessel route + per-country case attribution</h3>
        <span className="map-count">
          {totalAcross} attributed across {incidents.reduce((a, i) => a + i.countries.filter(c => c.confirmed_count+c.suspected_count+c.deaths > 0).length, 0)} countries &middot; {trackPoints} track points
        </span>
      </div>
      <div className="world-map-container" ref={containerRef}>
        <button
          type="button"
          className={`spread-sim-toggle${simActive ? ' active' : ''}`}
          onClick={simActive ? stopSim : startSim}
          title={
            simActive
              ? 'Stop and clear the simulation layer'
              : 'Retrospective 90-day exposure-branch simulation — seeded from MV Hondius confirmed cases only. Purple dots = simulated risk, NOT confirmed cases.'
          }
        >
          {simActive ? '■ STOP SIM' : '▶ RUN SIMULATION'}
        </button>
        {simActive && (() => {
          const dayInt = Math.min(ANDV_PARAMS.projection_days, Math.ceil(simDay))
          const d = new Date(2026, 4, 10)
          d.setDate(d.getDate() + dayInt)
          const dateStr = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
          const all = simCasesRef.current
          const monitoring = all.filter((c) => !c.infected && c.day_exposed <= simDay && simDay < c.day_exposed + 42).length
          const active     = all.filter((c) => c.infected && c.day_symptoms <= simDay && c.day_outcome > simDay).length
          const incub      = all.filter((c) => c.infected && c.day_symptoms > simDay && c.day_symptoms <= simDay + 3).length
          const dead       = all.filter((c) => c.infected && c.will_die && c.day_outcome <= simDay).length
          const recovered  = all.filter((c) => c.infected && !c.will_die && c.day_outcome <= simDay && c.day_symptoms <= simDay).length
          const earlyDisp = SIM_FLIGHTS.filter((f) => f.flight_day < 0 && f.flight_day !== -27)
            .reduce((s, f) => s + f.pax_count, 0)
          const tenPax = SIM_FLIGHTS.filter((f) => f.flight_day >= 0)
            .reduce((s, f) => s + f.pax_count, 0)
          return (
            <div className="spread-sim-overlay">
              {/* ── PROMINENT SIMULATION WARNING ── */}
              <div className="spread-sim-mode-badge">
                ⚠ SIMULATION MODE — NOT CONFIRMED CASE DATA
              </div>
              <div className="spread-sim-mode-sub">
                Purple dots = modelled exposure risk only. Confirmed cases shown separately on map.
              </div>

              {/* ── Day + date ── */}
              <div className="spread-sim-day">
                Day <strong>{dayInt}</strong>
                <span className="spread-sim-day-suffix"> / {ANDV_PARAMS.projection_days}</span>
                <span className="spread-sim-date"> &middot; {dateStr} 2026</span>
              </div>

              {/* ── Timeline scrubber ── */}
              <div className="spread-sim-scrubber-row">
                <input
                  type="range"
                  min={0}
                  max={ANDV_PARAMS.projection_days}
                  step={1}
                  value={dayInt}
                  onChange={handleScrub}
                  className="sim-scrubber"
                  aria-label="Simulation day"
                />
                {simPaused && (
                  <button type="button" className="spread-sim-resume" onClick={resumeSim} title="Resume playback">
                    ▶
                  </button>
                )}
                {simFinished && !simPaused && (
                  <button type="button" className="spread-sim-resume" onClick={startSim} title="Replay from day 0">
                    ↻
                  </button>
                )}
              </div>

              {/* ── Simulated case counts ── */}
              {(monitoring + active + incub + recovered + dead) > 0 && (
                <div className="spread-sim-cases">
                  {monitoring > 0 && <><span className="sim-dot-mon" /> {monitoring} monitoring &nbsp;</>}
                  {active > 0     && <><span className="sim-dot-sym" /> {active} active sim &nbsp;</>}
                  {incub > 0      && <><span className="sim-dot-inc" /> {incub} incubating &nbsp;</>}
                  {recovered > 0  && <><span className="sim-dot-rec" /> {recovered} recovered &nbsp;</>}
                  {dead > 0       && <><span className="sim-dot-dead" /> {dead} sim fatal</>}
                </div>
              )}

              {/* ── Flight arc summary ── */}
              <div className="spread-sim-arcs">
                <span className="sim-arc-ten" /> {tenPax} pax · {SIM_FLIGHTS.filter(f => f.flight_day >= 0).length} routes from Tenerife
                &nbsp;&middot;&nbsp;
                <span className="sim-arc-sh" /> {earlyDisp} via Saint Helena (12 countries)
              </div>

              {/* ── Model parameters ── */}
              <div className="spread-sim-caveat">
                ANDV close-contact model &middot; R<sub>eff</sub>=0.9/1.2 adaptive (Martínez 2020 calibrated) &middot;
                incubation median 18d Erlang(k=11) &middot; seeded from confirmed cases only &middot;
                not a forecast
              </div>
            </div>
          )
        })()}
      </div>
      <div className="map-legend">
        <span className="legend-item">
          <span className="legend-square pz" /> suspected exposure (patient zero)
        </span>
        <span className="legend-item">
          <span className="legend-square dest has-case" /> confirmed cases
        </span>
        <span className="legend-item">
          <span className="legend-square dest" /> suspected only
        </span>
        <span className="legend-item">
          <span className="legend-line solid" /> vessel route
        </span>
        <span className="legend-item">
          <span className="legend-square sim-legend-dot" style={{ background: '#d97706' }} /> monitoring (sim)
        </span>
        <span className="legend-item">
          <span className="legend-square sim-legend-dot" style={{ background: '#7c3aed' }} /> sim exposure risk (NOT a case)
        </span>
        <span className="legend-item">
          <span className="legend-line sim-legend-arc" /> exposure branch (sim)
        </span>
      </div>
    </section>
  )
}
