// The App page: the interactive workbench. Two modes:
//  - Synthetic (LIVE): adjust the knobs, the TS classical engine re-forecasts instantly in the browser.
//  - Baked case (REPLAY): load a committed case and see the whole ladder (classical + statistical + ML +
//    foundation) from the leakage-safe backtest baked offline.
import { useEffect, useMemo, useState } from 'react';
import { loadIndex, loadManifest, loadTrace } from '../api/artifacts';
import type { CaseIndex, Trace } from '../lib/contract.types';
import { forecastAllLive, normalPpf } from '../lib/liveEngine';
import { coverage, mase, seasonalNaiveMae } from '../lib/liveMetrics';
import { loadNLinearMeta, runNLinear } from '../lib/onnxRunner';
import { DEFAULT_KNOBS, generateSeries, type SyntheticKind, type SyntheticKnobs } from '../lib/synthetic';
import { WorkbenchChart, type ChartData, type ChartSeries } from '../render/WorkbenchChart';

const LEVELS = [0.1, 0.5, 0.9];

const ONNX_NAME = 'NLinear (ONNX)';
const COLORS: Record<string, string> = {
  SeasonalNaive: '#58a6ff', SES: '#bc8cff', Holt: '#f778ba', HoltWinters: '#ff9f1c', Theta: '#56d364',
  AutoETS: '#79c0ff', AutoTheta: '#d2a8ff', AutoARIMA: '#ffa657', LightGBM: '#7ee787', 'Chronos-Bolt': '#ff7b72',
  [ONNX_NAME]: '#e3b341',
};
const colorFor = (n: string) => COLORS[n] ?? `hsl(${(n.split('').reduce((a, c) => a + c.charCodeAt(0), 0) * 47) % 360} 70% 65%)`;

const KINDS: SyntheticKind[] = ['seasonal', 'trend_seasonal', 'intermittent', 'random_walk', 'white_noise'];
const fmt = (v: number, nd = 3) => (Number.isFinite(v) ? v.toFixed(nd) : '-');

interface Row { name: string; family: string; mase: number; coverage: number; }

export function AppPage() {
  const [mode, setMode] = useState<'synthetic' | 'baked'>('synthetic');
  const [knobs, setKnobs] = useState<SyntheticKnobs>(DEFAULT_KNOBS);
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [caseId, setCaseId] = useState('');
  const [trace, setTrace] = useState<Trace | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [err, setErr] = useState('');
  const [onnx, setOnnx] = useState<(ChartSeries & { mase: number; coverage: number }) | null>(null);

  useEffect(() => {
    loadIndex().then((ix) => { setIndex(ix); setCaseId(ix.cases[0]?.case_id ?? ''); }).catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (mode !== 'baked' || !caseId) return;
    loadManifest(caseId).then((m) => loadTrace(m.artifact.path)).then(setTrace).catch((e) => setErr(String(e)));
  }, [mode, caseId]);

  const synthetic = useMemo(() => {
    if (mode !== 'synthetic') return null;
    const y = generateSeries(knobs);
    const cut = Math.max(1, y.length - knobs.horizon);
    const history = y.slice(0, cut);
    const actual = y.slice(cut);
    const forecasts = forecastAllLive(history, knobs.seasonality, knobs.horizon, LEVELS);
    const scale = seasonalNaiveMae(history, knobs.seasonality);
    const rows: Row[] = forecasts.map((f) => ({
      name: f.name, family: 'classical',
      mase: mase(actual, f.point, scale), coverage: coverage(actual, f.lower, f.upper),
    }));
    const methods: ChartSeries[] = forecasts.map((f) => ({ name: f.name, color: colorFor(f.name), point: f.point, lower: f.lower, upper: f.upper }));
    return { history, actual, horizon: knobs.horizon, m: knobs.seasonality, methods, rows };
  }, [mode, knobs]);

  const baked = useMemo(() => {
    if (mode !== 'baked' || !trace) return null;
    const methods: ChartSeries[] = trace.methods.map((m) => ({ name: m.name, color: colorFor(m.name), point: m.point, lower: m.lower, upper: m.upper }));
    const rows: Row[] = trace.methods.map((m) => ({ name: m.name, family: m.family, mase: m.backtest.mase ?? NaN, coverage: m.backtest.coverage ?? NaN }));
    return { history: trace.history, actual: trace.actual, horizon: trace.horizon, m: trace.seasonality, methods, rows };
  }, [mode, trace]);

  const activeData = mode === 'synthetic' ? synthetic : baked;

  // ONNX live deep tier: run the NLinear model on the active history (async), add it as a live method.
  const sig = activeData ? `${mode}:${activeData.horizon}:${activeData.m}:${activeData.history.length}:${activeData.history.reduce((a, v) => a + v, 0).toFixed(1)}` : '';
  useEffect(() => {
    let cancelled = false;
    setOnnx(null);
    if (!activeData) return;
    const { history, actual, horizon, m } = activeData;
    (async () => {
      try {
        const meta = await loadNLinearMeta();
        if (horizon !== meta.horizon || history.length < meta.lookback) return;
        const { point, scale } = await runNLinear(history);
        const sigma = meta.sigma_norm * scale;
        const lower = point.map((p, i) => p + normalPpf(0.1) * sigma * Math.sqrt(i + 1));
        const upper = point.map((p, i) => p + normalPpf(0.9) * sigma * Math.sqrt(i + 1));
        const sc = seasonalNaiveMae(history, m);
        if (!cancelled) setOnnx({ name: ONNX_NAME, color: colorFor(ONNX_NAME), point, lower, upper, mase: mase(actual, point, sc), coverage: coverage(actual, lower, upper) });
      } catch {
        /* graceful: the ONNX method simply does not appear if the runtime/model fails to load */
      }
    })();
    return () => { cancelled = true; };
  }, [sig]); // eslint-disable-line react-hooks/exhaustive-deps

  const allMethods = activeData ? (onnx ? [...activeData.methods, onnx] : activeData.methods) : [];
  const allRows: Row[] = activeData
    ? (onnx ? [...activeData.rows, { name: onnx.name, family: 'deep', mase: onnx.mase, coverage: onnx.coverage }] : activeData.rows)
    : [];
  const chartData: ChartData | null = activeData
    ? { history: activeData.history, actual: activeData.actual, horizon: activeData.horizon, methods: allMethods.filter((mm) => !hidden.has(mm.name)) }
    : null;
  const rankedRows = [...allRows].sort((a, b) => (a.mase || Infinity) - (b.mase || Infinity));
  const best = rankedRows.find((r) => Number.isFinite(r.mase))?.name;

  const setK = (patch: Partial<SyntheticKnobs>) => setKnobs((k) => ({ ...k, ...patch }));
  const toggle = (name: string) => setHidden((h) => { const n = new Set(h); n.has(name) ? n.delete(name) : n.add(name); return n; });

  return (
    <div>
      {err && <p style={{ color: '#f85149' }}>error: {err}</p>}
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <section style={{ minWidth: 260, flex: '0 0 260px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div>
            <b>Source</b>
            <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
              <button onClick={() => setMode('synthetic')} style={tab(mode === 'synthetic')}>Synthetic (live)</button>
              <button onClick={() => setMode('baked')} style={tab(mode === 'baked')}>Baked case</button>
            </div>
          </div>
          {mode === 'synthetic' ? (
            <>
              <label>Pattern{' '}
                <select value={knobs.kind} onChange={(e) => setK({ kind: e.target.value as SyntheticKind })}>
                  {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
                </select>
              </label>
              {slider('length', knobs.n, 40, 400, 10, (v) => setK({ n: v }))}
              {slider('seasonality m', knobs.seasonality, 1, 48, 1, (v) => setK({ seasonality: v }))}
              {slider('horizon', knobs.horizon, 1, 48, 1, (v) => setK({ horizon: v }))}
              {slider('amplitude', knobs.amp, 0, 40, 1, (v) => setK({ amp: v }))}
              {slider('slope', knobs.slope, -1, 1, 0.05, (v) => setK({ slope: v }))}
              {slider('noise', knobs.noise, 0, 15, 0.5, (v) => setK({ noise: v }))}
              {slider('seed', knobs.seed, 0, 50, 1, (v) => setK({ seed: v }))}
            </>
          ) : (
            <label>Case{' '}
              <select value={caseId} onChange={(e) => setCaseId(e.target.value)}>
                {index?.cases.map((c) => <option key={c.case_id} value={c.case_id}>{c.case_id}</option>)}
              </select>
            </label>
          )}
          <div>
            <b>Methods</b>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 4 }}>
              {activeData?.methods.map((m) => (
                <label key={m.name} style={{ color: m.color, fontSize: 14 }}>
                  <input type="checkbox" checked={!hidden.has(m.name)} onChange={() => toggle(m.name)} /> {m.name}
                </label>
              ))}
            </div>
          </div>
        </section>

        <section style={{ flex: 1, minWidth: 420 }}>
          {chartData && <WorkbenchChart data={chartData} />}
          <p style={{ fontSize: 13, color: '#8b949e' }}>
            Grey = history, green dashed = held-out truth, coloured = each method's forecast with its prediction
            interval. {mode === 'synthetic'
              ? 'Classical methods computed live in your browser (parity-checked against the Python engine).'
              : 'Forecasts + metrics replayed from the offline backtest (classical + statistical + ML + foundation).'}
          </p>
          <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 14 }}>
            <thead>
              <tr>{['method', 'family', 'MASE', 'coverage'].map((h) => (
                <th key={h} style={{ textAlign: 'left', borderBottom: '1px solid #30363d', padding: '4px 8px' }}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {rankedRows.map((r) => (
                <tr key={r.name} style={{ fontWeight: r.name === best ? 700 : 400 }}>
                  <td style={{ padding: '4px 8px', color: colorFor(r.name) }}>{r.name}</td>
                  <td style={{ padding: '4px 8px' }}>{r.family}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(r.mase)}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(r.coverage, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: 13, color: '#8b949e' }}>
            MASE below 1 beats the seasonal-naive baseline. Best on this series: <b>{best ?? '-'}</b>. No method
            wins everywhere: seasonal cases favour the seasonal/foundation methods; a random walk or white noise
            cannot be beaten by much.
          </p>
        </section>
      </div>
    </div>
  );
}

function tab(on: boolean): React.CSSProperties {
  return { padding: '4px 10px', border: '1px solid #30363d', borderRadius: 6, background: on ? '#1f6feb' : 'transparent', color: on ? '#fff' : 'inherit', cursor: 'pointer' };
}

function slider(label: string, value: number, min: number, max: number, step: number, on: (v: number) => void) {
  return (
    <label style={{ fontSize: 14, display: 'block' }}>
      {label}: <b>{value}</b>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => on(Number(e.target.value))} style={{ width: '100%' }} />
    </label>
  );
}
