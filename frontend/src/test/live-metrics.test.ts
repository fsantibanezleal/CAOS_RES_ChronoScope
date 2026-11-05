import { expect, it } from 'vitest';
import { coverage, mase, seasonalNaiveMae } from '../lib/liveMetrics';

it('scores a complete held-out path against the observed seasonal scale', () => {
  const scale = seasonalNaiveMae([10, 12, 14, 16], 1);
  expect(scale).toBe(2);
  expect(mase([18, 20], [17, 21], scale)).toBe(.5);
  expect(coverage([18, 20], [17, 19], [19, 21])).toBe(1);
});

it('adversarial: a constant or nonfinite prefix cannot fabricate a raw-unit MASE denominator', () => {
  for (const history of [[5, 5, 5], [1, NaN, 3], [1, Infinity, 3]]) expect(seasonalNaiveMae(history, 1)).toBeNaN();
  expect(seasonalNaiveMae([1, 2, 3], 0)).toBeNaN();
  expect(seasonalNaiveMae([1, 2, 3], 3)).toBeNaN();
  expect(mase([5], [5], seasonalNaiveMae([5, 5, 5], 1))).toBeNaN();
});

it('adversarial: incomplete or invalid forecasts cannot improve scores by dropping bad pairs', () => {
  expect(mase([1, 2], [1], 1)).toBeNaN();
  expect(mase([1, 2], [1, NaN], 1)).toBeNaN();
  expect(mase([1, 2], [1, 2], Infinity)).toBeNaN();
  expect(mase([1e308], [-1e308], 1)).toBeNaN();
  expect(coverage([1, 2], [0], [2])).toBeNaN();
  expect(coverage([1, 2], [0, NaN], [2, 3])).toBeNaN();
  expect(coverage([1, 2], [2, 0], [0, 3])).toBeNaN();
});

it('adversarial: changing observable units and location preserves scaled loss and coverage', () => {
  const convert = (values: number[]) => values.map(value => value * 1000 + 273.15);
  const history = [10, 12, 14, 16], actual = [18, 20], point = [17, 21], lower = [17, 19], upper = [19, 21];
  expect(mase(convert(actual), convert(point), seasonalNaiveMae(convert(history), 1)))
    .toBeCloseTo(mase(actual, point, seasonalNaiveMae(history, 1)), 12);
  expect(coverage(convert(actual), convert(lower), convert(upper))).toBe(coverage(actual, lower, upper));
});
