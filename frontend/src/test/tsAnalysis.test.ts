// Ground-truth tests for the live analysis module, mirroring the Python toolkit's test style:
// every diagnostic is checked against a process whose answer is known analytically (AR(1) ACF is
// phi^k, PACF cuts off after lag 1, a pure sine's dominant period is its true period, DFA alpha is
// ~0.5 on white noise and ~1.5 on a random walk).
import { describe, expect, it } from 'vitest';
import { acf, bartlettBand, dfaAlpha, histogram, pacf, periodogram, rolling, summaryStats } from '../lib/tsAnalysis';

// Deterministic LCG so the tests never flake (no Math.random).
function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (1664525 * s + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

// Box-Muller standard normals from the LCG.
function normals(n: number, seed: number): number[] {
  const u = lcg(seed);
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const a = Math.max(u(), 1e-12);
    out.push(Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * u()));
  }
  return out;
}

function ar1(n: number, phi: number, seed: number): number[] {
  const e = normals(n + 100, seed);
  const y: number[] = [0];
  for (let i = 1; i < n + 100; i++) y.push(phi * y[i - 1] + e[i]);
  return y.slice(100);
}

describe('summaryStats', () => {
  it('recovers moments of a known constant-plus-alternating series', () => {
    // y alternates 1,-1: mean 0, std 1, skew 0, kurtosis excess -2 (two-point distribution).
    const y = Array.from({ length: 1000 }, (_, i) => (i % 2 === 0 ? 1 : -1));
    const s = summaryStats(y);
    expect(s.n).toBe(1000);
    expect(s.mean).toBeCloseTo(0, 10);
    expect(s.std).toBeCloseTo(1, 10);
    expect(s.skewness).toBeCloseTo(0, 10);
    expect(s.kurtosisExcess).toBeCloseTo(-2, 10);
  });

  it('ignores NaN gaps', () => {
    const s = summaryStats([1, NaN, 3, NaN, 5]);
    expect(s.n).toBe(3);
    expect(s.mean).toBeCloseTo(3, 10);
  });
});

describe('acf (Box-Jenkins r_k)', () => {
  it('is phi^k on a long AR(1)', () => {
    const y = ar1(6000, 0.7, 42);
    const r = acf(y, 5);
    expect(r[0]).toBe(1);
    expect(r[1]).toBeCloseTo(0.7, 1);
    expect(r[2]).toBeCloseTo(0.49, 1);
    expect(r[3]).toBeCloseTo(0.343, 1);
  });

  it('is ~0 beyond lag 0 on white noise (inside the Bartlett band)', () => {
    const y = normals(4000, 7);
    const r = acf(y, 10);
    const band = bartlettBand(y.length);
    for (let k = 1; k <= 10; k++) expect(Math.abs(r[k])).toBeLessThan(2 * band);
  });
});

describe('pacf (Durbin-Levinson)', () => {
  it('cuts off after lag 1 on an AR(1): phi at lag 1, ~0 after', () => {
    const y = ar1(6000, 0.6, 11);
    const p = pacf(y, 6);
    expect(p[1]).toBeCloseTo(0.6, 1);
    const band = 2 * bartlettBand(y.length);
    for (let k = 2; k <= 6; k++) expect(Math.abs(p[k])).toBeLessThan(band + 0.02);
  });
});

describe('periodogram', () => {
  it('finds the true period of a pure sine', () => {
    const m = 24;
    const y = Array.from({ length: 480 }, (_, t) => Math.sin((2 * Math.PI * t) / m));
    const pg = periodogram(y);
    expect(pg.dominantPeriod).toBeCloseTo(m, 5);
  });

  it('splits power between two seasonalities (both peaks present)', () => {
    const y = Array.from({ length: 1008 }, (_, t) => Math.sin((2 * Math.PI * t) / 24) + 0.8 * Math.sin((2 * Math.PI * t) / 168));
    const pg = periodogram(y);
    // top-2 periods must be {24, 168}
    const order = pg.power.map((p, i) => [p, pg.periods[i]] as const).sort((a, b) => b[0] - a[0]);
    const top2 = [order[0][1], order[1][1]].sort((a, b) => a - b);
    expect(top2[0]).toBeCloseTo(24, 3);
    expect(top2[1]).toBeCloseTo(168, 3);
  });
});

describe('rolling', () => {
  it('rolling mean of a linear ramp ends at the mean of the last window', () => {
    const y = Array.from({ length: 50 }, (_, i) => i);
    const { mean } = rolling(y, 5);
    // last window = 45..49 -> mean 47
    expect(mean[49]).toBeCloseTo(47, 10);
  });

  it('rolling std of a constant series is 0', () => {
    const { std } = rolling(new Array(30).fill(3), 5);
    expect(std[29]).toBeCloseTo(0, 12);
  });
});

describe('dfaAlpha (Peng 1994 scaling exponent)', () => {
  it('is ~0.5 on white noise', () => {
    const a = dfaAlpha(normals(4096, 3));
    expect(a).not.toBeNull();
    expect(a!).toBeGreaterThan(0.4);
    expect(a!).toBeLessThan(0.62);
  });

  it('is ~1.5 on a random walk', () => {
    const e = normals(4096, 5);
    const y: number[] = []; let acc = 0;
    for (const x of e) { acc += x; y.push(acc); }
    const a = dfaAlpha(y);
    expect(a).not.toBeNull();
    expect(a!).toBeGreaterThan(1.3);
    expect(a!).toBeLessThan(1.7);
  });

  it('returns null when the series is too short', () => {
    expect(dfaAlpha(normals(32, 1))).toBeNull();
  });
});

describe('histogram', () => {
  it('counts sum to n and edges span the range', () => {
    const y = normals(500, 9);
    const h = histogram(y, 24);
    expect(h.counts.reduce((a, b) => a + b, 0)).toBe(500);
    expect(h.edges[0]).toBeCloseTo(Math.min(...y), 10);
    expect(h.edges[24]).toBeCloseTo(Math.max(...y), 10);
  });
});
