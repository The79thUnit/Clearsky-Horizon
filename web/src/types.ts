export interface CaseRecord {
  id: string
  source_code: string
  source_name: string
  src_citation: string
  title: string
  summary: string | null
  country_iso2: string | null
  region: string | null
  serotype_code: string | null
  serotype_text: string | null
  reported_date: string | null
  ingested_at: string
  raw_url: string
  nato_reliability: string
  nato_credibility: number
  pipeline_confidence: number
  analyst_confidence: number | null
}

export interface CaseList {
  items: CaseRecord[]
  total: number
  limit: number
  offset: number
}

export interface SourceRecord {
  id: string
  code: string
  name: string
  tier: number
  provenance_type: string
  nato_reliability: string
  nato_credibility: number
  enabled: boolean
  last_fetched_at: string | null
  last_http_status: number | null
  last_latency_ms: number | null
  total_items_ingested: number
}

export interface SourceList {
  items: SourceRecord[]
}

export interface ClusterRecord {
  id: string
  name: string
  country_iso2: string | null
  region: string | null
  serotype_code: string | null
  started_at: string | null
  ended_at: string | null
  status: string
  case_count: number
  death_count: number
}

export interface ClusterList {
  items: ClusterRecord[]
  total: number
}

export interface ClusterDetail extends ClusterRecord {
  cases: CaseRecord[]
}

export interface BreakdownEntry {
  label: string
  count: number
}

export interface StatsResponse {
  // Authoritative real-world counters (from WHO DON, CDC HAN, PAHO alerts).
  total_confirmed_cases_authoritative: number
  total_suspected_cases_authoritative: number
  total_deaths_authoritative: number
  total_active_incidents: number
  // Ingestion telemetry (what the pipeline has consumed; informational only).
  total_reports_ingested: number
  total_countries_in_reports: number
  total_clusters_active: number
  total_serotypes_seen: number
  total_sources_enabled: number
  reports_last_24h: number
  reports_last_7d: number
  reports_last_14d: number
  by_serotype: BreakdownEntry[]
  by_country: BreakdownEntry[]
}

export interface IncidentCountryRow {
  country_iso2: string
  confirmed_count: number
  suspected_count: number
  deaths: number
  first_reported_at: string | null
}

export interface IncidentAuthoritativeCount {
  confirmed_cases: number
  suspected_cases: number
  deaths: number
  recovered: number
  source_code: string
  source_name: string
  reported_at: string
  nato_reliability: string
  nato_credibility: number
  src_citation: string
  notes: string | null
}

export interface IncidentRecord {
  id: string
  code: string
  name: string
  serotype_code: string | null
  started_at: string | null
  ended_at: string | null
  status: string
  summary: string | null
  primary_location_country_iso2: string | null
  primary_location_name: string | null
  primary_vessel_imo: string | null
  primary_vessel_name: string | null
  primary_vessel_mmsi: string | null
  primary_vessel_flag: string | null
  confirmed_cases: number
  suspected_cases: number
  deaths: number
  recovered: number
  authority_source_code: string | null
  authority_reported_at: string | null
  corroborating_sources: number
  countries: IncidentCountryRow[]
}

export interface IncidentList {
  items: IncidentRecord[]
  total: number
}

export interface IncidentDetail extends IncidentRecord {
  counts_history: IncidentAuthoritativeCount[]
}

export interface EntityRecord {
  id: string
  entity_type: string
  public_label: string | null
  properties: Record<string, unknown>
}

export interface RelationshipRecord {
  id: string
  src_id: string
  dst_id: string
  rel_type: string
  properties: Record<string, unknown>
  confidence: number
  src_citation: string
}

export interface VesselTrackPoint {
  ts: string
  lat: number
  lng: number
  speed_knots: number | null
  heading: number | null
  source: string
}

export interface IncidentOntology {
  incident_code: string
  entities: EntityRecord[]
  relationships: RelationshipRecord[]
  vessel_track: VesselTrackPoint[]
}

export interface TickEvent {
  type: 'tick'
  ts: string
}

export type EventType =
  | 'case'
  | 'fatality'
  | 'cluster_new'
  | 'cluster_update'
  | 'statement'
  | 'medevac'
  | 'milestone'

export type EventSeverity = 'info' | 'notice' | 'alert' | 'critical'

export interface EventRecord {
  id: string
  occurred_at: string
  event_type: EventType
  severity: EventSeverity
  title: string
  summary: string | null
  country_iso2: string | null
  serotype_code: string | null
  source_code: string | null
  source_url: string | null
  cluster_id: string | null
}

export interface EventList {
  items: EventRecord[]
  total: number
}
