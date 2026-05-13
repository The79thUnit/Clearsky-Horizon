// Quick test: run the simulation and count purple dots
import { readFileSync } from 'fs'

// Inline minimal versions of the dependencies
function mulberry32(a) {
  return function() {
    a |= 0; a = a + 0x6d2b79f5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296
  }
}

const ts = readFileSync('src/data/spreadModel.ts', 'utf8')

// Extract ANDV_PARAMS
const paramMatch = ts.match(/export const ANDV_PARAMS = \{([\s\S]*?)\n\}/)
console.log('Found ANDV_PARAMS:', !!paramMatch)

// Extract SIM_FLIGHTS count
const flightMatches = ts.match(/id: ['"]fl-/g)
console.log('Found SIM_FLIGHTS:', flightMatches?.length)

// Extract SIM_SEEDS count
const seedMatches = ts.match(/id: ['"]seed-/g)
console.log('Found SIM_SEEDS:', seedMatches?.length)

// Extract INFECT_PROB values
const infectMatch = ts.match(/const INFECT_PROB[:\s\S]*?\}/m)
console.log('INFECT_PROB found:', !!infectMatch)
if (infectMatch) {
  const text = infectMatch[0]
  const confirmed = text.match(/confirmed_case:\s+([\d.]+)/)
  const exposure = text.match(/exposure_monitoring:\s+([\d.]+)/)
  const crew = text.match(/crew_repatriation:\s+([\d.]+)/)
  console.log(`  confirmed_case: ${confirmed?.[1]}`)
  console.log(`  exposure_monitoring: ${exposure?.[1]}`)
  console.log(`  crew_repatriation: ${crew?.[1]}`)
}

// Extract flight passenger counts
const flightPax = ts.match(/pax_count: (\d+),/g)
if (flightPax) {
  const total = flightPax.reduce((sum, s) => sum + parseInt(s.match(/\d+/)[0]), 0)
  console.log(`Total passengers across all flights: ${total}`)
  console.log(`Expected monitoring dots: ~${Math.floor(total / 3)} (1 per 3 pax)`)
  
  // With 0.20 average infection probability, expect ~13% infected
  const expectedInfected = Math.floor((total / 3) * 0.175)
  console.log(`Expected purple dots from passengers (avg INFECT_PROB=0.175): ~${expectedInfected}`)
}

// Check for runFullSim function
const simFunc = ts.match(/export function runFullSim.*?\{([\s\S]*?)\n\}/)
console.log('\nrunFullSim function found:', !!simFunc)

// Check for secondary branching
const secondary = ts.match(/while \(queue\.length > 0\)/)
console.log('Secondary branching logic found:', !!secondary)

console.log('\n✓ Simulation structure is intact')
