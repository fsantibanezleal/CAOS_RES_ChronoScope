// Minimal live metrics for the synthetic workbench holdout (the browser scores the live classical
// forecasts on the held-out tail). Mirrors the MASE/coverage definitions in preqts/chronoscopelab, on a
// single holdout (the App is a workbench, not the full rolling backtest; that lives in the baked Benchmark).

export function seasonalNaiveMae(insample: number[], m: number): number {
  if (!Number.isInteger(m) || m < 1 || !insample.every(Number.isFinite)) return NaN;
  const step = m;
  if (insample.length <= step) return NaN;
  let s = 0;
  let n = 0;
  for (let t = step; t < insample.length; t++) {
    s += Math.abs(insample[t] - insample[t - step]);
    n++;
  }
  const scale = s / n;
  return Number.isFinite(scale) && scale > 0 ? scale : NaN;
}

export function mase(actual: number[], point: number[], scale: number): number {
  if (!Number.isFinite(scale) || !(scale > 0) || actual.length === 0 || actual.length !== point.length
      || !actual.every(Number.isFinite) || !point.every(Number.isFinite)) return NaN;
  let s = 0;
  let n = 0;
  for (let i = 0; i < actual.length; i++) {
    if (Number.isFinite(actual[i]) && Number.isFinite(point[i])) {
      s += Math.abs(actual[i] - point[i]);
      n++;
    }
  }
  const score = n ? s / n / scale : NaN;
  return Number.isFinite(score) ? score : NaN;
}

export function coverage(actual: number[], lower: number[], upper: number[]): number {
  if (actual.length === 0 || lower.length !== actual.length || upper.length !== actual.length
      || !actual.every(Number.isFinite) || !lower.every(Number.isFinite) || !upper.every(Number.isFinite)
      || lower.some((value, i) => value > upper[i])) return NaN;
  let inside = 0;
  let n = 0;
  for (let i = 0; i < actual.length; i++) {
    if (Number.isFinite(actual[i]) && Number.isFinite(lower[i]) && Number.isFinite(upper[i])) {
      if (actual[i] >= lower[i] && actual[i] <= upper[i]) inside++;
      n++;
    }
  }
  return n ? inside / n : NaN;
}
