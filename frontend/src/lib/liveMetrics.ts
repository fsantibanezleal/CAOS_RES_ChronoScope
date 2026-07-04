// Minimal live metrics for the synthetic workbench holdout (the browser scores the live classical
// forecasts on the held-out tail). Mirrors the MASE/coverage definitions in preqts/chronoscopelab, on a
// single holdout (the App is a workbench, not the full rolling backtest; that lives in the baked Benchmark).

export function seasonalNaiveMae(insample: number[], m: number): number {
  const step = m >= 1 && insample.length > m ? m : 1;
  if (insample.length <= step) return NaN;
  let s = 0;
  let n = 0;
  for (let t = step; t < insample.length; t++) {
    s += Math.abs(insample[t] - insample[t - step]);
    n++;
  }
  const scale = s / n;
  return scale > 0 ? scale : 1e-8;
}

export function mase(actual: number[], point: number[], scale: number): number {
  if (!(scale > 0) || actual.length === 0) return NaN;
  let s = 0;
  let n = 0;
  for (let i = 0; i < actual.length; i++) {
    if (Number.isFinite(actual[i]) && Number.isFinite(point[i])) {
      s += Math.abs(actual[i] - point[i]);
      n++;
    }
  }
  return n ? s / n / scale : NaN;
}

export function coverage(actual: number[], lower: number[], upper: number[]): number {
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
