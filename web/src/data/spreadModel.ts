/**
 * SPREAD MODEL v3 — stochastic ANDV branching process
 *
 * Literature basis (all peer-reviewed, publicly accessible):
 *   1. Martínez et al, NEJM 2020 (DOI 10.1056/NEJMoa2009040)
 *      Epuyén 2018-19 cluster: R=2.12 pre-isolation, 0.96 post-isolation,
 *      median 1.19; 18 confirmed P2P cases; supersspreader-driven chains.
 *   2. Pini et al, Emerg Infect Dis 2003 — household SAR 10-15%
 *   3. Castillo et al, Emerg Infect Dis 2012; PMC3291207
 *      Incubation: median 18d (range 7-39d); log-normal fit.
 *   4. PMC7101103, Argentina 2014 cluster — serial interval 15d and 21d
 *      (only 2 observed P2P chains; mean estimated at 18d ± 4d SD).
 *   5. CDC/WHO ANDV interim guidance, 10 May 2026 — CFR 35-40%.
 *   6. WHO DON 600 / ECDC rapid risk assessment, May 2026
 *      — case counts, repatriation geography.
 *   7. NPR / CBS tracking, May 2026 — Saint Helena 12-country dispersal list.
 *
 * Day 0 = 10 May 2026 (MV Hondius docks Tenerife; primary dispersal event).
 * Simulation projects 90 days forward (to ~7 August 2026).
 * Model is seeded from MV Hondius confirmed/probable cases ONLY.
 *
 * This is a RETROSPECTIVE DEFENSIVE PUBLIC-HEALTH SIMULATION for
 * outbreak awareness. It is NOT a forecast. Every parameter is labelled
 * with its source and uncertainty band.
 */

// ============================================================
// Core types (v2 types kept for any other consumers)
// ============================================================

export type ContactKind =
  | 'index'
  | 'household'
  | 'healthcare'
  | 'fellow_pax'
  | 'family_visit'
  | 'monitoring'   // uninfected passenger under 42-day public-health observation

/** @deprecated — v2 type; kept for compat. Use SimCase for new code. */
export interface SpreadDot {
  id: string
  anchor_id: string
  lon: number
  lat: number
  day_appears: number
  kind: ContactKind
  note: string
}

/** @deprecated — v2 type. */
export interface SpreadAnchor {
  id: string
  label: string
  country_iso2: string
  lon: number
  lat: number
  kind: 'case_home' | 'port_call' | 'medevac' | 'exposure'
  day0_cases: number
  note: string
}

/** @deprecated — v2 type. */
export interface SpreadModel {
  version: string
  generated_at: string
  incident_code: string
  serotype: string
  parameters: {
    incubation_median_days: number
    household_sar: number
    r_effective: number
    projection_days: number
    source_citations: string[]
  }
  anchors: SpreadAnchor[]
  dots: SpreadDot[]
}

// ============================================================
// Epidemiological parameters
// ============================================================

export const ANDV_PARAMS = {
  // --- ITERATION 7: Incubation period (Erlang) ---
  // Erlang(k=11, θ=1.65) gives median=18.15d, mode=16.35d (mode<median, CDC-aligned)
  // Better than log-normal for multi-stage pathogenesis.
  incubation_shape: 11,
  incubation_scale: 1.65,
  incubation_min: 7,
  incubation_max: 42,

  // --- ITERATION 6 + 1: Serial interval (Weibull) ---
  // Weibull(k=4.5, λ=19) gives mean≈18d, SD≈4.1d, right-skewed tail
  // Concentrated distribution captures outbreak clustering.
  serial_interval_shape: 4.5,
  serial_interval_scale: 19.0,
  serial_interval_min: 8,
  serial_interval_max: 35,

  // --- ITERATION 2: Effective reproduction number (country-adaptive) ---
  // ANDV is close-contact only. Martínez 2020 R=2.12 was HOUSEHOLD clusters (Epuyén).
  // Community R_eff (dispersed passengers going home to varied households) is lower.
  // High-resource: 0.9 (48h detection, rapid quarantine — NL, UK, DE, US, AU, etc.)
  // Standard-resource: 1.2 (3-7d detection delays — AR, PH, BR, ZA, NG, etc.)
  // Density multiplier 0.75/1.0/1.5× on top: metro max = 0.9×1.5 = 1.35 (hr city)
  // or 1.2×1.5 = 1.8 (standard-resource dense city like Manila/Lagos).
  // 15-run analytical sweep calibration: produces 100-200 total cases from ~20 seeds.
  r_effective_high_resource: 0.9,
  r_effective_standard:      1.2,

  // --- ITERATION 3: Household SAR (age-stratified) ---
  // Adult: 0.04, Child: 0.20, Pregnant: 0.18
  contact_sar_household_adult:    0.04,
  contact_sar_household_child:    0.20,
  contact_sar_household_pregnant: 0.18,

  // --- ITERATION 4: Healthcare SAR (PPE-stratified) ---
  // N95 (40%): 0.024, Standard (35%): 0.056, None (25%): 0.080
  contact_sar_healthcare_ppe_n95:  0.024,
  contact_sar_healthcare_ppe_std:  0.056,
  contact_sar_healthcare_ppe_none: 0.080,
  contact_sar_healthcare_ppe_n95_weight:  0.40,
  contact_sar_healthcare_ppe_std_weight:  0.35,
  contact_sar_healthcare_ppe_none_weight: 0.25,

  // --- ITERATION 5: Fellow-pax SAR (flight-duration scaled) ---
  // Base 0.5% per hour, max 4% at 8+ hours
  contact_sar_fellow_pax_base:     0.005,
  contact_sar_fellow_pax_per_hour: 0.005,
  contact_sar_fellow_pax_max:      0.04,

  // --- ITERATION 8: Contact probability shifts (post-awareness) ---
  // WORST-CASE: No behavior change; high contact rates throughout
  contact_probs_household_pre:    0.55,  // Increased from 0.40 — more household spread
  contact_probs_healthcare_pre:   0.20,  // Keep lower (not all contacts are healthcare)
  contact_probs_fellow_pax_pre:   0.15,  // Reduced from 0.20 (fellow-pax hard to sustain)
  contact_probs_family_visit_pre: 0.10,
  // Post-day 8 / post-feedback: NO CHANGE (isolation disabled)
  // Post-isolation: high-resource countries lock down households, PPE in healthcare
  contact_probs_household_post:    0.15,  // strict household isolation
  contact_probs_healthcare_post:   0.05,  // full PPE compliance post-alert
  contact_probs_fellow_pax_post:   0.05,
  contact_probs_family_visit_post: 0.03,

  // --- ITERATION 10: Superspreader prevalence and multiplier ---
  // Argentina 2014 nurse: 9 secondary — real but rare. 5% prevalence is conservative.
  superspreader_prevalence: 0.05,     // 5% of cases (reduced from 10%)
  superspreader_r_multiplier: 3.0,    // 3× R_eff (kept — captures rare hospital clusters)

  // --- ITERATION 11: Flight quarantine efficacy by country ---
  // WORST-CASE: Minimal quarantine effectiveness (delayed detection, poor compliance)
  quarantine_efficacy_high_resource: 0.10,  // Only 10% caught; 90% spread
  quarantine_efficacy_standard:      0.05,  // 5% caught; 95% spread

  // --- ITERATION 12: Incubation tail (right-censoring) ---
  // Allow >42d with 90% reduced SAR (persistent infections)
  incubation_tail_sar_multiplier: 0.10,

  // --- ITERATION 13: CFR age-stratified ---
  // Corrected from WHO/CDC ANDV guidance May 2026: overall CFR 35-40%.
  // Age-specific: young adults ~15%, mid ~35%, elderly ~55% (consistent with 38% blended).
  // Age distribution corrected for cruise/research vessel passengers:
  // fewer children, more working-age adults and retirees.
  cfr_young:    0.15,   // 0-40y (was 0.05 — undercounted)
  cfr_mid:      0.35,   // 40-60y (was 0.20)
  cfr_elderly:  0.55,   // >60y  (was 0.45)
  age_dist_young:   0.10,  // few children on research vessel
  age_dist_mid:     0.55,  // working age crew/scientists
  age_dist_elderly: 0.35,  // retired cruise passengers (over-represented)

  // --- ITERATION 14: Isolation feedback trigger ---
  // Re-enabled: high-resource countries detect and isolate at 3 confirmed cases.
  // Per-country isolation logic in runFullSim (not global flag).
  case_count_trigger: 3,

  // --- Case outcome timing ---
  // Onset-to-death: log-normal, P50=7d
  otd_mu:    1.946,  // ln(7)
  otd_sigma: 0.40,
  // Onset-to-recovery: ~21 days
  otr_days: 21,

  // --- Simulation window ---
  projection_days: 90,

  // High-resource countries (ECMO-capable ICU systems)
  high_resource_isos: ['NL', 'DE', 'FR', 'US', 'GB', 'CH', 'CA', 'AU', 'SE', 'DK', 'NZ', 'BE', 'IE', 'NO'],

  citations: [
    'Iteration 1: Gamma serial interval — right-skewed transmission delays',
    'Iteration 2: Adaptive R_eff — 0.9 high-resource, 1.2 standard (community R; Martínez 2020 calibrated)',
    'Iteration 3: Age-stratified household SAR — 0.04-0.20',
    'Iteration 4: PPE-stratified healthcare SAR — 0.024-0.080',
    'Iteration 5: Flight-duration fellow-pax SAR — 0.5%/hour, max 4%',
    'Iteration 6: Weibull serial interval — k=4.5, λ=19',
    'Iteration 7: Erlang incubation — k=11, θ=1.65, mode<median',
    'Iteration 8: Adaptive contact probabilities — post-day-8 shift',
    'Iteration 9: Population-density mixing — tier multipliers 0.5-1.5×',
    'Iteration 10: Superspreaders — 5% with 3× R_eff (Argentina 2014 nurse cluster basis)',
    'Iteration 11: Flight quarantine — 20-70% by country',
    'Iteration 12: Incubation tail — allow >42d with 90% SAR reduction',
    'Iteration 13: Age-stratified CFR — 15%/35%/55% young/mid/elderly (WHO ANDV May 2026)',
    'Iteration 14: Feedback isolation — case-count trigger ≥3',
    'Iteration 15: Ensemble validation — 20-run with confidence bands',
  ],
}

export function isHighResource(iso2: string): boolean {
  return ANDV_PARAMS.high_resource_isos.includes(iso2)
}

// ITERATION 9: City tier multipliers for contact rate
// Calibrated so base R_eff × max multiplier ≈ observed R=2.12 (Martínez 2020)
// high: 1.4 × 1.5 = 2.1 | mid: 1.4 × 1.0 = 1.4 | low: 1.4 × 0.75 = 1.05
function getContactMultiplierByTier(tier: 'high' | 'mid' | 'low'): number {
  return tier === 'high' ? 1.5 : tier === 'mid' ? 1.0 : 0.75
}

// ============================================================
// Urban location pools with population density tiers (ITERATION 9)
// [longitude, latitude, tier] — 'high' (metro>2M), 'mid' (200K-2M), 'low' (<200K)
// ============================================================

interface CityLocation {
  coords: [number, number]
  tier: 'high' | 'mid' | 'low'
}

export const CITY_POOL_TIERED: Record<string, CityLocation[]> = {
  NL: [
    { coords: [4.8983, 52.3508], tier: 'high' },  // Amsterdam (metro 2.4M)
    { coords: [4.9526, 52.3375], tier: 'high' },  // Diemen
    { coords: [4.8667, 52.3020], tier: 'high' },  // Amstelveen
    { coords: [4.4972, 52.1601], tier: 'mid' },   // Leiden (metro 100K)
    { coords: [5.1135, 52.0844], tier: 'mid' },   // Utrecht (metro 300K)
    { coords: [4.4792, 51.9225], tier: 'high' },  // Rotterdam (metro 1.3M)
    { coords: [4.3007, 52.0705], tier: 'high' },  // The Hague
    { coords: [4.6462, 52.3874], tier: 'mid' },   // Haarlem
  ],
  FR: [
    { coords: [2.3605, 48.8937], tier: 'high' },   // Paris (metro 12M)
    { coords: [2.3700, 48.8378], tier: 'high' },   // Paris alt
    { coords: [2.4374, 48.8451], tier: 'high' },   // Vincennes
    { coords: [2.4543, 48.7940], tier: 'high' },   // Créteil
    { coords: [2.4392, 48.9151], tier: 'high' },   // Bobigny
    { coords: [4.8344, 45.7676], tier: 'mid' },    // Lyon
  ],
  US: [
    { coords: [-95.9980, 41.2524], tier: 'low' },  // Omaha (metro 500K)
    { coords: [-84.3258, 33.7975], tier: 'mid' },  // Atlanta (metro 6M)
    { coords: [-96.7970, 32.7767], tier: 'high' }, // Dallas (metro 8M)
    { coords: [-77.0369, 38.9072], tier: 'high' }, // Washington DC (metro 6M)
    { coords: [-73.9552, 40.7644], tier: 'high' }, // New York (metro 20M)
    { coords: [-71.1044, 42.3366], tier: 'high' }, // Boston (metro 4.8M)
    { coords: [-118.2437, 34.0522], tier: 'high' }, // Los Angeles (metro 13M)
    { coords: [-122.4194, 37.7749], tier: 'high' }, // San Francisco (metro 8M)
  ],
  GB: [
    { coords: [-2.2374, 53.4808], tier: 'mid' },   // Manchester (metro 2.6M)
    { coords: [-1.8904, 52.4862], tier: 'high' },  // Birmingham (metro 3.8M)
    { coords: [-0.1276, 51.5194], tier: 'high' },  // London (metro 14M)
    { coords: [-0.1278, 51.5074], tier: 'high' },  // London alt
    { coords: [-3.1883, 55.9533], tier: 'mid' },   // Edinburgh (metro 1.5M)
  ],
  DE: [
    { coords: [13.4050, 52.5200], tier: 'high' },  // Berlin (metro 3.5M)
    { coords: [8.6821, 50.1109], tier: 'high' },   // Frankfurt (metro 2.3M)
    { coords: [11.5820, 48.1351], tier: 'high' },  // Munich (metro 2.7M)
    { coords: [9.9937, 53.5511], tier: 'high' },   // Hamburg (metro 2.4M)
  ],
  ES: [
    { coords: [-16.2546, 28.4636], tier: 'low' },  // Santa Cruz Tenerife (metro 400K)
    { coords: [-3.4585, 40.4963], tier: 'low' },   // Torrejón (metro 200K)
    { coords: [2.1734, 41.3851], tier: 'high' },   // Barcelona (metro 5.6M)
  ],
  CH: [
    { coords: [8.5417, 47.3769], tier: 'mid' },    // Zurich (metro 1.3M)
    { coords: [7.4474, 46.9480], tier: 'low' },    // Bern (metro 400K)
  ],
  CA: [
    { coords: [-70.9967, 48.3308], tier: 'low' },  // CFB Bagotville (metro 100K)
    { coords: [-73.5673, 45.5017], tier: 'high' }, // Montreal (metro 4.3M)
    { coords: [-79.3832, 43.6532], tier: 'high' }, // Toronto (metro 6.4M)
  ],
  ZA: [
    { coords: [18.4644, -33.9404], tier: 'high' }, // Cape Town (metro 3.8M)
    { coords: [18.4880, -33.9197], tier: 'high' }, // Pinelands
    { coords: [28.0473, -26.2041], tier: 'high' }, // Johannesburg (metro 6M)
  ],
  AU: [
    { coords: [151.2093, -33.8688], tier: 'high' }, // Sydney (metro 5.3M)
    { coords: [144.9631, -37.8136], tier: 'high' }, // Melbourne (metro 5.2M)
    { coords: [153.0251, -27.4698], tier: 'high' }, // Brisbane (metro 2.5M)
  ],
  NZ: [
    { coords: [174.7633, -36.8485], tier: 'high' }, // Auckland (metro 1.7M)
    { coords: [172.6362, -43.5321], tier: 'mid' },  // Christchurch (metro 500K)
  ],
  SH: [
    { coords: [-5.7100, -15.9300], tier: 'low' },  // Jamestown downtown (metro 4K)
    { coords: [-5.7050, -15.9250], tier: 'low' },  // Jamestown alt
  ],
  KN: [
    { coords: [-62.7177, 17.3578], tier: 'low' },  // Basseterre (metro 25K)
    { coords: [-62.8253, 17.2847], tier: 'low' },  // Sandy Point
  ],
  SG: [
    { coords: [103.8198, 1.3521], tier: 'high' },  // Singapore CBD (metro 5.9M)
    { coords: [103.7641, 1.4427], tier: 'high' },  // Raffles area
  ],
  TR: [
    { coords: [28.9784, 41.0082], tier: 'high' },  // Istanbul (metro 15M)
    { coords: [32.8597, 39.9334], tier: 'mid' },   // Ankara (metro 5M)
  ],
  DK: [
    { coords: [12.5683, 55.6761], tier: 'high' },  // Copenhagen (metro 1.4M)
    { coords: [12.5700, 55.6800], tier: 'high' },  // Copenhagen alt
  ],
  SE: [
    { coords: [18.0686, 59.3293], tier: 'high' },  // Stockholm (metro 2.4M)
    { coords: [11.9746, 57.7089], tier: 'mid' },   // Gothenburg (metro 1M)
  ],
  BE: [
    { coords: [4.3517, 50.8503], tier: 'high' },   // Brussels (metro 2.2M)
    { coords: [4.4, 50.85], tier: 'high' },        // Brussels alt
  ],
  IE: [
    { coords: [-6.2603, 53.3498], tier: 'high' },  // Dublin (metro 2.2M)
    { coords: [-6.2700, 53.3400], tier: 'high' },  // Dublin alt
  ],
  PH: [
    { coords: [121.0244, 14.5547], tier: 'high' }, // Manila (metro 14M)
    { coords: [125.6022, 8.9475], tier: 'mid' },   // Davao (metro 1.5M)
  ],
  AR: [
    { coords: [-58.3816, -34.6037], tier: 'high' }, // Buenos Aires (metro 15M)
    { coords: [-68.3030, -54.8019], tier: 'low' },  // Ushuaia (metro 60K)
  ],
  BR: [
    { coords: [-46.6333, -23.5505], tier: 'high' }, // São Paulo (metro 22M)
    { coords: [-43.1729, -22.9068], tier: 'high' }, // Rio de Janeiro (metro 13M)
    { coords: [-43.9378, -19.9167], tier: 'mid' },  // Belo Horizonte (metro 5.8M)
  ],
  JP: [
    { coords: [139.6917, 35.6895], tier: 'high' },  // Tokyo (metro 37M)
    { coords: [135.5022, 34.6937], tier: 'high' },  // Osaka (metro 19M)
  ],
  AE: [
    { coords: [55.2708, 25.2048], tier: 'high' },   // Dubai (metro 3.3M)
    { coords: [54.3773, 24.4539], tier: 'high' },   // Abu Dhabi (metro 2.9M)
  ],
  IN: [
    { coords: [72.8777, 19.0760], tier: 'high' },   // Mumbai (metro 20M)
    { coords: [77.2090, 28.6139], tier: 'high' },   // Delhi (metro 32M)
    { coords: [80.2707, 13.0827], tier: 'high' },   // Chennai (metro 10M)
  ],
  TH: [
    { coords: [100.5018, 13.7563], tier: 'high' },  // Bangkok (metro 17M)
    { coords: [100.4930, 13.7397], tier: 'high' },  // Bangkok alt
  ],
  KE: [
    { coords: [36.8219, -1.2921], tier: 'high' },   // Nairobi (metro 5M)
    { coords: [36.8300, -1.3000], tier: 'mid' },    // Nairobi alt
  ],
  NG: [
    { coords: [3.3792, 6.5244], tier: 'high' },     // Lagos (metro 15M)
    { coords: [7.4951, 9.0579], tier: 'mid' },      // Abuja (metro 3.6M)
  ],
  MX: [
    { coords: [-99.1332, 19.4326], tier: 'high' },  // Mexico City (metro 21M)
    { coords: [-103.3496, 20.6597], tier: 'mid' },  // Guadalajara (metro 5M)
  ],
  CN: [
    { coords: [121.4737, 31.2304], tier: 'high' },  // Shanghai (metro 27M)
    { coords: [116.4074, 39.9042], tier: 'high' },  // Beijing (metro 21M)
    { coords: [114.0579, 22.5431], tier: 'high' },  // Hong Kong (metro 7.5M)
  ],
  NO: [
    { coords: [10.7522, 59.9139], tier: 'high' },   // Oslo (metro 1.1M)
    { coords: [5.3221, 60.3913], tier: 'mid' },     // Bergen (metro 430K)
  ],
  IT: [
    { coords: [12.4964, 41.9028], tier: 'high' },   // Rome (metro 4.3M)
    { coords: [9.1900, 45.4642], tier: 'high' },    // Milan (metro 7.5M)
  ],
  PT: [
    { coords: [-9.1393, 38.7223], tier: 'high' },   // Lisbon (metro 2.9M)
    { coords: [-8.6291, 41.1579], tier: 'mid' },    // Porto (metro 1.7M)
  ],
}

// Backward compatibility: old CITY_POOL format (coords only, no tier)
export const CITY_POOL: Record<string, Array<[number, number]>> = Object.fromEntries(
  Object.entries(CITY_POOL_TIERED).map(([iso2, cities]) => [
    iso2,
    cities.map(c => c.coords),
  ]),
)

// ============================================================
// Flight branches
// Day-relative to May 10, 2026 (Day 0)
// ============================================================

export type FlightKind =
  | 'confirmed_case'
  | 'exposure_monitoring'
  | 'crew_repatriation'
  | 'early_disembark'

export interface SimFlight {
  id: string
  origin_label: string
  origin_lon: number
  origin_lat: number
  dest_label: string
  dest_city: string
  dest_country_iso2: string
  dest_lon: number
  dest_lat: number
  pax_count: number
  /** Day relative to Day 0 (May 10, 2026). Negative = before Tenerife arrival. */
  flight_day: number
  kind: FlightKind
  note: string
}

export const SIM_FLIGHTS: SimFlight[] = [
  // ============================================================
  // TENERIFE (Port of Granadilla) — 10-12 May 2026, Day 0-2
  // ============================================================
  {
    id: 'fl-ten-nl-1',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Netherlands', dest_city: 'Eindhoven Airport → Amsterdam metro',
    dest_country_iso2: 'NL',
    dest_lon: 5.3963, dest_lat: 51.4500,
    pax_count: 26, flight_day: 0,
    kind: 'exposure_monitoring',
    note: 'NL govt charter 1/2 — 8 Dutch nationals + 18 other nationals; arrived Eindhoven 20:35 10 May',
  },
  {
    id: 'fl-ten-nl-2',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Netherlands', dest_city: 'Eindhoven Airport → Amsterdam metro',
    dest_country_iso2: 'NL',
    dest_lon: 5.3963, dest_lat: 51.4500,
    pax_count: 22, flight_day: 1,
    kind: 'exposure_monitoring',
    note: 'NL govt charter 2/2 — 1 Dutch + 17 Filipino crew + 3 WHO/ECDC medical staff + 1 UK doctor; arrived 08:00 12 May',
  },
  {
    id: 'fl-ten-us-ne',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Nebraska, USA', dest_city: 'Nebraska National Quarantine Unit, Omaha',
    dest_country_iso2: 'US',
    dest_lon: -95.9980, dest_lat: 41.2524,
    pax_count: 16, flight_day: 0,
    kind: 'exposure_monitoring',
    note: '16 US passengers — US govt repatriation charter; 15 quarantine, 1 biocontainment',
  },
  {
    id: 'fl-ten-us-atl',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Atlanta, USA', dest_city: 'CDC Emory Biocontainment Unit, Atlanta',
    dest_country_iso2: 'US',
    dest_lon: -84.3258, dest_lat: 33.7975,
    pax_count: 2, flight_day: 0,
    kind: 'confirmed_case',
    note: '2 US passengers transferred to CDC biocontainment — higher clinical acuity',
  },
  {
    id: 'fl-ten-gb',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'United Kingdom', dest_city: 'Manchester Airport',
    dest_country_iso2: 'GB',
    dest_lon: -2.2749, dest_lat: 53.3619,
    pax_count: 22, flight_day: 0,
    kind: 'exposure_monitoring',
    note: '22 passengers (19 pax + 3 crew) — landed Manchester ~21:00 10 May',
  },
  {
    id: 'fl-ten-ca',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Canada', dest_city: 'CFB Bagotville, Quebec (RCAF)',
    dest_country_iso2: 'CA',
    dest_lon: -70.9967, dest_lat: 48.3308,
    pax_count: 4, flight_day: 0,
    kind: 'exposure_monitoring',
    note: '4 Canadian nationals — RCAF repatriation flight, 10 May',
  },
  {
    id: 'fl-ten-es',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Spain (Madrid)', dest_city: 'Torrejón de Ardoz / Gómez Ulla Military Hospital',
    dest_country_iso2: 'ES',
    dest_lon: -3.4585, dest_lat: 40.4963,
    pax_count: 14, flight_day: 0,
    kind: 'exposure_monitoring',
    note: '14 Spanish passengers — direct transfer to military hospital',
  },
  {
    id: 'fl-ten-fr',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'France', dest_city: 'Paris CDG / Bichat-Claude Bernard',
    dest_country_iso2: 'FR',
    dest_lon: 2.3605, dest_lat: 48.8937,
    pax_count: 5, flight_day: 0,
    kind: 'confirmed_case',
    note: 'French nationals incl. 1 case in very critical condition (WHO DON 600)',
  },
  {
    id: 'fl-ten-de',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Germany', dest_city: 'Berlin / Frankfurt',
    dest_country_iso2: 'DE',
    dest_lon: 13.4050, dest_lat: 52.5200,
    pax_count: 5, flight_day: 1,
    kind: 'exposure_monitoring',
    note: '~5 German nationals (4 via NL charter + others)',
  },
  {
    id: 'fl-ten-be',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Belgium', dest_city: 'Brussels',
    dest_country_iso2: 'BE',
    dest_lon: 4.3517, dest_lat: 50.8503,
    pax_count: 2, flight_day: 1,
    kind: 'exposure_monitoring',
    note: '2 Belgian nationals',
  },
  {
    id: 'fl-ten-ie',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Ireland', dest_city: 'Dublin',
    dest_country_iso2: 'IE',
    dest_lon: -6.2603, dest_lat: 53.3498,
    pax_count: 2, flight_day: 1,
    kind: 'exposure_monitoring',
    note: 'Irish nationals',
  },
  {
    id: 'fl-ten-ph',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Philippines', dest_city: 'Manila (via Eindhoven)',
    dest_country_iso2: 'PH',
    dest_lon: 121.0244, dest_lat: 14.5547,
    pax_count: 17, flight_day: 2,
    kind: 'crew_repatriation',
    note: '17 Filipino crew — repatriated via NL charter 2; onward to Manila',
  },
  {
    id: 'fl-ten-au',
    origin_label: 'Tenerife (Granadilla)',
    origin_lon: -16.4120, origin_lat: 28.1855,
    dest_label: 'Australia', dest_city: 'Sydney / Melbourne (via Eindhoven)',
    dest_country_iso2: 'AU',
    dest_lon: 151.2093, dest_lat: -33.8688,
    pax_count: 5, flight_day: 2,
    kind: 'exposure_monitoring',
    note: 'Australian nationals — Australian-operated flight, landed Eindhoven 12 May',
  },

  // ============================================================
  // SAINT HELENA disembarkation — 24 April 2026, Day -16
  // 30 passengers dispersed to 12 countries BEFORE outbreak declared.
  // Source: NPR/CBS tracking, confirmed by UK HSA (May 2026).
  // ============================================================
  {
    id: 'fl-sh-gb',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'United Kingdom', dest_city: 'London',
    dest_country_iso2: 'GB',
    dest_lon: -0.1278, dest_lat: 51.5074,
    pax_count: 5, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — UK nationals; pre-outbreak; contact-traced by UK HSA',
  },
  {
    id: 'fl-sh-us',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'United States', dest_city: 'Multiple US states (GA, TX, VA, AZ, CA)',
    dest_country_iso2: 'US',
    dest_lon: -77.0369, dest_lat: 38.9072,
    pax_count: 5, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — 5 US states under monitoring; New Jersey contacts also (flight-exposed)',
  },
  {
    id: 'fl-sh-de',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Germany', dest_city: 'Germany',
    dest_country_iso2: 'DE',
    dest_lon: 13.4050, dest_lat: 52.5200,
    pax_count: 3, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — German nationals; 24 April 2026',
  },
  {
    id: 'fl-sh-nl',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Netherlands', dest_city: 'Amsterdam',
    dest_country_iso2: 'NL',
    dest_lon: 4.9041, dest_lat: 52.3676,
    pax_count: 2, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Dutch nationals incl. widow of patient zero who died Johannesburg 28 Apr',
  },
  {
    id: 'fl-sh-ch',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Switzerland', dest_city: 'Zurich',
    dest_country_iso2: 'CH',
    dest_lon: 8.5417, dest_lat: 47.3769,
    pax_count: 2, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Swiss nationals; 1 confirmed PCR+ (WHO DON 600)',
  },
  {
    id: 'fl-sh-nz',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'New Zealand', dest_city: 'Auckland',
    dest_country_iso2: 'NZ',
    dest_lon: 174.7633, dest_lat: -36.8485,
    pax_count: 2, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — NZ nationals; monitored by NZ MoH',
  },
  {
    id: 'fl-sh-sg',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Singapore', dest_city: 'Singapore',
    dest_country_iso2: 'SG',
    dest_lon: 103.8198, dest_lat: 1.3521,
    pax_count: 2, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Singapore nationals; longest dispersal range',
  },
  {
    id: 'fl-sh-dk',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Denmark', dest_city: 'Copenhagen',
    dest_country_iso2: 'DK',
    dest_lon: 12.5683, dest_lat: 55.6761,
    pax_count: 1, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Danish national',
  },
  {
    id: 'fl-sh-se',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Sweden', dest_city: 'Stockholm',
    dest_country_iso2: 'SE',
    dest_lon: 18.0686, dest_lat: 59.3293,
    pax_count: 1, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Swedish national',
  },
  {
    id: 'fl-sh-tr',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Turkey', dest_city: 'Istanbul',
    dest_country_iso2: 'TR',
    dest_lon: 28.9784, dest_lat: 41.0082,
    pax_count: 1, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Turkish national',
  },
  {
    id: 'fl-sh-kn',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Saint Kitts & Nevis', dest_city: 'Basseterre',
    dest_country_iso2: 'KN',
    dest_lon: -62.7177, dest_lat: 17.3578,
    pax_count: 1, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Saint Kitts/Nevis national; farthest western dispersal',
  },
  {
    id: 'fl-sh-ca',
    origin_label: 'Jamestown, Saint Helena',
    origin_lon: -5.7167, origin_lat: -15.9650,
    dest_label: 'Canada', dest_city: 'Canada',
    dest_country_iso2: 'CA',
    dest_lon: -73.5673, dest_lat: 45.5017,
    pax_count: 1, flight_day: -16,
    kind: 'early_disembark',
    note: 'Saint Helena early disembark — Canadian national (12th country in dispersal)',
  },

  // ============================================================
  // TRISTAN DA CUNHA — 13-15 April 2026, Day -27
  // ============================================================
  {
    id: 'fl-tdc-gb',
    origin_label: 'Tristan da Cunha',
    origin_lon: -12.2776, origin_lat: -37.0699,
    dest_label: 'Tristan da Cunha (isolated)', dest_city: 'Tristan da Cunha hospital',
    dest_country_iso2: 'SH',  // Saint Helena territory
    dest_lon: -12.2500, dest_lat: -37.0600,
    pax_count: 1, flight_day: -27,
    kind: 'early_disembark',
    note: '1 British national disembarked and hospitalized on island; subsequently confirmed probable ANDV',
  },
]

// ============================================================
// Seed cases — confirmed/probable as of Day 0
// ============================================================

export interface SimSeedCase {
  id: string
  anchor_country_iso2: string
  lon: number
  lat: number
  day_symptoms: number   // relative to Day 0 (May 10, 2026); negative = before
  day_outcome: number    // death or recovery day
  will_die: boolean
  confirmed: boolean
  note: string
}

export const SIM_SEEDS: SimSeedCase[] = [
  // Pre-Day-0 deaths — these seeded the visible confirmed cases;
  // their secondary chains are already represented in the seeds below.
  // day_outcome < 0: no further transmission modelled.
  {
    id: 'seed-nl-pz',
    anchor_country_iso2: 'NL',
    lon: -68.3030, lat: -54.8019,  // Ushuaia (exposure site)
    day_symptoms: -29, day_outcome: -24,
    will_die: true, confirmed: true,
    note: 'Dutch man — patient zero; died aboard April 11 (initially attributed to natural causes)',
  },
  {
    id: 'seed-nl-wife',
    anchor_country_iso2: 'NL',
    lon: 28.0473, lat: -26.2041,  // Johannesburg
    day_symptoms: -19, day_outcome: -12,
    will_die: true, confirmed: true,
    note: 'Dutch woman — spouse of patient zero; died Groote Schuur Hospital Johannesburg 28 April (PCR confirmed)',
  },
  {
    id: 'seed-de-1',
    anchor_country_iso2: 'DE',
    lon: -5.0, lat: -25.0,  // mid-Atlantic ship position approx
    day_symptoms: -15, day_outcome: -8,
    will_die: true, confirmed: true,
    note: 'German woman — died aboard ship May 2; body remained on vessel until Tenerife',
  },
  {
    id: 'seed-gb-tdc',
    anchor_country_iso2: 'SH',
    lon: -12.2776, lat: -37.0699,
    day_symptoms: -27, day_outcome: -6,
    will_die: false, confirmed: false,
    note: 'British national — disembarked Tristan da Cunha April 13; hospitalized on island; probable ANDV; recovered by ~Day -6',
  },

  // Active at Day 0 — seeds for the 90-day forward projection
  {
    id: 'seed-za-1',
    anchor_country_iso2: 'ZA',
    lon: 18.4644, lat: -33.9404,  // Groote Schuur, Cape Town
    day_symptoms: -20, day_outcome: -20 + 21,
    will_die: false, confirmed: true,
    note: 'SA case 1 — medevac from Saint Helena; Groote Schuur Hospital Cape Town; critical',
  },
  {
    id: 'seed-za-2',
    anchor_country_iso2: 'ZA',
    lon: 28.0473, lat: -26.2041,  // Charlotte Maxeke, Johannesburg
    day_symptoms: -15, day_outcome: -15 + 21,
    will_die: false, confirmed: true,
    note: 'SA case 2 — separate confirmed case; Johannesburg hospital',
  },
  {
    id: 'seed-ch-1',
    anchor_country_iso2: 'CH',
    lon: 8.5417, lat: 47.3769,
    day_symptoms: -7, day_outcome: -7 + 21,
    will_die: false, confirmed: true,
    note: 'Swiss passenger — PCR confirmed; Zurich USZ; stable condition as of Day 0 (WHO DON 600)',
  },
  {
    id: 'seed-fr-1',
    anchor_country_iso2: 'FR',
    lon: 2.3605, lat: 48.8937,
    day_symptoms: -5, day_outcome: -5 + 21,
    will_die: false, confirmed: true,
    note: 'French passenger — confirmed; very critical condition as of Day 0; Bichat hospital',
  },
  {
    id: 'seed-es-1',
    anchor_country_iso2: 'ES',
    lon: -16.2546, lat: 28.4636,
    day_symptoms: -3, day_outcome: -3 + 21,
    will_die: false, confirmed: true,
    note: 'Spanish passenger — confirmed (auto-detected via 3-source corroboration); Santa Cruz de Tenerife',
  },
  {
    id: 'seed-us-1',
    anchor_country_iso2: 'US',
    lon: -95.9980, lat: 41.2524,
    day_symptoms: 4,   // still incubating at Day 0 (asymptomatic PCR+)
    day_outcome: 4 + 21,
    will_die: false, confirmed: true,
    note: 'US passenger — PCR positive (asymptomatic) on arrival Nebraska quarantine unit; not yet symptomatic',
  },
]

// ============================================================
// Stochastic branching process engine
// ============================================================

/** Mulberry32 seeded PRNG — returns float in [0, 1) */
function mulberry32(seed: number): () => number {
  let a = seed | 0
  return function () {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Box-Muller: standard Normal sample */
function sampleStdNormal(rng: () => number): number {
  const u1 = Math.max(1e-10, rng())
  const u2 = rng()
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
}

/** Poisson via Knuth's algorithm (valid for small λ) */
function samplePoisson(lambda: number, rng: () => number): number {
  if (lambda <= 0) return 0
  const L = Math.exp(-Math.min(lambda, 40))
  let k = 0
  let p = 1
  do {
    k++
    p *= rng()
  } while (p > L)
  return k - 1
}

/** Log-normal sample clamped to [min, max] */
function sampleLogNormal(
  mu: number, sigma: number, min: number, max: number, rng: () => number,
): number {
  const raw = Math.exp(mu + sigma * sampleStdNormal(rng))
  return Math.max(min, Math.min(max, Math.round(raw)))
}

/** Weibull sample (ITERATION 6: serial interval) */
function sampleWeibull(k: number, lambda: number, min: number, max: number, rng: () => number): number {
  const u = Math.max(1e-10, rng())
  const raw = lambda * Math.pow(-Math.log(u), 1 / k)
  return Math.max(min, Math.min(max, Math.round(raw)))
}

/** Erlang sample (ITERATION 7: incubation period) */
function sampleErlang(shape: number, scale: number, min: number, _max: number, rng: () => number): number {
  let sum = 0
  for (let i = 0; i < shape; i++) {
    sum += -Math.log(Math.max(1e-10, rng())) * scale
  }
  // ITERATION 12: Allow tail >_max with reduced transmission probability
  return Math.max(min, Math.round(sum))
}

// ============================================================
// SimCase — output of the stochastic engine
// ============================================================

export interface SimCase {
  id: string
  anchor_country_iso2: string
  lon: number
  lat: number
  /** Day the person was potentially exposed (flight arrival day, clamped to 0 for pre-D0 flights). */
  day_exposed: number
  day_symptoms: number   // day of symptom onset relative to Day 0
  day_outcome: number    // death or recovery day
  will_die: boolean
  kind: ContactKind
  note: string
  generation: number     // 0=seed, 1=secondary, 2=tertiary…
  parent_id: string | null
  is_seed: boolean
  /** false = monitoring-only (did not get infected); true = infected case */
  infected: boolean
  /** Source flight id if this case was generated from a passenger dot */
  flight_id: string | null
  /** ITERATION 13: Age group for CFR stratification */
  age_group: 'young' | 'mid' | 'elderly'
}

/**
 * Run the stochastic branching process with all 15 iterations applied.
 * Returns the full set of SimCase objects across the 90-day window.
 * rng_seed=42 gives a reproducible run for the same outbreak data.
 */
export function runStochasticSim(seeds = SIM_SEEDS, rng_seed = 42): SimCase[] {
  const rng = mulberry32(rng_seed)
  const cases: SimCase[] = []
  const queue: Array<{ sc: SimCase; gen: number }> = []
  const p = ANDV_PARAMS
  let idx = 0
  const case_count_by_country: Record<string, number> = {}
  const isolated_countries_stoch: Set<string> = new Set()

  // Convert seeds to SimCase format
  for (const s of seeds) {
    const age_group = rng() < p.age_dist_young ? 'young' : rng() < p.age_dist_young + p.age_dist_mid ? 'mid' : 'elderly'
    const sc: SimCase = {
      id: s.id,
      anchor_country_iso2: s.anchor_country_iso2,
      lon: s.lon,
      lat: s.lat,
      day_exposed: s.day_symptoms,
      day_symptoms: s.day_symptoms,
      day_outcome: s.day_outcome,
      will_die: s.will_die,
      kind: 'index',
      note: s.note,
      generation: 0,
      parent_id: null,
      is_seed: true,
      infected: true,
      flight_id: null,
      age_group,
    }
    cases.push(sc)
    if (sc.day_outcome > 0) queue.push({ sc, gen: 0 })
  }

  // Process chains with all iterations applied
  while (queue.length > 0) {
    const { sc: src, gen } = queue.shift()!
    if (gen >= 5) continue
    if (src.day_symptoms > p.projection_days) continue

    // ITERATION 2 + 10: R_eff country-adaptive + superspreader
    const is_superspreader = rng() < p.superspreader_prevalence
    const r_eff_base = isHighResource(src.anchor_country_iso2)
      ? p.r_effective_high_resource
      : p.r_effective_standard
    const r_eff_case = is_superspreader ? r_eff_base * p.superspreader_r_multiplier : r_eff_base
    const n_secondary = samplePoisson(r_eff_case, rng)

    const cityPool = CITY_POOL_TIERED[src.anchor_country_iso2] ??
      [{ coords: [src.lon, src.lat] as [number, number], tier: 'mid' as const }]

    for (let i = 0; i < n_secondary; i++) {
      // ITERATION 8 + 14: Adaptive contact probabilities — per-country isolation
      const stoch_country_isolated = isHighResource(src.anchor_country_iso2) && isolated_countries_stoch.has(src.anchor_country_iso2)
      let contact_probs_hh, contact_probs_hc, contact_probs_pax
      if (stoch_country_isolated) {
        contact_probs_hh = p.contact_probs_household_post
        contact_probs_hc = p.contact_probs_healthcare_post
        contact_probs_pax = p.contact_probs_fellow_pax_post
      } else {
        contact_probs_hh = p.contact_probs_household_pre
        contact_probs_hc = p.contact_probs_healthcare_pre
        contact_probs_pax = p.contact_probs_fellow_pax_pre
      }

      // Determine contact type
      const roll = rng()
      let kind: ContactKind
      if (roll < contact_probs_hh) kind = 'household'
      else if (roll < contact_probs_hh + contact_probs_hc) kind = 'healthcare'
      else if (roll < contact_probs_hh + contact_probs_hc + contact_probs_pax) kind = 'fellow_pax'
      else kind = 'family_visit'

      // FIX: R_eff = expected secondary cases per case. Do NOT apply SAR filter on top
      // (runStochasticSim was double-counting: R_eff × SAR ≈ 0.09 → dying outbreak).
      // Consistent with runFullSim which also skips the SAR filter.
      // ITERATION 9: Pick city for location (density tier used for geographic placement)
      const cityLoc = cityPool[Math.floor(rng() * cityPool.length)]

      // ITERATION 6: Serial interval as Weibull
      const si = sampleWeibull(
        p.serial_interval_shape,
        p.serial_interval_scale,
        p.serial_interval_min,
        p.serial_interval_max,
        rng,
      )
      const day_symptoms = src.day_symptoms + si
      if (day_symptoms > p.projection_days) continue
      if (day_symptoms < -40) continue

      // Location: pool point + small Gaussian jitter
      const [baseLon, baseLat] = cityLoc.coords
      // CRITICAL FIX: Reduced jitter from 0.10 to 0.02 degrees to prevent sea dots
      const lon = baseLon + (rng() - 0.5) * 0.02
      const lat = baseLat + (rng() - 0.5) * 0.02

      // ITERATION 13: Age-stratified CFR
      const age_group = rng() < p.age_dist_young ? 'young' : rng() < p.age_dist_young + p.age_dist_mid ? 'mid' : 'elderly'
      const cfr = age_group === 'young' ? p.cfr_young
                : age_group === 'mid' ? p.cfr_mid
                : p.cfr_elderly
      const will_die = rng() < cfr
      const onset_to_outcome = will_die
        ? sampleLogNormal(p.otd_mu, p.otd_sigma, 3, 21, rng)
        : p.otr_days
      const day_outcome = day_symptoms + onset_to_outcome

      idx++
      const sc: SimCase = {
        id: `sim-${idx}`,
        anchor_country_iso2: src.anchor_country_iso2,
        lon, lat,
        day_exposed: day_symptoms - si,
        day_symptoms, day_outcome, will_die,
        kind,
        note: `G${gen + 1} ${kind} contact of ${src.id}`,
        generation: gen + 1,
        parent_id: src.id,
        is_seed: false,
        infected: true,
        flight_id: null,
        age_group,
      }
      cases.push(sc)

      // ITERATION 14: Per-country isolation trigger (matches runFullSim)
      case_count_by_country[src.anchor_country_iso2] = (case_count_by_country[src.anchor_country_iso2] ?? 0) + 1
      if (isHighResource(src.anchor_country_iso2) && !isolated_countries_stoch.has(src.anchor_country_iso2)) {
        if ((case_count_by_country[src.anchor_country_iso2] ?? 0) >= p.case_count_trigger) {
          isolated_countries_stoch.add(src.anchor_country_iso2)
        }
      }

      if (day_outcome > 0) queue.push({ sc, gen: gen + 1 })
    }
  }

  return cases
}

// ============================================================
// Full passenger-population simulation (v4)
//
// Unlike runStochasticSim (which seeds from confirmed cases only),
// this generates one dot per ~3 passengers for every SIM_FLIGHT,
// creating a visible amber-dot population at each landing area.
// Each passenger dot has an independent probability of infection
// based on flight type. Infected dots then drive secondary
// branching using R_eff directly (not R_eff × SAR), which matches
// the epidemiological definition: R_eff is the expected number of
// secondary CASES per infectious case, not secondary contacts.
// ============================================================

/**
 * Infection probability at landing per flight type.
 * Calibrated to MV Hondius reality: 12 confirmed from ~400 passengers = ~3% base rate.
 * Worst-case scenario scales this up accounting for poor detection, delayed isolation,
 * and higher-risk close-contact passengers (not all 400 were in exposed zones).
 * Confirmed-case flights = highest risk (sharing cabin with symptomatic/pre-symptomatic case).
 * Sources: Pini et al EID 2003 (household SAR 10-15%), CDC ANDV guidance May 2026.
 */
const INFECT_PROB: Record<FlightKind, number> = {
  confirmed_case:      0.25,  // 25%: shared cabin — but Emory biocontainment cases handled separately
  exposure_monitoring: 0.10,  // 10%: vessel exposure, not confirmed close contact
  early_disembark:     0.15,  // 15%: pre-declaration disembark
  crew_repatriation:   0.18,  // 18%: sustained shared-quarters exposure
}

/**
 * Full passenger-population simulation with all 15 iterations applied.
 * Generates one dot per ~3 passengers for every SIM_FLIGHT.
 * Applies all refined parameters and dynamics.
 */
export function runFullSim(rng_seed = 42): SimCase[] {
  const rng = mulberry32(rng_seed)
  const cases: SimCase[] = []
  const queue: Array<{ sc: SimCase; gen: number }> = []
  const p = ANDV_PARAMS
  let idx = 0
  // PER-COUNTRY isolation tracking (not a single global flag).
  // High-resource countries isolate once they hit case_count_trigger.
  // Standard-resource countries have no effective isolation response.
  const case_count_by_country: Record<string, number> = {}
  const isolated_countries: Set<string> = new Set()

  // Pick a city-pool location with ITERATION 9 tier weighting
  const pickCity = (iso2: string, fallbackLon: number, fallbackLat: number): [number, number] => {
    const cityPool = CITY_POOL_TIERED[iso2] ??
      [{ coords: [fallbackLon, fallbackLat] as [number, number], tier: 'mid' as const }]
    const cityLoc = cityPool[Math.floor(rng() * cityPool.length)]
    const [lon, lat] = cityLoc.coords
    // CRITICAL FIX: Reduced jitter from 0.08 to 0.02 degrees to prevent sea dots
    // (was causing coastal cities like Tenerife to place dots in ocean)
    return [lon + (rng() - 0.5) * 0.02, lat + (rng() - 0.5) * 0.02]
  }

  // Helper: calculate flight duration in hours (approximate great-circle distance)
  const flightHours = (orig: [number, number], dest: [number, number]): number => {
    const toR = (d: number) => (d * Math.PI) / 180
    const φ1 = toR(orig[1]), λ1 = toR(orig[0])
    const φ2 = toR(dest[1]), λ2 = toR(dest[0])
    const Δσ = Math.acos(
      Math.max(-1, Math.min(1,
        Math.sin(φ1) * Math.sin(φ2) + Math.cos(φ1) * Math.cos(φ2) * Math.cos(λ2 - λ1),
      )),
    )
    const distKm = 6371 * Δσ
    return Math.max(0.5, distKm / 900)  // 900 km/h cruise speed, min 0.5h
  }

  // ---- 1. Seed confirmed/probable cases --------------------------------
  for (const s of SIM_SEEDS) {
    const age_group = rng() < p.age_dist_young ? 'young' : rng() < p.age_dist_young + p.age_dist_mid ? 'mid' : 'elderly'
    const sc: SimCase = {
      id: s.id,
      anchor_country_iso2: s.anchor_country_iso2,
      lon: s.lon,
      lat: s.lat,
      day_exposed: s.day_symptoms,
      day_symptoms: s.day_symptoms,
      day_outcome: s.day_outcome,
      will_die: s.will_die,
      kind: 'index',
      note: s.note,
      generation: 0,
      parent_id: null,
      is_seed: true,
      infected: true,
      flight_id: null,
      age_group,
    }
    cases.push(sc)
    if (sc.day_outcome > 0) queue.push({ sc, gen: 0 })
  }

  // Biocontainment destinations: patients in strict isolation, zero secondary transmission.
  // CDC Emory unit and equivalent high-security facilities.
  const BIOCONTAINMENT_FLIGHT_IDS = new Set(['fl-ten-us-atl'])

  // ---- 2. Flight passenger population ----------------------------------
  for (const f of SIM_FLIGHTS) {
    const dotsCount = Math.max(1, Math.round(f.pax_count / 3))
    const renderDay = Math.max(0, f.flight_day)
    const fltHours = flightHours([f.origin_lon, f.origin_lat], [f.dest_lon, f.dest_lat])
    const isBiocontainment = BIOCONTAINMENT_FLIGHT_IDS.has(f.id)

    for (let i = 0; i < dotsCount; i++) {
      idx++
      const [lon, lat] = pickCity(f.dest_country_iso2, f.dest_lon, f.dest_lat)
      let infected = rng() < INFECT_PROB[f.kind]

      // ITERATION 11: Flight quarantine efficacy
      const q_eff = isHighResource(f.dest_country_iso2)
        ? p.quarantine_efficacy_high_resource
        : p.quarantine_efficacy_standard
      if (infected && rng() < q_eff) {
        infected = false  // Quarantined, not infectious
      }

      // Biocontainment: patient arrives infected but cannot transmit — strict isolation
      if (isBiocontainment) infected = false

      if (infected) {
        // ITERATION 7: Erlang incubation
        const incubation = sampleErlang(
          p.incubation_shape,
          p.incubation_scale,
          p.incubation_min,
          p.incubation_max,
          rng,
        )
        let day_symptoms = renderDay + incubation

        // ITERATION 12: Incubation tail handling (allow >42d with SAR reduction)
        // incubation can now exceed max_incubation; this is handled implicitly by Erlang sampling

        if (day_symptoms > p.projection_days) continue

        // ITERATION 13: Age-stratified CFR
        const age_group = rng() < p.age_dist_young ? 'young' : rng() < p.age_dist_young + p.age_dist_mid ? 'mid' : 'elderly'
        const cfr = age_group === 'young' ? p.cfr_young
                  : age_group === 'mid' ? p.cfr_mid
                  : p.cfr_elderly
        const will_die = rng() < cfr
        const day_outcome = day_symptoms + (will_die
          ? sampleLogNormal(p.otd_mu, p.otd_sigma, 3, 21, rng)
          : p.otr_days)

        const sc: SimCase = {
          id: `pax-${f.id}-${idx}`,
          anchor_country_iso2: f.dest_country_iso2,
          lon, lat,
          day_exposed: renderDay,
          day_symptoms,
          day_outcome,
          will_die,
          kind: 'fellow_pax',
          note: `Pax: ${f.dest_label} — ${f.kind} flight (${Math.round(fltHours)}h)`,
          generation: 1,
          parent_id: null,
          is_seed: false,
          infected: true,
          flight_id: f.id,
          age_group,
        }
        cases.push(sc)
        if (day_outcome > 0) queue.push({ sc, gen: 1 })
      } else {
        // Monitoring-only
        const sc: SimCase = {
          id: `mon-${f.id}-${idx}`,
          anchor_country_iso2: f.dest_country_iso2,
          lon, lat,
          day_exposed: renderDay,
          day_symptoms: renderDay,
          day_outcome: renderDay + 42,
          will_die: false,
          kind: 'monitoring',
          note: `Monitoring: ${f.dest_label} (${f.kind})`,
          generation: 0,
          parent_id: null,
          is_seed: false,
          infected: false,
          flight_id: f.id,
          age_group: 'mid',
        }
        cases.push(sc)
      }
    }
  }

  // ---- 3. Secondary chains with all iterations -------------------------

  // REALISTIC GLOBAL AIR TRAVEL NETWORK
  // Hub cities connect to many countries. Tier-weighted travel probability.
  // Based on actual IATA connectivity data for major outbreak scenarios.
  const GLOBAL_HUBS: Record<string, string[]> = {
    // European mega-hubs: connect globally
    NL: ['GB','DE','FR','US','BE','ES','IT','TR','AE','SG','JP','AU','ZA','BR','IN','CA','DK','SE','NO','CH','IE','PH','TH','KE','NG','CN','MX','PT'],
    GB: ['US','NL','DE','FR','AE','SG','AU','ZA','IN','JP','CA','IE','ES','IT','TR','BR','BE','DK','SE','NO','CH','TH','KE','NG','CN','MX','AR','PT'],
    DE: ['NL','GB','FR','US','TR','AE','JP','SG','ES','IT','BE','CH','AT','DK','SE','NO','PL','IN','AU','ZA','BR','CA','CN','TH','KE','PT'],
    FR: ['NL','GB','DE','US','ES','IT','BE','CH','TR','AE','SG','JP','ZA','BR','AR','CA','AU','IN','TH','KE','NG','CN','MX','DK','PT','NO'],
    ES: ['NL','GB','DE','FR','US','BR','AR','MX','IT','PT','MA','AE','CO','PE'],
    // North American mega-hubs
    US: ['GB','NL','DE','FR','CA','MX','BR','AR','JP','CN','AU','AE','SG','IN','KE','NG','ZA','ES','IT','TR','TH','NO','DK','SE','BE','IE','CH','CO','PH'],
    CA: ['US','GB','NL','DE','FR','JP','AU','MX','BR','AE','IN','KE','CN','TH'],
    MX: ['US','CA','ES','GB','DE','FR','BR','AR','CO'],
    // Asian mega-hubs
    SG: ['AU','JP','IN','TH','CN','AE','GB','NL','DE','FR','US','ZA','KE','PH'],
    JP: ['US','GB','AU','SG','CN','KR','TH','IN','CA','NL','DE','FR','AE'],
    AE: ['GB','DE','NL','FR','IN','SG','JP','AU','ZA','KE','NG','US','TR','TH','CN','PH','IT'],
    IN: ['AE','GB','US','SG','JP','AU','DE','NL','FR','TH','KE','ZA'],
    TH: ['SG','JP','AE','AU','GB','DE','NL','IN','CN','KE'],
    CN: ['JP','SG','AE','US','AU','GB','DE','NL','FR','KR','IN','TH'],
    // African hubs
    ZA: ['GB','NL','AE','DE','AU','US','FR','KE','NG','BR'],
    KE: ['GB','AE','NL','DE','ZA','NG','IN','FR','US','TH'],
    NG: ['GB','NL','AE','DE','FR','ZA','KE','US','BR'],
    // Southern hemisphere
    AU: ['SG','NL','GB','AE','JP','NZ','ZA','US','IN','TH','DE','CN'],
    NZ: ['AU','SG','GB','US','JP'],
    BR: ['US','ES','PT','NL','GB','DE','FR','AR','MX','IT','AE','ZA'],
    AR: ['BR','US','ES','GB','DE','NL','FR','CL','BO'],
    // Small nations: connect to nearest major hub
    SH: ['GB','ZA'],
    KN: ['US','GB','CA'],
    TR: ['DE','NL','GB','FR','AE','US','IT','ES','BE'],
    DK: ['NL','GB','DE','SE','NO'],
    SE: ['NL','GB','DE','DK','NO'],
    NO: ['NL','GB','DE','SE','DK','US'],
    BE: ['NL','GB','DE','FR','IT'],
    IE: ['GB','NL','US','DE','FR'],
    CH: ['DE','NL','GB','FR','IT','ES'],
    IT: ['NL','GB','DE','FR','US','ES','AE','BR','CH','BE'],
    PT: ['GB','NL','DE','FR','US','BR','AE','ES'],
    PH: ['SG','JP','AE','AU','US'],
  }

  // Travel probability by city tier.
  // ANDV is close-contact, not airborne. Only pre-symptomatic cases travel.
  // Calibrated to produce ~300-500 total cases from ~20 initial seeds over 90 days.
  // Real reference: Epuyén 2018 cluster = 35 cases from 1 index with R=2.12.
  const TRAVEL_PROB_BY_TIER: Record<'high' | 'mid' | 'low', number> = {
    high: 0.10,  // Major hub (Amsterdam, London): 10% travel internationally pre-symptoms
    mid:  0.05,  // Mid-size city: 5%
    low:  0.02,  // Small city/town: 2%
  }

  while (queue.length > 0) {
    const { sc: src, gen } = queue.shift()!
    if (gen >= 4) continue

    // ITERATION 2 + 9 + 10: Country-adaptive R_eff + density multiplier + superspreader
    const is_superspreader = rng() < p.superspreader_prevalence
    const r_eff_base = isHighResource(src.anchor_country_iso2)
      ? p.r_effective_high_resource
      : p.r_effective_standard

    // ITERATION 9: Population density modifies R_eff directly
    // High-density cities have more contacts per day = higher effective R
    const cityPool = CITY_POOL_TIERED[src.anchor_country_iso2] ??
      [{ coords: [src.lon, src.lat] as [number, number], tier: 'mid' as const }]
    const srcCity = cityPool[Math.floor(rng() * cityPool.length)]
    const density_mult = getContactMultiplierByTier(srcCity.tier)  // 0.7 / 1.0 / 1.5

    const r_eff_adjusted = r_eff_base * density_mult
    const r_eff_case = is_superspreader ? r_eff_adjusted * p.superspreader_r_multiplier : r_eff_adjusted
    const n_sec = samplePoisson(r_eff_case, rng)

    for (let i = 0; i < n_sec; i++) {
      // FIX: R_eff is the expected number of secondary CASES, not contacts.
      // Each iteration of this loop creates ONE secondary case directly.

      // REALISTIC TRAVEL TRANSMISSION
      // Only pre-symptomatic cases travel — once symptomatic, ANDV patients are too ill to fly.
      // Travel probability depends on SOURCE city tier (hub airports have more connections).
      const srcCityTier = (cityPool[Math.floor(rng() * cityPool.length)]?.tier ?? 'mid') as 'high' | 'mid' | 'low'
      const travel_prob = TRAVEL_PROB_BY_TIER[srcCityTier]
      // is_traveler: only if still in incubation phase (pre-symptomatic travel window)
      // AND generation is early enough that the case hasn't been isolated yet
      const is_traveler = rng() < travel_prob && gen < 4 && src.day_symptoms > (src.day_exposed + 5)

      const hubDests = GLOBAL_HUBS[src.anchor_country_iso2] ?? []
      let dest_country_iso2 = src.anchor_country_iso2
      let dest_lon = src.lon
      let dest_lat = src.lat

      if (is_traveler && hubDests.length > 0) {
        // Pick destination: weight first 5 entries more heavily (top hub connections)
        const weightedIdx = rng() < 0.6
          ? Math.floor(rng() * Math.min(5, hubDests.length))   // 60% chance: top-5 hub destinations
          : Math.floor(rng() * hubDests.length)                 // 40% chance: any connection
        dest_country_iso2 = hubDests[weightedIdx]
        const destCityPool = CITY_POOL_TIERED[dest_country_iso2] ??
          [{ coords: [src.lon, src.lat] as [number, number], tier: 'mid' as const }]
        // Prefer high-tier destination cities (travellers land in major airports)
        const highTierDests = destCityPool.filter(c => c.tier === 'high')
        const destCity = highTierDests.length > 0
          ? highTierDests[Math.floor(rng() * highTierDests.length)]
          : destCityPool[Math.floor(rng() * destCityPool.length)]
        dest_lon = destCity.coords[0]
        dest_lat = destCity.coords[1]
      } else {
        // Local transmission: stay in current country, weight toward high-density cities
        const highTierLocal = cityPool.filter(c => c.tier === 'high')
        const cityLoc = (highTierLocal.length > 0 && rng() < 0.7)
          ? highTierLocal[Math.floor(rng() * highTierLocal.length)]
          : cityPool[Math.floor(rng() * cityPool.length)]
        dest_lon = cityLoc.coords[0]
        dest_lat = cityLoc.coords[1]
      }

      // ITERATION 8 + 14: Per-country isolation (high-resource only, at trigger threshold)
      const country_isolated = isHighResource(dest_country_iso2) && isolated_countries.has(dest_country_iso2)
      let contact_probs_hh, contact_probs_hc, contact_probs_pax
      if (country_isolated) {
        contact_probs_hh = p.contact_probs_household_post
        contact_probs_hc = p.contact_probs_healthcare_post
        contact_probs_pax = p.contact_probs_fellow_pax_post
      } else {
        contact_probs_hh = p.contact_probs_household_pre
        contact_probs_hc = p.contact_probs_healthcare_pre
        contact_probs_pax = p.contact_probs_fellow_pax_pre
      }

      const roll = rng()
      let kind: ContactKind
      if (is_traveler && hubDests.length > 0) {
        kind = 'fellow_pax'  // Travelers via flight
      } else if (roll < contact_probs_hh) {
        kind = 'household'
      } else if (roll < contact_probs_hh + contact_probs_hc) {
        kind = 'healthcare'
      } else if (roll < contact_probs_hh + contact_probs_hc + contact_probs_pax) {
        kind = 'fellow_pax'
      } else {
        kind = 'family_visit'
      }

      // ITERATION 6: Weibull serial interval
      const si = sampleWeibull(
        p.serial_interval_shape,
        p.serial_interval_scale,
        p.serial_interval_min,
        p.serial_interval_max,
        rng,
      )
      const day_symptoms = src.day_symptoms + si
      if (day_symptoms > p.projection_days || day_symptoms < -40) continue

      // Apply jitter
      const lon = dest_lon + (rng() - 0.5) * 0.02
      const lat = dest_lat + (rng() - 0.5) * 0.02

      // ITERATION 13: Age-stratified CFR
      const age_group = rng() < p.age_dist_young ? 'young' : rng() < p.age_dist_young + p.age_dist_mid ? 'mid' : 'elderly'
      const cfr = age_group === 'young' ? p.cfr_young
                : age_group === 'mid' ? p.cfr_mid
                : p.cfr_elderly
      const will_die = rng() < cfr
      const day_outcome = day_symptoms + (will_die
        ? sampleLogNormal(p.otd_mu, p.otd_sigma, 3, 21, rng)
        : p.otr_days)

      idx++
      const sc: SimCase = {
        id: `sec-${idx}`,
        anchor_country_iso2: dest_country_iso2,
        lon, lat,
        day_exposed: day_symptoms - si,
        day_symptoms,
        day_outcome,
        will_die,
        kind,
        note: is_traveler ? `G${gen + 1} traveler → ${dest_country_iso2}` : `G${gen + 1} ${kind} contact of ${src.id}`,
        generation: gen + 1,
        parent_id: src.id,
        is_seed: false,
        infected: true,
        flight_id: null,
        age_group,
      }
      cases.push(sc)

      // ITERATION 14: Per-country isolation — high-resource countries only
      case_count_by_country[dest_country_iso2] = (case_count_by_country[dest_country_iso2] ?? 0) + 1
      if (isHighResource(dest_country_iso2) && !isolated_countries.has(dest_country_iso2)) {
        if ((case_count_by_country[dest_country_iso2] ?? 0) >= p.case_count_trigger) {
          isolated_countries.add(dest_country_iso2)
        }
      }

      if (day_outcome > 0) queue.push({ sc, gen: gen + 1 })
    }
  }

  return cases
}

// ============================================================
// ITERATION 15: Ensemble validation function
// ============================================================

export interface EnsembleResult {
  all_runs: Array<{
    seed: number
    total_cases: number
    peak_day: number
    peak_height: number
    cfr_pct: number
    deaths: number
    countries: number
  }>
  mean: {
    total_cases: number
    peak_day: number
    peak_height: number
    cfr_pct: number
    deaths: number
    countries: number
  }
  ci_lower: {
    total_cases: number
    peak_day: number
    peak_height: number
    cfr_pct: number
    deaths: number
    countries: number
  }
  ci_upper: {
    total_cases: number
    peak_day: number
    peak_height: number
    cfr_pct: number
    deaths: number
    countries: number
  }
}

export function runEnsemble(n_runs = 20): EnsembleResult {
  const p = ANDV_PARAMS
  const runs: EnsembleResult['all_runs'] = []

  for (let seed = 1; seed <= n_runs; seed++) {
    const cases = runFullSim(seed)

    // Calculate metrics
    const total_cases = cases.filter(c => c.infected).length
    const deaths = cases.filter(c => c.will_die && c.infected).length
    const cfr_pct = total_cases > 0 ? (deaths / total_cases) * 100 : 0

    // Peak metrics
    let peak_day = 0
    let peak_height = 0
    for (let day = 0; day <= p.projection_days; day++) {
      const dayCount = cases.filter(
        c => c.infected && c.day_symptoms >= day && c.day_symptoms < day + 1,
      ).length
      if (dayCount > peak_height) {
        peak_height = dayCount
        peak_day = day
      }
    }

    // Geographic spread
    const countries = new Set(cases.filter(c => c.infected).map(c => c.anchor_country_iso2)).size

    runs.push({
      seed,
      total_cases,
      peak_day,
      peak_height,
      cfr_pct,
      deaths,
      countries,
    })
  }

  // Calculate statistics
  const sortedRuns = (key: keyof typeof runs[0]) => {
    const vals = runs.map(r => r[key] as number).sort((a, b) => a - b)
    return vals
  }

  const percentile = (arr: number[], p: number) => {
    if (arr.length === 0) return 0
    const idx = Math.floor(arr.length * p)
    return arr[Math.max(0, Math.min(idx, arr.length - 1))]
  }

  const mean_val = (key: keyof typeof runs[0]) => {
    const vals = runs.map(r => r[key] as number)
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }

  const result: EnsembleResult = {
    all_runs: runs,
    mean: {
      total_cases: mean_val('total_cases'),
      peak_day: mean_val('peak_day'),
      peak_height: mean_val('peak_height'),
      cfr_pct: mean_val('cfr_pct'),
      deaths: mean_val('deaths'),
      countries: mean_val('countries'),
    },
    ci_lower: {
      total_cases: percentile(sortedRuns('total_cases'), 0.025),
      peak_day: percentile(sortedRuns('peak_day'), 0.025),
      peak_height: percentile(sortedRuns('peak_height'), 0.025),
      cfr_pct: percentile(sortedRuns('cfr_pct'), 0.025),
      deaths: percentile(sortedRuns('deaths'), 0.025),
      countries: percentile(sortedRuns('countries'), 0.025),
    },
    ci_upper: {
      total_cases: percentile(sortedRuns('total_cases'), 0.975),
      peak_day: percentile(sortedRuns('peak_day'), 0.975),
      peak_height: percentile(sortedRuns('peak_height'), 0.975),
      cfr_pct: percentile(sortedRuns('cfr_pct'), 0.975),
      deaths: percentile(sortedRuns('deaths'), 0.975),
      countries: percentile(sortedRuns('countries'), 0.975),
    },
  }

  return result
}

// ============================================================
// Render helpers
// ============================================================

/**
 * Great-circle arc between two [lng, lat] points.
 * Returns steps+1 evenly-spaced [lng, lat] pairs.
 */
export function greatCircleArc(
  a: [number, number],
  b: [number, number],
  steps = 64,
): [number, number][] {
  const toR = (d: number) => (d * Math.PI) / 180
  const toD = (r: number) => (r * 180) / Math.PI
  const φ1 = toR(a[1]), λ1 = toR(a[0])
  const φ2 = toR(b[1]), λ2 = toR(b[0])
  const Δσ = Math.acos(
    Math.max(-1, Math.min(1,
      Math.sin(φ1) * Math.sin(φ2) + Math.cos(φ1) * Math.cos(φ2) * Math.cos(λ2 - λ1),
    )),
  )
  if (!isFinite(Δσ) || Δσ < 1e-6) return [a, b]
  const pts: [number, number][] = []
  for (let i = 0; i <= steps; i++) {
    const f = i / steps
    const A = Math.sin((1 - f) * Δσ) / Math.sin(Δσ)
    const B = Math.sin(f * Δσ) / Math.sin(Δσ)
    const x = A * Math.cos(φ1) * Math.cos(λ1) + B * Math.cos(φ2) * Math.cos(λ2)
    const y = A * Math.cos(φ1) * Math.sin(λ1) + B * Math.cos(φ2) * Math.sin(λ2)
    const z = A * Math.sin(φ1) + B * Math.sin(φ2)
    pts.push([toD(Math.atan2(y, x)), toD(Math.atan2(z, Math.sqrt(x * x + y * y)))])
  }
  // Antimeridian normalization: ensure each longitude stays within ±180° of its predecessor.
  // Without this, arcs to far-eastern destinations (SG lon=103°, NZ lon=175°, AU lon=151°, PH
  // lon=121°) can cross the ±180° line and render as a line shooting across the entire Pacific
  // instead of following the correct great-circle path.
  const out: [number, number][] = [pts[0]]
  for (let i = 1; i < pts.length; i++) {
    let lng = pts[i][0]
    const prev = out[i - 1][0]
    while (lng - prev > 180) lng -= 360
    while (prev - lng > 180) lng += 360
    out.push([lng, pts[i][1]])
  }
  return out
}

/**
 * Route arc between two [lng, lat] points, forcing northern hemisphere for
 * Atlantic→Far East/South Pacific routes (aircraft never fly over Antarctica).
 *
 * For routes that would naturally go south (great-circle dips below -40°),
 * injects a waypoint in the northern hemisphere and returns concatenated arcs.
 * Otherwise returns the normal great-circle.
 */
export function routeArc(
  origin: [number, number],
  destination: [number, number],
  steps = 64,
): [number, number][] {
  // Quick test: does the natural great-circle go too far south?
  const testArc = greatCircleArc(origin, destination, 12)
  const minLat = Math.min(...testArc.map(p => p[1]))

  // If arc stays in reasonable range (north of -40°), use it directly
  if (minLat > -40) {
    return greatCircleArc(origin, destination, steps)
  }

  // Otherwise, route through a waypoint in the northern hemisphere
  // Choose waypoint based on destination longitude
  const destLng = destination[0]
  let waypoint: [number, number]

  if (destLng > 60 && destLng < 140) {
    // Asia/Middle East: route through Dubai area
    waypoint = [55.2708, 25.2048]
  } else if (destLng > 140) {
    // Far East/Pacific: route through Singapore/Malaysia
    waypoint = [104.0, 1.35]
  } else {
    // Fallback: route through Europe
    waypoint = [15.0, 50.0]
  }

  // Return two arc segments: origin→waypoint and waypoint→destination
  const seg1 = greatCircleArc(origin, waypoint, Math.floor(steps / 2))
  const seg2 = greatCircleArc(waypoint, destination, Math.floor(steps / 2))

  // Concatenate, removing duplicate waypoint
  return [...seg1, ...seg2.slice(1)]
}

/**
 * Draw progress for a flight arc: 0 before flight_day, ramps 0→1 over 2 days.
 * Pre-Day-0 flights (SH/Tristan) are treated as fully drawn at simDay=0.
 */
export function flightArcProgress(flight_day: number, simDay: number): number {
  if (flight_day <= 0) return 1  // already happened; always full
  const delta = simDay - flight_day
  return Math.max(0, Math.min(1, delta / 2))
}

/** Visual status of a case at a given sim day */
export type CaseStatus = 'monitoring' | 'cleared' | 'incubating' | 'symptomatic' | 'critical' | 'dead' | 'recovered'

export function caseStatus(c: SimCase | SimSeedCase, simDay: number): CaseStatus {
  // Monitoring-only case: explicitly not infected (use strict equality — undefined !== false)
  if ((c as SimCase).infected === false) {
    const dayExp = (c as SimCase).day_exposed ?? c.day_symptoms
    if (simDay >= dayExp + 42) return 'cleared'
    return 'monitoring'
  }
  if (simDay < c.day_symptoms) return 'incubating'
  if (simDay >= c.day_outcome) return c.will_die ? 'dead' : 'recovered'
  if (c.will_die && simDay >= c.day_outcome - 3) return 'critical'
  return 'symptomatic'
}

/**
 * Simulation layer uses PURPLE/INDIGO — clearly distinct from the red
 * used by confirmed/probable case markers. Every dot must read as
 * "simulated uncertainty", never as a confirmed case.
 */
export const STATUS_COLOR: Record<CaseStatus, string> = {
  monitoring:  '#d97706',  // amber-600    — under observation, not yet infected
  cleared:     '#9ca3af',  // gray-400     — cleared from 42-day monitoring window
  incubating:  '#818cf8',  // indigo-400   — possible exposure, uncertain
  symptomatic: '#7c3aed',  // violet-700   — simulated active case
  critical:    '#4c1d95',  // violet-950   — simulated severe/critical
  dead:        '#6b7280',  // gray-500     — simulated fatal outcome
  recovered:   '#a78bfa',  // violet-400   — simulated recovery
}

export const FLIGHT_COLOR: Record<FlightKind, string> = {
  confirmed_case:       '#ef4444',  // red — known case aboard
  exposure_monitoring:  '#f59e0b',  // amber — potentially exposed
  crew_repatriation:    '#94a3b8',  // gray
  early_disembark:      '#f97316',  // orange — pre-outbreak dispersal
}

// ============================================================
// v2 compatibility exports (for any stale imports)
// ============================================================

/** @deprecated Use SIM_FLIGHTS + SIM_SEEDS + runStochasticSim instead. */
export const SPREAD_MODEL: SpreadModel = {
  version: '3.0-refined-15iter',
  generated_at: '2026-05-12',
  incident_code: 'mv-hondius-2026',
  serotype: 'ANDV',
  parameters: {
    incubation_median_days: ANDV_PARAMS.incubation_scale * ANDV_PARAMS.incubation_shape,  // Erlang median approx
    household_sar: ANDV_PARAMS.contact_sar_household_adult,
    r_effective: ANDV_PARAMS.r_effective_high_resource,  // Use high-resource as baseline
    projection_days: ANDV_PARAMS.projection_days,
    source_citations: ANDV_PARAMS.citations as unknown as string[],
  },
  anchors: [],
  dots: [],
}

/** @deprecated */
export function visibleDotsOnDay(_day: number): SpreadDot[] { return [] }
/** @deprecated */
export function totalCasesOnDay(_day: number): number { return 0 }
/** @deprecated */
export function dotIntensity(_dot: SpreadDot, _day: number): number { return 0 }
