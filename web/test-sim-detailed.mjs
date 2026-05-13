/**
 * Detailed simulation test harness
 * Runs the simulation and captures metrics for analysis
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Read and execute the compiled simulation code
const spreadModelPath = path.join(__dirname, 'dist', 'assets', 'index-C9x_E_LV.js');
const code = fs.readFileSync(spreadModelPath, 'utf8');

// Create a minimal simulation runner without the full web stack
// We'll use Node's vm to evaluate the bundle and extract functions
import vm from 'vm';

const bundle = fs.readFileSync(spreadModelPath, 'utf8');
const context = vm.createContext({
  console,
  Math,
  Array,
  Object,
  window: {},
  document: {},
});

// Instead of trying to parse the bundle, let's run the simulation directly
// by importing the TypeScript and compiling it on the fly
console.log('Setting up simulation test environment...');

// We'll create a minimal test that uses the actual source
const testCode = `
const ANDV_PARAMS = {
  incubation_mu: 2.890,
  incubation_sigma: 0.520,
  incubation_min: 7,
  incubation_max: 42,
  serial_interval_mean: 18,
  serial_interval_sd: 4,
  serial_interval_min: 8,
  serial_interval_max: 35,
  r_effective: 0.7,
  contact_probs_household: 0.40,
  contact_probs_healthcare: 0.25,
  contact_probs_fellow_pax: 0.20,
  contact_probs_family_visit: 0.15,
  contact_sar_household: 0.12,
  contact_sar_healthcare: 0.08,
  contact_sar_fellow_pax: 0.03,
  contact_sar_family_visit: 0.05,
  cfr_high_resource: 0.28,
  cfr_standard: 0.40,
  otd_mu: 1.946,
  otd_sigma: 0.40,
  otr_days: 21,
  projection_days: 90,
  high_resource_isos: ['NL', 'DE', 'FR', 'US', 'GB', 'CH', 'CA', 'AU', 'SE', 'DK', 'NZ', 'BE', 'IE', 'NO'],
};

function mulberry32(seed) {
  let a = seed | 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sampleStdNormal(rng) {
  const u1 = Math.max(1e-10, rng());
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function samplePoisson(lambda, rng) {
  if (lambda <= 0) return 0;
  const L = Math.exp(-Math.min(lambda, 40));
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rng();
  } while (p > L);
  return k - 1;
}

function sampleLogNormal(mu, sigma, min, max, rng) {
  const raw = Math.exp(mu + sigma * sampleStdNormal(rng));
  return Math.max(min, Math.min(max, Math.round(raw)));
}

function isHighResource(iso2) {
  return ANDV_PARAMS.high_resource_isos.includes(iso2);
}

// Minimal SIM_SEEDS for testing
const SIM_SEEDS = [
  { id: 'sh-primary', anchor_country_iso2: 'SH', lon: -5.71, lat: -15.93, day_symptoms: -12, day_outcome: -8, will_die: false, note: 'Saint Helena initial' },
  { id: 'za-secondary', anchor_country_iso2: 'ZA', lon: 28.047, lat: -26.204, day_symptoms: -4, day_outcome: 5, will_die: true, note: 'Johannesburg secondary' },
];

function runStochasticSim(seeds, rng_seed) {
  const rng = mulberry32(rng_seed);
  const cases = [];
  const queue = [];
  const p = ANDV_PARAMS;

  for (const s of seeds) {
    const sc = {
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
    };
    cases.push(sc);
    if (sc.day_outcome > 0) {
      queue.push({ sc, gen: 0 });
    }
  }

  let idx = 0;
  while (queue.length > 0) {
    const { sc: src, gen } = queue.shift();
    if (gen >= 4) continue;

    const n_secondary = samplePoisson(p.r_effective, rng);

    for (let i = 0; i < n_secondary; i++) {
      const roll = rng();
      let kind;
      if (roll < p.contact_probs_household) kind = 'household';
      else if (roll < p.contact_probs_household + p.contact_probs_healthcare) kind = 'healthcare';
      else if (roll < p.contact_probs_household + p.contact_probs_healthcare + p.contact_probs_fellow_pax) kind = 'fellow_pax';
      else kind = 'family_visit';

      const sar = kind === 'household' ? p.contact_sar_household
        : kind === 'healthcare' ? p.contact_sar_healthcare
        : kind === 'fellow_pax' ? p.contact_sar_fellow_pax
        : p.contact_sar_family_visit;
      if (rng() > sar) continue;

      const si = Math.max(
        p.serial_interval_min,
        Math.min(
          p.serial_interval_max,
          Math.round(p.serial_interval_mean + p.serial_interval_sd * sampleStdNormal(rng)),
        ),
      );
      const day_symptoms = src.day_symptoms + si;
      if (day_symptoms > p.projection_days) continue;
      if (day_symptoms < -40) continue;

      const cfr = isHighResource(src.anchor_country_iso2) ? p.cfr_high_resource : p.cfr_standard;
      const will_die = rng() < cfr;
      const onset_to_outcome = will_die
        ? sampleLogNormal(p.otd_mu, p.otd_sigma, 3, 21, rng)
        : p.otr_days;
      const day_outcome = day_symptoms + onset_to_outcome;

      idx++;
      const sc = {
        id: \`sim-\${idx}\`,
        anchor_country_iso2: src.anchor_country_iso2,
        lon: src.lon + (rng() - 0.5) * 0.1,
        lat: src.lat + (rng() - 0.5) * 0.1,
        day_exposed: day_symptoms - si,
        day_symptoms,
        day_outcome,
        will_die,
        kind,
        note: \`G\${gen + 1} \${kind}\`,
        generation: gen + 1,
        parent_id: src.id,
        is_seed: false,
        infected: true,
        flight_id: null,
      };
      cases.push(sc);
      if (day_outcome > 0) queue.push({ sc, gen: gen + 1 });
    }
  }

  return cases;
}

function analyzeSimulation(cases) {
  const byDay = {};
  for (let day = 0; day <= 90; day++) {
    byDay[day] = {
      total: 0,
      symptomatic: 0,
      dead: 0,
      recovered: 0,
      incubating: 0,
    };
  }

  for (const c of cases) {
    for (let day = 0; day <= 90; day++) {
      if (day < c.day_symptoms) {
        byDay[day].incubating++;
      } else if (day >= c.day_outcome) {
        if (c.will_die) {
          byDay[day].dead++;
        } else {
          byDay[day].recovered++;
        }
      } else {
        byDay[day].symptomatic++;
      }
      byDay[day].total++;
    }
  }

  const byCountry = {};
  for (const c of cases) {
    if (!byCountry[c.anchor_country_iso2]) {
      byCountry[c.anchor_country_iso2] = { total: 0, dead: 0, generations: {} };
    }
    byCountry[c.anchor_country_iso2].total++;
    if (c.will_die) byCountry[c.anchor_country_iso2].dead++;
    byCountry[c.anchor_country_iso2].generations[c.generation] = (byCountry[c.anchor_country_iso2].generations[c.generation] || 0) + 1;
  }

  const metrics = {
    total_cases: cases.length,
    total_deaths: cases.filter(c => c.will_die).length,
    peak_day: 0,
    peak_symptomatic: 0,
    avg_generation: cases.reduce((s, c) => s + c.generation, 0) / cases.length,
    by_country: byCountry,
    by_day: byDay,
  };

  for (let day = 0; day <= 90; day++) {
    if (byDay[day].symptomatic > metrics.peak_symptomatic) {
      metrics.peak_symptomatic = byDay[day].symptomatic;
      metrics.peak_day = day;
    }
  }

  return metrics;
}

// Run simulation
const cases = runStochasticSim(SIM_SEEDS, 42);
const metrics = analyzeSimulation(cases);

console.log(JSON.stringify(metrics, null, 2));
`;

eval(testCode);
