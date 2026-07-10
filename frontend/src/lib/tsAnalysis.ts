// Live time-series analysis (the browser subset of the Python analysis toolkit): the LIGHT diagnostics that
// recompute instantly as knobs move. Heavy verdicts (ADF/KPSS/PP, MF-DFA, RQA, Markov regimes) come from the
// BAKED analysis.json for committed cases; this module mirrors the light ones so the synthetic workbench is
// genuinely live. Definitions mirror chronoscopelab/analysis (same formulas, same references).

export interface SummaryStats {
  n: number; mean: number; std: number; min: number; max: number; skewness: number; kurtosisExcess: number;
}

export function summaryStats(y: number[]): SummaryStats {
  const v = y.filter(Number.isFinite);
  const n = v.length;
  const mean = v.reduce((a, b) => a + b, 0) / Math.max(1, n);
  let m2 = 0, m3 = 0, m4 = 0;
  for (const x of v) { const d = x - mean; m2 += d * d; m3 += d ** 3; m4 += d ** 4; }
  m2 /= n; m3 /= n; m4 /= n;
  const sd = Math.sqrt(m2);
  return {
    n, mean, std: sd, min: Math.min(...v), max: Math.max(...v),
    skewness: sd > 0 ? m3 / sd ** 3 : 0,
    kurtosisExcess: sd > 0 ? m4 / (m2 * m2) - 3 : 0,
  };
}

// ACF r_k = c_k / c_0 (Box-Jenkins); the 95% Bartlett band is +/-1.96/sqrt(n).
export function acf(y: number[], nlags: number): number[] {
  const v = y.filter(Number.isFinite);
  const n = v.length;
  const mean = v.reduce((a, b) => a + b, 0) / Math.max(1, n);
  const c0 = v.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
  const out: number[] = [1];
  for (let k = 1; k <= Math.min(nlags, n - 1); k++) {
    let ck = 0;
    for (let t = k; t < n; t++) ck += (v[t] - mean) * (v[t - k] - mean);
    out.push(c0 > 0 ? ck / n / c0 : 0);
  }
  return out;
}

// PACF via the Durbin-Levinson recursion on the ACF (mirrors statsmodels method='ld').
export function pacf(y: number[], nlags: number): number[] {
  const rho = acf(y, nlags);
  const p = Math.min(nlags, rho.length - 1);
  const phi: number[][] = Array.from({ length: p + 1 }, () => new Array(p + 1).fill(0));
  const out: number[] = [1];
  if (p >= 1) { phi[1][1] = rho[1]; out.push(rho[1]); }
  for (let k = 2; k <= p; k++) {
    let num = rho[k], den = 1;
    for (let j = 1; j < k; j++) { num -= phi[k - 1][j] * rho[k - j]; den -= phi[k - 1][j] * rho[j]; }
    const pk = den !== 0 ? num / den : 0;
    phi[k][k] = pk;
    for (let j = 1; j < k; j++) phi[k][j] = phi[k - 1][j] - pk * phi[k - 1][k - j];
    out.push(pk);
  }
  return out;
}

export const bartlettBand = (n: number) => 1.96 / Math.sqrt(Math.max(1, n));

// Schuster periodogram via a direct DFT (n <= ~2000 here, O(n^2) is fine): power vs period.
export function periodogram(y: number[]): { periods: number[]; power: number[]; dominantPeriod: number | null } {
  const v = y.filter(Number.isFinite);
  const n = v.length;
  const mean = v.reduce((a, b) => a + b, 0) / Math.max(1, n);
  const half = Math.floor(n / 2);
  const periods: number[] = [];
  const power: number[] = [];
  for (let k = 1; k <= half; k++) {
    let re = 0, im = 0;
    const w = (2 * Math.PI * k) / n;
    for (let t = 0; t < n; t++) { const d = v[t] - mean; re += d * Math.cos(w * t); im -= d * Math.sin(w * t); }
    periods.push(n / k);
    power.push((re * re + im * im) / n);
  }
  let best = -1, bestP: number | null = null;
  for (let i = 0; i < power.length; i++) if (power[i] > best) { best = power[i]; bestP = periods[i]; }
  return { periods, power, dominantPeriod: bestP };
}

export function rolling(y: number[], w: number): { mean: (number | null)[]; std: (number | null)[] } {
  const mean: (number | null)[] = [], std: (number | null)[] = [];
  for (let i = 0; i < y.length; i++) {
    const seg = y.slice(Math.max(0, i - w + 1), i + 1).filter(Number.isFinite);
    if (seg.length < 2) { mean.push(null); std.push(null); continue; }
    const m = seg.reduce((a, b) => a + b, 0) / seg.length;
    mean.push(m);
    std.push(Math.sqrt(seg.reduce((a, b) => a + (b - m) ** 2, 0) / seg.length));
  }
  return { mean, std };
}

// DFA scaling exponent alpha (Peng 1994): integrate, per-window linear detrend, RMS fluctuation vs scale.
// alpha ~ 0.5 white noise · ~1 pink · ~1.5 random walk; fGn H = alpha, fBm H = alpha - 1.
export function dfaAlpha(y: number[]): number | null {
  const v = y.filter(Number.isFinite);
  const n = v.length;
  if (n < 64) return null;
  const mean = v.reduce((a, b) => a + b, 0) / n;
  const prof: number[] = []; let acc = 0;
  for (const x of v) { acc += x - mean; prof.push(acc); }
  const scales: number[] = [];
  for (let s = 8; s <= Math.floor(n / 4); s = Math.round(s * 1.5)) scales.push(s);
  const logS: number[] = [], logF: number[] = [];
  for (const s of scales) {
    const k = Math.floor(n / s);
    let f2 = 0, cnt = 0;
    for (let b = 0; b < k; b++) {
      const seg = prof.slice(b * s, (b + 1) * s);
      // linear detrend via least squares on 0..s-1
      const m = seg.length; const tx = (m - 1) / 2;
      let sxy = 0, sxx = 0, my = seg.reduce((a, c) => a + c, 0) / m;
      for (let t = 0; t < m; t++) { sxy += (t - tx) * (seg[t] - my); sxx += (t - tx) ** 2; }
      const slope = sxx > 0 ? sxy / sxx : 0;
      for (let t = 0; t < m; t++) { const r = seg[t] - (my + slope * (t - tx)); f2 += r * r; cnt++; }
    }
    if (cnt > 0) { logS.push(Math.log(s)); logF.push(0.5 * Math.log(f2 / cnt)); }
  }
  if (logS.length < 3) return null;
  const mx = logS.reduce((a, b) => a + b, 0) / logS.length;
  const my = logF.reduce((a, b) => a + b, 0) / logF.length;
  let num = 0, den = 0;
  for (let i = 0; i < logS.length; i++) { num += (logS[i] - mx) * (logF[i] - my); den += (logS[i] - mx) ** 2; }
  return den > 0 ? num / den : null;
}

// Classical additive decomposition (the moving-average method, Hyndman & Athanasopoulos FPP3 ch. 3):
// trend = centered MA(m) (an even m uses the standard 2x(m) average), seasonal = per-phase means of the
// detrended series (normalized to sum 0), remainder = y - trend - seasonal. This is the LIGHT live mirror
// of the baked STL/MSTL panels: exact for stable seasonality, honest about edges (trend is NaN in the
// first/last m/2 points, as in every classical implementation).
export interface Decomposition {
  trend: (number | null)[];
  seasonal: number[];
  remainder: (number | null)[];
  seasonalStrength: number; // max(0, 1 - Var(remainder)/Var(seasonal + remainder)) (FPP3 12.2)
  trendStrength: number; // max(0, 1 - Var(remainder)/Var(trend + remainder))
}

export function decompose(y: number[], m: number): Decomposition | null {
  const n = y.length;
  if (m < 2 || n < 2 * m + 1) return null;
  const half = Math.floor(m / 2);
  const trend: (number | null)[] = new Array(n).fill(null);
  for (let t = half; t < n - half; t++) {
    let s = 0;
    if (m % 2 === 0) {
      // 2 x m-MA: half-weights on the two outermost points
      s = (y[t - half] + y[t + half]) / 2;
      for (let j = -half + 1; j <= half - 1; j++) s += y[t + j];
      s /= m;
    } else {
      for (let j = -half; j <= half; j++) s += y[t + j];
      s /= m;
    }
    trend[t] = Number.isFinite(s) ? s : null;
  }
  // seasonal indices from the detrended series
  const sums = new Array(m).fill(0);
  const counts = new Array(m).fill(0);
  for (let t = 0; t < n; t++) {
    const tr = trend[t];
    if (tr == null || !Number.isFinite(y[t])) continue;
    sums[t % m] += y[t] - tr;
    counts[t % m]++;
  }
  const seasonalIdx = sums.map((s, i) => (counts[i] > 0 ? s / counts[i] : 0));
  const meanIdx = seasonalIdx.reduce((a, b) => a + b, 0) / m;
  const centered = seasonalIdx.map((v) => v - meanIdx); // sums to 0 by construction
  const seasonal = Array.from({ length: n }, (_, t) => centered[t % m]);
  const remainder: (number | null)[] = Array.from({ length: n }, (_, t) =>
    trend[t] == null || !Number.isFinite(y[t]) ? null : y[t] - (trend[t] as number) - seasonal[t],
  );
  const varOf = (v: number[]) => {
    if (v.length < 2) return NaN;
    const mu = v.reduce((a, b) => a + b, 0) / v.length;
    return v.reduce((a, b) => a + (b - mu) ** 2, 0) / v.length;
  };
  const rem = remainder.filter((v): v is number => v != null && Number.isFinite(v));
  const pairsSeas: number[] = [];
  const pairsTrend: number[] = [];
  for (let t = 0; t < n; t++) {
    if (remainder[t] == null) continue;
    pairsSeas.push(seasonal[t] + (remainder[t] as number));
    pairsTrend.push((trend[t] as number) + (remainder[t] as number));
  }
  const vr = varOf(rem);
  const seasonalStrength = Math.max(0, 1 - vr / Math.max(1e-12, varOf(pairsSeas)));
  const trendStrength = Math.max(0, 1 - vr / Math.max(1e-12, varOf(pairsTrend)));
  return { trend, seasonal, remainder, seasonalStrength, trendStrength };
}

// Normal QQ pairs: sorted sample quantiles vs standard-normal quantiles at the Blom plotting
// positions (i - 3/8)/(n + 1/4). A straight line = Gaussian; S-shape = heavy tails.
export function qqPairs(values: number[]): { theoretical: number[]; sample: number[] } {
  const v = values.filter(Number.isFinite).slice().sort((a, b) => a - b);
  const n = v.length;
  if (n < 8) return { theoretical: [], sample: [] };
  const mean = v.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(v.reduce((a, b) => a + (b - mean) ** 2, 0) / n) || 1;
  const theoretical: number[] = [];
  const sample: number[] = [];
  for (let i = 1; i <= n; i++) {
    theoretical.push(normalInv((i - 0.375) / (n + 0.25)));
    sample.push((v[i - 1] - mean) / sd);
  }
  return { theoretical, sample };
}

// Acklam's rational approximation of the standard normal inverse CDF (|error| < 1.15e-9).
export function normalInv(p: number): number {
  if (!(p > 0 && p < 1)) return NaN;
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const pl = 0.02425;
  let q: number, r: number;
  if (p < pl) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= 1 - pl) {
    q = p - 0.5; r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

export function histogram(y: number[], bins = 24): { edges: number[]; counts: number[] } {
  const v = y.filter(Number.isFinite);
  const lo = Math.min(...v), hi = Math.max(...v);
  const w = (hi - lo) / bins || 1;
  const counts = new Array(bins).fill(0);
  for (const x of v) counts[Math.min(bins - 1, Math.floor((x - lo) / w))]++;
  return { edges: Array.from({ length: bins + 1 }, (_, i) => lo + i * w), counts };
}
