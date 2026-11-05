import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { Reevaluation } from '../lib/reevaluation.types';
import { mase } from '../lib/liveMetrics';

const root = fileURLToPath(new URL('../../../', import.meta.url));
describe.each(['reevaluation', 'fresh-reevaluation'])('%s final-holdout contract', (artifact) => {
  const data: Reevaluation = JSON.parse(readFileSync(join(root, `data/derived/${artifact}.json`), 'utf8'));

  it('adversarial: detects changed traces or source before admitting stored scores', () => {
    if (data.source_comparison_sha256) {
      expect(createHash('sha256').update(readFileSync(join(root, 'data/derived/reevaluation.json'))).digest('hex')).toBe(data.source_comparison_sha256);
    }
    for (const [path, expected] of Object.entries({ ...data.trace_sha256, ...data.input_sha256,
      ...(artifact === 'reevaluation' ? data.code_sha256 : {}) })) {
      const actual = createHash('sha256').update(readFileSync(join(root, path))).digest('hex');
      expect(actual, path).toBe(expected);
    }
    if (artifact === 'fresh-reevaluation') {
      // Independently hash the historical members, rather than substitute the
      // current export/analysis code for the experiment's original source.
      const receipt = JSON.parse(readFileSync(join(root, 'docs/research/fresh-source-archive.json'), 'utf8'));
      const archive = join(root, receipt.archive);
      expect(createHash('sha256').update(readFileSync(archive)).digest('hex')).toBe(receipt.archive_sha256);
      expect(createHash('sha256').update(readFileSync(join(root, receipt.artifact))).digest('hex')).toBe(receipt.artifact_sha256);
      const reader = spawnSync('python', ['-c', [
        'import sys,zipfile,json,base64',
        'with zipfile.ZipFile(sys.argv[1]) as z:',
        ' assert len(z.namelist())==len(set(z.namelist()))',
        ' print(json.dumps({n:base64.b64encode(z.read(n)).decode() for n in z.namelist()}))',
      ].join('\n'), archive], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
      expect(reader.status, reader.stderr).toBe(0);
      const sources: Record<string, string> = JSON.parse(reader.stdout);
      expect(Object.keys(sources).sort()).toEqual(Object.keys(data.code_sha256).sort());
      for (const [path, expected] of Object.entries(data.code_sha256)) {
        expect(createHash('sha256').update(Buffer.from(sources[path], 'base64')).digest('hex'), path).toBe(expected);
      }
    }
  });

  it('scores every method against the same case holdout and historical scale', () => {
    expect(data.cases).toHaveLength(15);
    for (const c of data.cases) {
      const trace = JSON.parse(readFileSync(join(root, `data/derived/${c.case_id}/trace.json`), 'utf8'));
      expect(c.actual).toEqual(trace.actual);
      expect(c.history).toHaveLength(trace.history_len);
      for (let i = 0; i < trace.history_index.length; i++) {
        expect(c.history[trace.history_index[i]]).toBeCloseTo(trace.history[i], 4);
      }
      for (const method of c.methods) {
        expect(method.point).toHaveLength(c.horizon);
        expect(method.metrics.mase).toBeCloseTo(mase(c.actual, method.point,
          c.history.slice(c.seasonality).reduce((s: number, v: number, i: number) => s + Math.abs(v - c.history[i]), 0)
          / (c.history.length - c.seasonality)), 8);
      }
    }
  });
});
