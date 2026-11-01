import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { Reevaluation } from '../lib/reevaluation.types';
import { mase } from '../lib/liveMetrics';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const data: Reevaluation = JSON.parse(readFileSync(join(root, 'data/derived/reevaluation.json'), 'utf8'));

describe('Common final-holdout contract', () => {
  it('adversarial: detects changed traces or source before admitting stored scores', () => {
    for (const [path, expected] of Object.entries({ ...data.trace_sha256, ...data.code_sha256 })) {
      const actual = createHash('sha256').update(readFileSync(join(root, path))).digest('hex');
      expect(actual, path).toBe(expected);
    }
  });

  it('scores every method against the same case holdout and historical scale', () => {
    expect(data.cases).toHaveLength(15);
    for (const c of data.cases) {
      const trace = JSON.parse(readFileSync(join(root, `data/derived/${c.case_id}/trace.json`), 'utf8'));
      expect(c.actual).toEqual(trace.actual);
      for (const method of c.methods) {
        expect(method.point).toHaveLength(c.horizon);
        expect(method.metrics.mase).toBeCloseTo(mase(c.actual, method.point,
          trace.history.slice(c.seasonality).reduce((s: number, v: number, i: number) => s + Math.abs(v - trace.history[i]), 0)
          / (trace.history.length - c.seasonality)), 8);
      }
    }
  });
});
