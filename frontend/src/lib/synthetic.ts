// Synthetic time-series generators for the App's live workbench: adjust the knobs, regenerate the series,
// and the live classical engine re-forecasts instantly. Mirrors the case families in
// data-pipeline/chronoscopelab/cases/forecast_cases.py (seasonal, trend+seasonal, intermittent,
// random-walk, white-noise). Deterministic given a seed (mulberry32) so a shared link reproduces it.

export type SyntheticKind = 'seasonal' | 'trend_seasonal' | 'intermittent' | 'random_walk' | 'white_noise';

export interface SyntheticKnobs {
  kind: SyntheticKind;
  n: number;
  seasonality: number;
  horizon: number;
  level: number;
  amp: number;
  slope: number;
  noise: number;
  seed: number;
}

export const DEFAULT_KNOBS: SyntheticKnobs = {
  kind: 'trend_seasonal',
  n: 180,
  seasonality: 12,
  horizon: 12,
  level: 50,
  amp: 12,
  slope: 0.3,
  noise: 3,
  seed: 7,
};

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussian(rng: () => number): number {
  // Box-Muller
  const u = Math.max(1e-12, rng());
  const v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function generateSeries(k: SyntheticKnobs): number[] {
  const rng = mulberry32(k.seed);
  const y: number[] = [];
  const m = Math.max(1, k.seasonality);
  for (let t = 0; t < k.n; t++) {
    let v: number;
    switch (k.kind) {
      case 'seasonal':
        v = k.level + k.amp * Math.sin((2 * Math.PI * t) / m) + k.noise * gaussian(rng);
        break;
      case 'trend_seasonal':
        v = k.level + k.slope * t + k.amp * Math.sin((2 * Math.PI * t) / m) + k.noise * gaussian(rng);
        break;
      case 'intermittent':
        v = rng() < 0.25 ? Math.abs(k.amp) * (0.5 + rng()) : 0;
        break;
      case 'random_walk':
        v = (y.length ? y[y.length - 1] : k.level) + k.noise * gaussian(rng);
        break;
      case 'white_noise':
        v = k.level + k.noise * gaussian(rng);
        break;
      default:
        v = k.level;
    }
    y.push(v);
  }
  return y;
}
