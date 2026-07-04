// The replay SPA: list cases grouped by CATEGORY, select one, replay its committed trace (CONTRACT 2), and
// compare forecasting methods (point + interval vs the held-out truth) with their backtest metrics. The
// always-available static path (ADR-0054); the optional Pyodide live lane (src/pyodide) is the recompute upgrade.
import { useEffect, useMemo, useState } from 'react';
import { loadIndex, loadManifest, loadTrace } from './api/artifacts';
import type { CaseIndex, CaseManifest, Trace } from './lib/contract.types';
import { ForecastChart } from './render/ForecastChart';

const fmt = (v: number | null, nd = 3) => (v == null || Number.isNaN(v) ? '-' : v.toFixed(nd));

export default function App() {
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [sel, setSel] = useState('');
  const [manifest, setManifest] = useState<CaseManifest | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [method, setMethod] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    loadIndex()
      .then((ix) => {
        setIndex(ix);
        setSel(ix.cases[0]?.case_id ?? '');
      })
      .catch((e: unknown) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (!sel) return;
    loadManifest(sel)
      .then((m) => {
        setManifest(m);
        return loadTrace(m.artifact.path);
      })
      .then((tr) => {
        setTrace(tr);
        setMethod(tr.summary.best_method ?? tr.methods[0]?.name ?? '');
      })
      .catch((e: unknown) => setErr(String(e)));
  }, [sel]);

  const byCategory = useMemo(() => {
    const out: Record<string, string[]> = {};
    index?.cases.forEach((c) => (out[c.category] ??= []).push(c.case_id));
    return out;
  }, [index]);

  const selectedMethod = trace?.methods.find((m) => m.name === method) ?? trace?.methods[0];

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 900, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>ChronoScope: forecasting method atlas</h1>
      <p>
        Replaying committed backtests (CONTRACT 2). {index?.n_cases ?? 0} cases across{' '}
        {Object.keys(byCategory).length} categories. Grey = history, green dashed = held-out truth, blue = the
        selected method with its prediction interval.
      </p>
      {err && <p style={{ color: '#f85149' }}>error: {err}</p>}

      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
        <label>
          Case:{' '}
          <select value={sel} onChange={(e) => setSel(e.target.value)}>
            {Object.entries(byCategory).map(([cat, ids]) => (
              <optgroup key={cat} label={cat}>
                {ids.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        {trace && (
          <label>
            Method:{' '}
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              {trace.methods.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {manifest && (
        <p>
          lane: <b>{manifest.lane}</b>, source: <b>{manifest.real_or_synthetic}</b>. <i>{manifest.expected_band}</i>
        </p>
      )}

      {trace && selectedMethod && <ForecastChart trace={trace} method={selectedMethod} />}

      {trace && (
        <>
          <p>
            best method: <b>{trace.summary.best_method}</b> (MASE {fmt(trace.summary.best_mase)}). Backtest over the
            case history; MASE &lt; 1 beats the seasonal-naive baseline.
          </p>
          <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 14 }}>
            <thead>
              <tr>
                {['method', 'family', 'MASE', 'WQL', 'coverage', 'windows'].map((h) => (
                  <th key={h} style={{ textAlign: 'left', borderBottom: '1px solid #30363d', padding: '4px 8px' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trace.methods.map((m) => (
                <tr key={m.name} style={{ fontWeight: m.name === trace.summary.best_method ? 700 : 400 }}>
                  <td style={{ padding: '4px 8px' }}>{m.name}</td>
                  <td style={{ padding: '4px 8px' }}>{m.family}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(m.backtest.mase)}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(m.backtest.wql)}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(m.backtest.coverage, 2)}</td>
                  <td style={{ padding: '4px 8px' }}>{m.backtest.n_windows ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </main>
  );
}
