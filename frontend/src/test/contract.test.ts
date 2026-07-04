// Ties the CONTRACT 2 TS mirror to the REAL committed artifacts: the index, a manifest, and its trace must parse
// into the mirror types and pass basic shape checks. If the pipeline changes the schema without updating
// contract.types.ts, this test (and tsc) fail.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import type { CaseIndex, CaseManifest, Trace } from '../lib/contract.types';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const read = <T>(...p: string[]): T => JSON.parse(readFileSync(join(ROOT, 'data', 'derived', ...p), 'utf-8')) as T;

describe('CONTRACT 2 mirror matches the committed artifacts', () => {
  it('index -> manifest -> trace parse into the mirror types and are consistent', () => {
    const idx = read<CaseIndex>('manifests', 'index.json');
    expect(idx.schema).toContain('chronoscope.index/');
    expect(idx.cases.length).toBeGreaterThan(0);

    const m = read<CaseManifest>('manifests', `${idx.cases[0].case_id}.json`);
    expect(m.artifact.bytes).toBeGreaterThan(0);
    expect(['live', 'precompute']).toContain(m.lane);
    expect(m.series.n_obs).toBeGreaterThan(0);

    const tr = read<Trace>(...m.artifact.path.split('/'));
    expect(tr.schema).toContain('chronoscope.trace/');
    expect(tr.actual.length).toBe(tr.horizon);
    expect(tr.methods.length).toBeGreaterThan(0);
    for (const meth of tr.methods) {
      expect(meth.point.length).toBe(tr.horizon);
      expect(meth.lower.length).toBe(tr.horizon);
      expect(meth.upper.length).toBe(tr.horizon);
    }
    const names = tr.methods.map((x) => x.name);
    expect(names).toContain(tr.summary.best_method);
  });
});
