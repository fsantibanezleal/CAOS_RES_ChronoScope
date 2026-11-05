import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { describe, expect, it } from 'vitest';
import { BROWSER_CALIBRATION, calibratedLinearIntervals } from '../lib/calibratedLinearIntervals';

const source = (name: string) => JSON.parse(gunzipSync(readFileSync(new URL(
  `../../../docs/research/browser-linear/confirmation-v1/${name}.json.gz`, import.meta.url))).toString());
const records = source('series').test as { id: string; values: number[] }[];
const forecasts = source('forecasts') as { id: string; methods: Record<string, {point: number[]; lower: number[]; upper: number[]}> }[];
const byId = new Map(records.map(record => [record.id, record]));
const scale = (history: number[]) => {
  const mean = history.reduce((a, b) => a + b, 0) / history.length;
  return Math.sqrt(history.reduce((sum, value) => sum + (value - mean) ** 2, 0) / history.length);
};

describe('source-bound prefix-stratified browser intervals', () => {
  it('matches all 800 independently admitted confirmation paths', () => {
    expect(forecasts).toHaveLength(800);
    for (const forecast of forecasts) {
      const history = byId.get(forecast.id)!.values.slice(-60, -12);
      const expected = forecast.methods.stratified;
      const result = calibratedLinearIntervals(history, expected.point, scale(history));
      for (let i = 0; i < 12; i++) {
        expect(result.lower[i]).toBeCloseTo(expected.lower[i], 8);
        expect(result.upper[i]).toBeCloseTo(expected.upper[i], 8);
      }
    }
  });

  it('adversarial: changing units and translating cannot change the selected group or normalized interval', () => {
    const history = byId.get(forecasts[0].id)!.values.slice(-60, -12);
    const point = forecasts[0].methods.stratified.point;
    const first = calibratedLinearIntervals(history, point, scale(history));
    const converted = history.map(value => value * 1000 + 273.15);
    const next = calibratedLinearIntervals(converted, point.map(value => value * 1000 + 273.15), scale(converted));
    expect(next.group).toBe(first.group);
    for (let i = 0; i < 12; i++) {
      expect(next.lower[i]).toBeCloseTo(first.lower[i] * 1000 + 273.15, 7);
      expect(next.upper[i]).toBeCloseTo(first.upper[i] * 1000 + 273.15, 7);
    }
  });

  it('adversarial: malformed calibration or unsupported input cannot manufacture an interval', () => {
    const history = byId.get(forecasts[0].id)!.values.slice(-60, -12);
    const point = forecasts[0].methods.stratified.point;
    const broken = structuredClone(BROWSER_CALIBRATION);
    broken.absolute_residual_radii[0][0] = NaN;
    expect(() => calibratedLinearIntervals(history, point, scale(history), broken)).toThrow('metadata');
    expect(() => calibratedLinearIntervals(history, point, 1)).toThrow('scale');
    expect(() => calibratedLinearIntervals(history, point.slice(1), scale(history))).toThrow('input');
    expect(() => calibratedLinearIntervals(Array(48).fill(1), point, 1)).toThrow('scale');
  });
});
