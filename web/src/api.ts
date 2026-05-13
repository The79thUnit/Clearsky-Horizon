import type {
  CaseList,
  ClusterDetail,
  ClusterList,
  EventList,
  IncidentDetail,
  IncidentList,
  IncidentOntology,
  SourceList,
  StatsResponse,
} from './types'

// Production: empty string = same-origin (nginx proxies /api/* to the api service).
// Dev (npm run dev): falls back to the local FastAPI server on :8000.
export const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  (import.meta.env.DEV ? 'http://localhost:8000' : '')

/**
 * Single-shot GET with built-in retry on transient 5xx responses.
 *
 * Why: nginx's resolver has a 1-second negative cache, so when Docker's
 * embedded DNS hiccups for ~5ms during a container rebuild, the next
 * ~1s of requests see HTTP 502/503. We catch those at the FE level and
 * silently retry once after a short wait — the user never sees a red
 * "API 502" banner for a transient DNS blip.
 *
 * Also handles the structured 503 `{"error":"upstream_resolving"}` that
 * nginx emits from @api_fail_json when its own retry path fails.
 *
 * One retry is enough: by then the resolver cache has expired and the
 * api container is reachable again. Failing twice in a row indicates a
 * real outage, which we DO want to surface to the user.
 */
async function get<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`
  const headers = { accept: 'application/json' }

  let res = await fetch(url, { headers })

  // Transient gateway / upstream-resolving conditions get one retry.
  if (res.status === 502 || res.status === 503 || res.status === 504) {
    await new Promise((r) => setTimeout(r, 1200))
    res = await fetch(url, { headers, cache: 'no-store' })
  }

  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function fetchCases(limit = 50, offset = 0): Promise<CaseList> {
  return get<CaseList>(`/api/v1/cases?limit=${limit}&offset=${offset}`)
}

export function fetchSources(): Promise<SourceList> {
  return get<SourceList>('/api/v1/sources')
}

export function fetchClusters(limit = 100): Promise<ClusterList> {
  return get<ClusterList>(`/api/v1/clusters?limit=${limit}`)
}

export function fetchCluster(id: string): Promise<ClusterDetail> {
  return get<ClusterDetail>(`/api/v1/clusters/${id}`)
}

export function fetchStats(): Promise<StatsResponse> {
  return get<StatsResponse>('/api/v1/meta/stats')
}

export function fetchEvents(limit = 50): Promise<EventList> {
  return get<EventList>(`/api/v1/meta/events?limit=${limit}`)
}

export function fetchIncidents(): Promise<IncidentList> {
  return get<IncidentList>('/api/v1/incidents')
}

export function fetchIncident(idOrCode: string): Promise<IncidentDetail> {
  return get<IncidentDetail>(`/api/v1/incidents/${idOrCode}`)
}

export function fetchIncidentOntology(code: string): Promise<IncidentOntology> {
  return get<IncidentOntology>(`/api/v1/incidents/${code}/ontology`)
}
