import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { CombinationCase, CombinationIndex } from '../lib/contract.types';
import { loadCombinationCase } from '../api/artifacts';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const index: CombinationIndex = JSON.parse(readFileSync(join(root, 'data/derived/validated-combinations.json'), 'utf8'));

afterEach(() => vi.unstubAllGlobals());
describe('combination consumer contract', () => {
  it('retains the entire inventory and independently scores every displayed path', () => {
    expect(index.complete).toBe(true);
    expect(index.cases).toHaveLength(1802);
    expect(index.cohorts.map(c => [c.id, c.admitted, c.excluded])).toEqual([
      ['m4_weekly', 294, 65], ['m3_monthly', 1422, 6], ['selected_cases', 15, 0],
    ]);
    for (const entry of index.cases) {
      const row: CombinationCase = JSON.parse(readFileSync(join(root, 'data/derived', entry.path), 'utf8'));
      expect([row.id, row.dataset]).toEqual([entry.id, entry.dataset]);
      expect(row.origins.length).toBe(entry.origins);
      for (const origin of row.origins) for (const method of origin.methods) {
        expect(method.quantiles).toHaveLength(origin.actual.length);
        let absolute = 0;
        method.quantiles.forEach((q, i) => {
          if (!q.every(Number.isFinite) || !(q[0] <= q[1] && q[1] <= q[2])) throw new Error(`Invalid quantiles: ${entry.path}, ${method.name}`);
          absolute += Math.abs(q[1] - origin.actual[i]);
        });
        const computed = absolute / origin.actual.length / origin.scale;
        if (method.metrics.mase == null || !Number.isFinite(computed) || Math.abs(computed - method.metrics.mase) > 0.00001) throw new Error(`Displayed score mismatch: ${entry.path}, ${method.name}`);
      }
    }
  });
  it('adversarial: rejects traversal paths before making a request', async () => {
    const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
    await expect(loadCombinationCase('combinations/../../private.json')).rejects.toThrow('Invalid combination');
    expect(fetch).not.toHaveBeenCalled();
  });
  it('adversarial: rejects a response from a different series', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ dataset: 'm4_weekly', id: 'T2' }) }));
    await expect(loadCombinationCase('combinations/m4_weekly/T1.json')).rejects.toThrow('identity mismatch');
  });
  it('keeps missing measurements unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));
    await expect(loadCombinationCase('combinations/m4_weekly/T1.json')).rejects.toThrow('HTTP 404');
  });
});
