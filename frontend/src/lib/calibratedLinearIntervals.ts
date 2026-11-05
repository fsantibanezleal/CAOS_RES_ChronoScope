import data from './browserCalibration.json';
import type { components } from './contract.gen';

export type BrowserCalibration = components['schemas']['BrowserCalibration'];
export const BROWSER_CALIBRATION = data as BrowserCalibration;
export const BROWSER_LINEAR_NAME = 'Normalized linear (ONNX)';

/** Marginal per-lead bands, calibrated only for the documented synthetic population. */
export function calibratedLinearIntervals(history: number[], point: number[], scale: number,
  calibration: BrowserCalibration = BROWSER_CALIBRATION) {
  const c = calibration;
  if (c.lookback !== 48 || c.horizon !== 12 || c.alpha !== .2
      || c.roughness_boundaries.length !== 2 || c.roughness_boundaries[0] !== .5 || c.roughness_boundaries[1] !== 1.25
      || c.calibration_bin_counts.length !== 3 || c.calibration_bin_counts.some(n => !Number.isInteger(n) || n < 20)
      || c.absolute_residual_radii.length !== 3 || c.absolute_residual_radii.some(row =>
        row.length !== 12 || row.some(value => !Number.isFinite(value) || value < 0))) throw new Error('Invalid calibration metadata');
  if (history.length < c.lookback || point.length !== c.horizon || !history.every(Number.isFinite)
      || !point.every(Number.isFinite) || !Number.isFinite(scale) || scale <= 0) throw new Error('Invalid calibrated forecast input');
  const window = history.slice(-c.lookback);
  const mean = window.reduce((a, b) => a + b, 0) / window.length;
  const variance = window.reduce((sum, value) => sum + (value - mean) ** 2, 0) / window.length;
  if (!Number.isFinite(variance) || variance <= 0 || Math.abs(Math.sqrt(variance) / scale - 1) > 1e-9) {
    throw new Error('Unavailable or inconsistent observed scale');
  }
  const roughness = window.slice(1).reduce((sum, value, i) => sum + (value - window[i]) ** 2, 0) / (window.length - 1) / variance;
  const group = roughness < c.roughness_boundaries[0] ? 0 : roughness < c.roughness_boundaries[1] ? 1 : 2;
  const radii = c.absolute_residual_radii[group];
  const lower = point.map((value, i) => value - radii[i] * scale);
  const upper = point.map((value, i) => value + radii[i] * scale);
  if (![...lower, ...upper].every(Number.isFinite)) throw new Error('Nonfinite calibrated interval');
  return { lower, upper, group };
}
