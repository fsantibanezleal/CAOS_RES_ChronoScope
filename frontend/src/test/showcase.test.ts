import { describe, expect, it } from 'vitest';
import { completedMemory, delayCoordinates, projectDelay, SHOWCASE_KINDS } from '../lib/showcase';
describe('Source-bound showcase geometry and information timing', () => {
  it('adversarial: every delay coordinate stays inside the observed prefix', () => {
    const history = Array.from({ length: 2000 }, (_, i) => i * 3 - 8);
    const points = delayCoordinates(history, 4);
    expect(points.length).toBeLessThanOrEqual(500);
    for (const point of points) { expect(point.index + 8).toBeLessThan(history.length); expect(point.value).toEqual([history[point.index], history[point.index + 4], history[point.index + 8]]); }
    expect(delayCoordinates([1, NaN, 3])).toEqual([]);
    expect(delayCoordinates([1, 2], 1)).toEqual([]);
    expect(delayCoordinates([1, 2, 3], 0)).toEqual([]);
  });
  it('adversarial: a partly observed block cannot enter memory at the query', () => {
    expect(completedMemory([10, 20, 30, 40], 12, 42)).toEqual([10, 20, 30]);
    expect(completedMemory([10, 20, 30, 40], 12, 41)).toEqual([10, 20]);
    expect(completedMemory([10], 0, 20)).toEqual([]);
  });
  it('adversarial: positive affine unit conversions cannot distort the displayed geometry', () => {
    const point = [2, 7, 4], center = 3, span = 9;
    expect(projectDelay(point.map(v => 1000 * v - 12), 1000 * center - 12, 1000 * span, .7)).toEqual(projectDelay(point, center, span, .7));
    expect(SHOWCASE_KINDS).toEqual(['system', 'component', 'domain', 'dynamics', 'method', 'decision']);
  });
});
