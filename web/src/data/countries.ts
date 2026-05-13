/**
 * Country lookup table: ISO2 -> { name, flag emoji, centroid lat/lng }.
 *
 * Coverage matches the worker's ProMED RSS country map (Phase 1) so every
 * record that gets a country_iso2 also gets a flag + name + map pin.
 *
 * Centroids are approximate (used only for map marker placement, not analysis).
 */

export interface CountryInfo {
  name: string
  flag: string
  lat: number
  lng: number
}

export const COUNTRIES: Record<string, CountryInfo> = {
  AR: { name: 'Argentina', flag: '🇦🇷', lat: -34.0, lng: -64.0 },
  US: { name: 'United States', flag: '🇺🇸', lat: 39.5, lng: -98.35 },
  CL: { name: 'Chile', flag: '🇨🇱', lat: -35.7, lng: -71.5 },
  FI: { name: 'Finland', flag: '🇫🇮', lat: 64.5, lng: 26.0 },
  BR: { name: 'Brazil', flag: '🇧🇷', lat: -14.2, lng: -51.9 },
  UY: { name: 'Uruguay', flag: '🇺🇾', lat: -32.5, lng: -55.8 },
  PY: { name: 'Paraguay', flag: '🇵🇾', lat: -23.4, lng: -58.4 },
  BO: { name: 'Bolivia', flag: '🇧🇴', lat: -16.3, lng: -63.6 },
  PE: { name: 'Peru', flag: '🇵🇪', lat: -9.2, lng: -75.0 },
  EC: { name: 'Ecuador', flag: '🇪🇨', lat: -1.8, lng: -78.2 },
  PA: { name: 'Panama', flag: '🇵🇦', lat: 8.5, lng: -80.8 },
  CO: { name: 'Colombia', flag: '🇨🇴', lat: 4.6, lng: -74.3 },
  VE: { name: 'Venezuela', flag: '🇻🇪', lat: 6.4, lng: -66.6 },
  CA: { name: 'Canada', flag: '🇨🇦', lat: 56.1, lng: -106.3 },
  MX: { name: 'Mexico', flag: '🇲🇽', lat: 23.6, lng: -102.5 },
  DE: { name: 'Germany', flag: '🇩🇪', lat: 51.2, lng: 10.5 },
  SE: { name: 'Sweden', flag: '🇸🇪', lat: 60.1, lng: 18.6 },
  NO: { name: 'Norway', flag: '🇳🇴', lat: 60.5, lng: 8.5 },
  DK: { name: 'Denmark', flag: '🇩🇰', lat: 56.3, lng: 9.5 },
  IS: { name: 'Iceland', flag: '🇮🇸', lat: 64.96, lng: -19.0 },
  FR: { name: 'France', flag: '🇫🇷', lat: 46.2, lng: 2.2 },
  ES: { name: 'Spain', flag: '🇪🇸', lat: 40.5, lng: -3.7 },
  IT: { name: 'Italy', flag: '🇮🇹', lat: 41.9, lng: 12.6 },
  RU: { name: 'Russia', flag: '🇷🇺', lat: 61.5, lng: 105.3 },
  CN: { name: 'China', flag: '🇨🇳', lat: 35.9, lng: 104.2 },
  KR: { name: 'South Korea', flag: '🇰🇷', lat: 35.9, lng: 127.8 },
  JP: { name: 'Japan', flag: '🇯🇵', lat: 36.2, lng: 138.3 },
  GB: { name: 'United Kingdom', flag: '🇬🇧', lat: 55.4, lng: -3.4 },
  NL: { name: 'Netherlands', flag: '🇳🇱', lat: 52.1, lng: 5.3 },
  BE: { name: 'Belgium', flag: '🇧🇪', lat: 50.5, lng: 4.5 },
  IE: { name: 'Ireland', flag: '🇮🇪', lat: 53.4, lng: -8.2 },
  AT: { name: 'Austria', flag: '🇦🇹', lat: 47.5, lng: 14.6 },
  CH: { name: 'Switzerland', flag: '🇨🇭', lat: 46.8, lng: 8.2 },
  PL: { name: 'Poland', flag: '🇵🇱', lat: 51.9, lng: 19.1 },
  CZ: { name: 'Czech Republic', flag: '🇨🇿', lat: 49.8, lng: 15.5 },
  SK: { name: 'Slovakia', flag: '🇸🇰', lat: 48.7, lng: 19.7 },
  SI: { name: 'Slovenia', flag: '🇸🇮', lat: 46.2, lng: 14.9 },
  HR: { name: 'Croatia', flag: '🇭🇷', lat: 45.1, lng: 15.2 },
  RS: { name: 'Serbia', flag: '🇷🇸', lat: 44.0, lng: 21.0 },
  BA: { name: 'Bosnia and Herzegovina', flag: '🇧🇦', lat: 43.9, lng: 17.7 },
  ME: { name: 'Montenegro', flag: '🇲🇪', lat: 42.7, lng: 19.4 },
  GR: { name: 'Greece', flag: '🇬🇷', lat: 39.1, lng: 21.8 },
  TR: { name: 'Turkey', flag: '🇹🇷', lat: 39.0, lng: 35.2 },
}

export function getCountryName(iso2: string | null | undefined): string {
  if (!iso2) return 'Unknown'
  return COUNTRIES[iso2.toUpperCase()]?.name ?? iso2
}

export function getCountryFlag(iso2: string | null | undefined): string {
  if (!iso2) return ''
  return COUNTRIES[iso2.toUpperCase()]?.flag ?? ''
}
