// Live classical forecasting engine (TypeScript), a faithful port of the pure-numpy Python core in
// data-pipeline/chronoscopelab/model/forecasters.py. This runs in the browser so the classical tier is
// genuinely LIVE (adjust a series or knobs, forecasts recompute instantly), computing the SAME thing the
// offline pipeline does. Parity with Python is asserted by a vitest against a committed fixture.
//
// Methods: seasonal-naive, SES, Holt (additive trend), Holt-Winters (additive), Theta. Point + interval.

export type Family = 'classical';

export interface MethodForecast {
  name: string;
  family: string;
  point: number[];
  lower: number[];
  upper: number[];
}

// --- normal quantile (Acklam's approximation; matches forecasters.normal_ppf) ---
const A = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
const B = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
const C = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
const D = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];

export function normalPpf(p: number): number {
  if (p <= 0) return -Infinity;
  if (p >= 1) return Infinity;
  const plow = 0.02425;
  const phigh = 1 - plow;
  if (p < plow) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((C[0] * q + C[1]) * q + C[2]) * q + C[3]) * q + C[4]) * q + C[5]) / ((((D[0] * q + D[1]) * q + D[2]) * q + D[3]) * q + 1);
  }
  if (p > phigh) {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((C[0] * q + C[1]) * q + C[2]) * q + C[3]) * q + C[4]) * q + C[5]) / ((((D[0] * q + D[1]) * q + D[2]) * q + D[3]) * q + 1);
  }
  const q = p - 0.5;
  const r = q * q;
  return (((((A[0] * r + A[1]) * r + A[2]) * r + A[3]) * r + A[4]) * r + A[5]) * q / (((((B[0] * r + B[1]) * r + B[2]) * r + B[3]) * r + B[4]) * r + 1);
}

// --- helpers ---
function linspace(a: number, b: number, n: number): number[] {
  if (n === 1) return [a];
  const step = (b - a) / (n - 1);
  return Array.from({ length: n }, (_, i) => a + step * i);
}

function mean(a: number[]): number {
  return a.reduce((s, v) => s + v, 0) / a.length;
}

function std(a: number[]): number {
  if (a.length === 0) return 0;
  const m = mean(a);
  return Math.sqrt(a.reduce((s, v) => s + (v - m) * (v - m), 0) / a.length);
}

function clean(y: number[]): number[] {
  // forward-fill then back-fill NaN so recursive methods stay defined (mirrors _clean)
  const out = y.slice();
  const idx = out.map((v, i) => (Number.isFinite(v) ? i : -1)).filter((i) => i >= 0);
  if (idx.length === 0) return out.map(() => 0);
  for (let i = 0; i < idx[0]; i++) out[i] = out[idx[0]];
  let last = out[idx[0]];
  for (let i = 0; i < out.length; i++) {
    if (!Number.isFinite(out[i])) out[i] = last;
    else last = out[i];
  }
  return out;
}

export interface PointFit {
  point: number[];
  sigma: number;
}

export function seasonalNaive(y: number[], m: number, h: number): PointFit {
  y = clean(y);
  const mm = m >= 1 && y.length > m ? m : 1;
  const season = y.slice(y.length - mm);
  const point = Array.from({ length: h }, (_, k) => season[k % mm]);
  const resid: number[] = [];
  for (let t = mm; t < y.length; t++) resid.push(y[t] - y[t - mm]);
  return { point, sigma: resid.length ? std(resid) : 0 };
}

function sesRun(y: number[], alpha: number): { fitted: number[]; level: number } {
  let level = y[0];
  const fitted = new Array(y.length).fill(0);
  fitted[0] = level;
  for (let t = 1; t < y.length; t++) {
    fitted[t] = level;
    level = alpha * y[t] + (1 - alpha) * level;
  }
  return { fitted, level };
}

function optAlpha(y: number[]): number {
  const grid = linspace(0.05, 0.95, 19);
  let bestA = grid[0];
  let bestSse = Infinity;
  for (const a of grid) {
    const { fitted } = sesRun(y, a);
    let sse = 0;
    for (let t = 1; t < y.length; t++) sse += (y[t] - fitted[t]) ** 2;
    if (sse < bestSse) {
      bestSse = sse;
      bestA = a;
    }
  }
  return bestA;
}

export function ses(y: number[], _m: number, h: number): PointFit {
  y = clean(y);
  const a = optAlpha(y);
  const { fitted, level } = sesRun(y, a);
  const resid = y.slice(1).map((v, i) => v - fitted[i + 1]);
  return { point: new Array(h).fill(level), sigma: y.length > 1 ? std(resid) : 0 };
}

function holtRun(y: number[], alpha: number, beta: number): { fitted: number[]; level: number; trend: number } {
  let level = y[0];
  let trend = y.length > 1 ? y[1] - y[0] : 0;
  const fitted = new Array(y.length).fill(0);
  fitted[0] = level;
  for (let t = 1; t < y.length; t++) {
    fitted[t] = level + trend;
    const prev = level;
    level = alpha * y[t] + (1 - alpha) * (level + trend);
    trend = beta * (level - prev) + (1 - beta) * trend;
  }
  return { fitted, level, trend };
}

export function holt(y: number[], _m: number, h: number): PointFit {
  y = clean(y);
  let best: [number, number] = [0.3, 0.1];
  let bestSse = Infinity;
  for (const a of linspace(0.1, 0.9, 9)) {
    for (const b of linspace(0.05, 0.5, 6)) {
      const { fitted } = holtRun(y, a, b);
      let sse = 0;
      for (let t = 1; t < y.length; t++) sse += (y[t] - fitted[t]) ** 2;
      if (sse < bestSse) {
        bestSse = sse;
        best = [a, b];
      }
    }
  }
  const { fitted, level, trend } = holtRun(y, best[0], best[1]);
  const resid = y.slice(1).map((v, i) => v - fitted[i + 1]);
  const point = Array.from({ length: h }, (_, k) => level + trend * (k + 1));
  return { point, sigma: y.length > 1 ? std(resid) : 0 };
}

function hwRun(y: number[], m: number, alpha: number, beta: number, gamma: number) {
  let level = mean(y.slice(0, m));
  let trend = y.length >= 2 * m ? (mean(y.slice(m, 2 * m)) - mean(y.slice(0, m))) / m : 0;
  const season = Array.from({ length: m }, (_, i) => y[i] - level);
  const fitted = new Array(y.length).fill(0);
  for (let t = 0; t < y.length; t++) {
    const s = season[t % m];
    fitted[t] = level + trend + s;
    const prev = level;
    level = alpha * (y[t] - s) + (1 - alpha) * (level + trend);
    trend = beta * (level - prev) + (1 - beta) * trend;
    season[t % m] = gamma * (y[t] - level) + (1 - gamma) * s;
  }
  return { fitted, level, trend, season };
}

export function holtWinters(y: number[], m: number, h: number): PointFit {
  y = clean(y);
  if (m < 2 || y.length < 2 * m) return holt(y, m, h);
  let best: [number, number, number] = [0.3, 0.1, 0.1];
  let bestSse = Infinity;
  for (const a of [0.1, 0.3, 0.5, 0.8]) {
    for (const b of [0.05, 0.2]) {
      for (const g of [0.1, 0.3, 0.6]) {
        const { fitted } = hwRun(y, m, a, b, g);
        let sse = 0;
        for (let t = m; t < y.length; t++) sse += (y[t] - fitted[t]) ** 2;
        if (sse < bestSse) {
          bestSse = sse;
          best = [a, b, g];
        }
      }
    }
  }
  const { fitted, level, trend, season } = hwRun(y, m, best[0], best[1], best[2]);
  const resid: number[] = [];
  for (let t = m; t < y.length; t++) resid.push(y[t] - fitted[t]);
  const point = Array.from({ length: h }, (_, k) => level + trend * (k + 1) + season[k % m]);
  return { point, sigma: y.length > m ? std(resid) : 0 };
}

function olsSlope(y: number[]): number {
  const n = y.length;
  if (n < 2) return 0;
  const t = Array.from({ length: n }, (_, i) => i);
  const tm = mean(t);
  const ym = mean(y);
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    num += (t[i] - tm) * (y[i] - ym);
    den += (t[i] - tm) * (t[i] - tm);
  }
  return den === 0 ? 0 : num / den;
}

export function theta(y: number[], _m: number, h: number): PointFit {
  y = clean(y);
  const b = olsSlope(y);
  const a = optAlpha(y);
  const { fitted, level } = sesRun(y, a);
  const resid = y.slice(1).map((v, i) => v - fitted[i + 1]);
  const point = Array.from({ length: h }, (_, k) => level + 0.5 * b * (k + 1));
  return { point, sigma: y.length > 1 ? std(resid) : 0 };
}

export const CLASSICAL_METHODS: { name: string; fn: (y: number[], m: number, h: number) => PointFit }[] = [
  { name: 'SeasonalNaive', fn: seasonalNaive },
  { name: 'SES', fn: ses },
  { name: 'Holt', fn: holt },
  { name: 'HoltWinters', fn: holtWinters },
  { name: 'Theta', fn: theta },
];

export function gaussianQuantiles(point: number[], sigma: number, levels: number[]): number[][] {
  const h = point.length;
  const cols = levels.map((lv) => point.map((p, i) => p + normalPpf(lv) * sigma * Math.sqrt(i + 1)));
  // monotone across levels (cumulative max), returned row-major (h rows x L cols)
  const out: number[][] = [];
  for (let i = 0; i < h; i++) {
    const row: number[] = [];
    let run = -Infinity;
    for (let j = 0; j < levels.length; j++) {
      run = Math.max(run, cols[j][i]);
      row.push(run);
    }
    out.push(row);
  }
  return out;
}

export function forecastAllLive(y: number[], m: number, h: number, levels: number[]): MethodForecast[] {
  const pointCol = levels.reduce((best, lv, j) => (Math.abs(lv - 0.5) < Math.abs(levels[best] - 0.5) ? j : best), 0);
  return CLASSICAL_METHODS.map(({ name, fn }) => {
    const { point, sigma } = fn(y, m, h);
    const q = gaussianQuantiles(point, sigma, levels);
    return {
      name,
      family: 'classical',
      point: q.map((row) => row[pointCol]),
      lower: q.map((row) => row[0]),
      upper: q.map((row) => row[levels.length - 1]),
    };
  });
}
