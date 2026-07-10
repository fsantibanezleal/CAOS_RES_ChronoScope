// The App: a per-case workbench in TWO HALVES behind a first-level source selector.
//  - UNDERSTAND: the analysis views (series + rolling stats, ACF/PACF, periodogram, distribution, memory)
//    computed LIVE in the browser for synthetic series, PLUS the baked heavy verdicts for committed cases.
//  - FORECAST: the ladder views (forecast + interval, ZOOM on the predicted zone, leaderboard, streaming
//    bench trajectories from the preqts prequential bake).
// Synthetic (LIVE): knobs regenerate the series; the TS classical engine + NLinear ONNX re-forecast
// instantly. Baked case (REPLAY): the full 18-method ladder + analysis + streaming artifacts, baked offline.
import { useEffect, useMemo, useState } from 'react';
import { SubTabs, useShellLang } from '@fasl-work/caos-app-shell';
import { loadAnalysis, loadIndex, loadManifest, loadStreaming, loadTrace } from '../api/artifacts';
import type { CaseIndex, CaseManifest, Trace } from '../lib/contract.types';
import { forecastAllLive, normalPpf } from '../lib/liveEngine';
import { coverage, mase, seasonalNaiveMae } from '../lib/liveMetrics';
import { loadNLinearMeta, runNLinear } from '../lib/onnxRunner';
import { DEFAULT_KNOBS, generateSeries, type SyntheticKind, type SyntheticKnobs } from '../lib/synthetic';
import { acf, bartlettBand, dfaAlpha, histogram, pacf, periodogram, rolling, summaryStats } from '../lib/tsAnalysis';
import { PanelBoundary } from '../render/PanelBoundary';
import { WorkbenchChart, type ChartData, type ChartSeries } from '../render/WorkbenchChart';

const LEVELS = [0.1, 0.5, 0.9];
const ONNX_NAME = 'NLinear (ONNX)';
const COLORS: Record<string, string> = {
  SeasonalNaive: '#58a6ff', SES: '#bc8cff', Holt: '#f778ba', HoltWinters: '#ff9f1c', Theta: '#56d364',
  AutoETS: '#79c0ff', AutoTheta: '#d2a8ff', AutoARIMA: '#ffa657', LightGBM: '#7ee787',
  'Chronos-Bolt': '#ff7b72', 'Chronos-2': '#ff9492', 'TimesFM-2.5': '#d29922',
  NLinear: '#e3b341', DLinear: '#f0883e', NHITS: '#a5d6ff',
  'NLinear (nf)': '#bf8700', 'DLinear (nf)': '#bd561d', 'NHITS (nf)': '#79c0ff',
  [ONNX_NAME]: '#e3b341',
};
const colorFor = (n: string) => COLORS[n] ?? `hsl(${(n.split('').reduce((a, c) => a + c.charCodeAt(0), 0) * 47) % 360} 70% 55%)`;
const KINDS: SyntheticKind[] = ['seasonal', 'trend_seasonal', 'intermittent', 'random_walk', 'white_noise'];
const fmt = (v: number | null | undefined, nd = 3) => (v == null || !Number.isFinite(v) ? '-' : v.toFixed(nd));

interface Row { name: string; family: string; mase: number; coverage: number; wql?: number; msis?: number; }

// ---------- small inline SVG plots (theme-aware via currentColor / tokens; static, no animation) ----------

function StemPlot({ values, band, title }: { values: number[]; band: number; title: string }) {
  const W = 380, H = 150, PAD = 24;
  const n = values.length;
  const sx = (i: number) => PAD + (i / Math.max(1, n - 1)) * (W - 2 * PAD);
  const sy = (v: number) => H / 2 - v * (H / 2 - PAD);
  return (
    <div className="cs-panel">
      <div className="cs-panel-t">{title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W }} role="img" aria-label={title}>
        <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="var(--color-border)" />
        <rect x={PAD} y={sy(band)} width={W - 2 * PAD} height={sy(-band) - sy(band)} fill="var(--color-accent)" opacity={0.08} />
        <line x1={PAD} y1={sy(band)} x2={W - PAD} y2={sy(band)} stroke="var(--color-accent)" strokeDasharray="4 3" opacity={0.5} />
        <line x1={PAD} y1={sy(-band)} x2={W - PAD} y2={sy(-band)} stroke="var(--color-accent)" strokeDasharray="4 3" opacity={0.5} />
        {values.map((v, i) => (
          <g key={i}>
            <line x1={sx(i)} y1={H / 2} x2={sx(i)} y2={sy(Math.max(-1, Math.min(1, v)))}
              stroke={Math.abs(v) > band && i > 0 ? 'var(--color-accent)' : 'var(--color-fg-faint)'} strokeWidth={2} />
          </g>
        ))}
      </svg>
    </div>
  );
}

function LinePlot({ xs, series, title, subtitle, refLine }: {
  xs: number[]; series: { label: string; values: (number | null)[]; color: string }[];
  title: string; subtitle?: string; refLine?: number;
}) {
  const W = 480, H = 170, PAD = 30;
  const finite = series.flatMap((s) => s.values.filter((v): v is number => v != null && Number.isFinite(v)));
  if (!finite.length) return null;
  const lo = Math.min(...finite, refLine ?? Infinity);
  const hi = Math.max(...finite, refLine ?? -Infinity);
  const sx = (i: number) => PAD + (i / Math.max(1, xs.length - 1)) * (W - 2 * PAD);
  const sy = (v: number) => H - PAD - ((v - lo) / Math.max(1e-9, hi - lo)) * (H - 2 * PAD);
  const path = (vals: (number | null)[]) => {
    let d = ''; let pen = false;
    vals.forEach((v, i) => {
      if (v == null || !Number.isFinite(v)) { pen = false; return; }
      d += `${pen ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`; pen = true;
    });
    return d;
  };
  return (
    <div className="cs-panel">
      <div className="cs-panel-t">{title}</div>
      {subtitle && <div className="cs-panel-sub">{subtitle}</div>}
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: W }} role="img" aria-label={title}>
        {refLine != null && <line x1={PAD} y1={sy(refLine)} x2={W - PAD} y2={sy(refLine)} stroke="var(--color-fg-faint)" strokeDasharray="5 4" />}
        {series.map((s) => <path key={s.label} d={path(s.values)} fill="none" stroke={s.color} strokeWidth={1.6} />)}
      </svg>
      <div className="cs-legend" style={{ flexDirection: 'row', gap: '0.8rem', flexWrap: 'wrap' }}>
        {series.map((s) => <label key={s.label}><span className="swatch" style={{ background: s.color }} /> {s.label}</label>)}
      </div>
    </div>
  );
}

// ---------------------------------------- the page ----------------------------------------

export default function AppPage() {
  const es = useShellLang() === 'es';
  const [mode, setMode] = useState<'synthetic' | 'baked'>('baked');
  const [knobs, setKnobs] = useState<SyntheticKnobs>(DEFAULT_KNOBS);
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [caseId, setCaseId] = useState('');
  const [manifest, setManifest] = useState<CaseManifest | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [analysis, setAnalysis] = useState<Record<string, any> | null>(null);
  const [streaming, setStreaming] = useState<Record<string, any> | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [err, setErr] = useState('');
  const [onnx, setOnnx] = useState<(ChartSeries & { mase: number; coverage: number }) | null>(null);

  useEffect(() => {
    loadIndex().then((ix) => { setIndex(ix); setCaseId(ix.cases[0]?.case_id ?? ''); }).catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (mode !== 'baked' || !caseId) return;
    setAnalysis(null); setStreaming(null); setTrace(null); setManifest(null);
    loadManifest(caseId).then(async (m) => {
      setManifest(m);
      setTrace(await loadTrace(m.artifact.path));
      if (m.analysis_artifact) setAnalysis(await loadAnalysis(m.analysis_artifact.path));
      if (m.streaming_artifact) setStreaming(await loadStreaming(m.streaming_artifact.path));
    }).catch((e) => setErr(String(e)));
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
    const methods: ChartSeries[] = trace.methods
      .filter((m) => m.point && m.lower && m.upper)
      .map((m) => ({ name: m.name, color: colorFor(m.name), point: m.point!, lower: m.lower!, upper: m.upper! }));
    const rows: Row[] = trace.methods.map((m) => ({
      name: m.name, family: m.family,
      mase: m.backtest.mase ?? NaN, coverage: m.backtest.coverage ?? NaN,
      wql: m.backtest.wql ?? NaN, msis: m.backtest.msis ?? NaN,
    }));
    return { history: trace.history, actual: trace.actual, horizon: trace.horizon, m: trace.seasonality, methods, rows };
  }, [mode, trace]);

  const activeData = mode === 'synthetic' ? synthetic : baked;

  // ONNX live deep tier on the active history (the LIVE learned model).
  const sig = activeData ? `${mode}:${activeData.horizon}:${activeData.m}:${activeData.history.length}:${activeData.history.reduce((a, v) => a + v, 0).toFixed(1)}` : '';
  useEffect(() => {
    let cancelled = false;
    setOnnx(null);
    if (!activeData || !activeData.history.length) return;
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
      } catch { /* graceful: the live ONNX method simply does not appear */ }
    })();
    return () => { cancelled = true; };
  }, [sig]); // eslint-disable-line react-hooks/exhaustive-deps

  const allMethods = activeData ? (onnx ? [...activeData.methods, onnx] : activeData.methods) : [];
  const allRows: Row[] = activeData
    ? (onnx ? [...activeData.rows, { name: onnx.name, family: 'deep (live)', mase: onnx.mase, coverage: onnx.coverage }] : activeData.rows)
    : [];
  const visibleMethods = allMethods.filter((mm) => !hidden.has(mm.name));
  const rankedRows = [...allRows].sort((a, b) => (Number.isFinite(a.mase) ? a.mase : Infinity) - (Number.isFinite(b.mase) ? b.mase : Infinity));
  const best = rankedRows.find((r) => Number.isFinite(r.mase))?.name;

  const setK = (patch: Partial<SyntheticKnobs>) => setKnobs((k) => ({ ...k, ...patch }));
  const toggle = (name: string) => setHidden((h) => { const n = new Set(h); if (n.has(name)) n.delete(name); else n.add(name); return n; });

  // ---------------- UNDERSTAND half (live analysis on the active series + baked verdicts) ----------------

  // Each live diagnostic degrades to its empty value instead of crashing the page on a pathological
  // series (the per-tab PanelBoundary is the second layer; this is the first).
  const safe = <T,>(f: () => T, fb: T): T => { try { return f(); } catch { return fb; } };
  const fullSeries = activeData ? [...activeData.history, ...activeData.actual] : [];
  const stats = fullSeries.length ? safe(() => summaryStats(fullSeries), null) : null;
  const nlags = Math.min(48, Math.max(10, Math.floor(fullSeries.length / 4)));
  const acfVals = fullSeries.length > 8 ? safe(() => acf(fullSeries, nlags), []) : [];
  const pacfVals = fullSeries.length > 8 ? safe(() => pacf(fullSeries, Math.min(nlags, 24)), []) : [];
  const pgram = fullSeries.length > 16 ? safe(() => periodogram(fullSeries), null) : null;
  const roll = fullSeries.length > 8 ? safe(() => rolling(fullSeries, Math.max(5, Math.floor(fullSeries.length / 12))), null) : null;
  const alpha = fullSeries.length >= 64 ? safe(() => dfaAlpha(fullSeries), null) : null;
  const hist = fullSeries.length ? safe(() => histogram(fullSeries), null) : null;
  const band = bartlettBand(fullSeries.length);
  const bakedStationarity = analysis && (analysis as any).stationarity;
  const bakedVolatility = analysis && (analysis as any).volatility;
  const bakedNonlinear = analysis && (analysis as any).nonlinear;
  const bakedFractal = analysis && (analysis as any).fractal;

  const understandSeries = (
    <div className="cs-main">
      {roll && (
        <LinePlot
          xs={fullSeries.map((_, i) => i)}
          series={[
            { label: es ? 'serie' : 'series', values: fullSeries, color: 'var(--color-fg-faint)' },
            { label: es ? 'media móvil' : 'rolling mean', values: roll.mean, color: 'var(--color-accent)' },
            { label: es ? 'desv. móvil' : 'rolling std', values: roll.std, color: '#d29922' },
          ]}
          title={es ? 'Serie + estadísticos móviles' : 'Series + rolling statistics'}
          subtitle={es ? 'Una media móvil que deriva = tendencia/quiebre; una desviación móvil que respira = heterocedasticidad.' : 'A drifting rolling mean = trend/break; a breathing rolling std = heteroscedasticity.'}
        />
      )}
      <div className="cs-kpis">
        <div className="cs-kpi"><div className="cs-kpi-v">{fmt(stats?.mean, 2)}</div><div className="cs-kpi-l">{es ? 'media' : 'mean'}</div></div>
        <div className="cs-kpi"><div className="cs-kpi-v">{fmt(stats?.std, 2)}</div><div className="cs-kpi-l">{es ? 'desv. est.' : 'std'}</div></div>
        <div className="cs-kpi"><div className="cs-kpi-v">{fmt(stats?.skewness, 2)}</div><div className="cs-kpi-l">{es ? 'asimetría' : 'skewness'}</div></div>
        <div className="cs-kpi"><div className="cs-kpi-v">{fmt(stats?.kurtosisExcess, 2)}</div><div className="cs-kpi-l">{es ? 'curtosis exc.' : 'excess kurtosis'}</div></div>
      </div>
      {hist && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'Distribución' : 'Distribution'}</div>
          <svg viewBox="0 0 380 120" width="100%" style={{ maxWidth: 380 }} role="img" aria-label="histogram">
            {hist.counts.map((c, i) => {
              const max = Math.max(...hist.counts, 1);
              const w = 340 / hist.counts.length;
              return <rect key={i} x={20 + i * w} y={110 - (c / max) * 100} width={w - 1} height={(c / max) * 100} fill="var(--color-accent)" opacity={0.55} />;
            })}
          </svg>
          <div className="cs-panel-sub">{es
            ? `curtosis en exceso ${fmt(stats?.kurtosisExcess, 2)}: > 0 = colas más pesadas que la normal (los intervalos gaussianos sub-cubren).`
            : `excess kurtosis ${fmt(stats?.kurtosisExcess, 2)}: > 0 = heavier tails than normal (Gaussian intervals under-cover).`}</div>
        </div>
      )}
    </div>
  );

  const understandStructure = (
    <div className="cs-main">
      {acfVals.length > 0 && <StemPlot values={acfVals} band={band} title={`ACF (${es ? 'banda' : 'band'} ±${band.toFixed(3)})`} />}
      {pacfVals.length > 0 && <StemPlot values={pacfVals} band={band} title="PACF (Durbin-Levinson)" />}
      <div className="cs-panel">
        <div className="cs-panel-t">{es ? 'Lectura Box-Jenkins' : 'Box-Jenkins read'}</div>
        <p className="cs-panel-sub">{es
          ? 'ACF que se corta tras q: MA(q). PACF que se corta tras p: AR(p). Ambas decaen: ARMA. Todo dentro de la banda: ruido blanco (nada que modelar). Decaimiento LENTO (hiperbólico): memoria larga, mira el panel de memoria.'
          : 'ACF cutting off after q: MA(q). PACF cutting off after p: AR(p). Both tailing off: ARMA. Everything inside the band: white noise (nothing to model). SLOW (hyperbolic) decay: long memory, see the memory panel.'}</p>
      </div>
      {pgram && (
        <LinePlot
          xs={pgram.periods.map((_, i) => i)}
          series={[{ label: es ? 'potencia' : 'power', values: pgram.power, color: 'var(--color-accent)' }]}
          title={es ? 'Periodograma (potencia por período)' : 'Periodogram (power per period)'}
          subtitle={`${es ? 'período dominante' : 'dominant period'}: ${fmt(pgram.dominantPeriod, 1)} ${es ? '(m declarado' : '(declared m'}: ${activeData?.m ?? '-'})`}
        />
      )}
    </div>
  );

  const understandVerdicts = (
    <div className="cs-main">
      <div className="cs-panel">
        <div className="cs-panel-t">{es ? 'Memoria y escalamiento (en vivo)' : 'Memory and scaling (live)'}</div>
        <p>DFA α = <b>{fmt(alpha, 3)}</b>{' '}
          {alpha != null && (
            <span className={`cs-badge ${Math.abs(alpha - 0.5) < 0.1 ? 'ok' : 'warn'}`}>
              {alpha < 0.45 ? (es ? 'anti-persistente' : 'anti-persistent')
                : alpha > 1.2 ? (es ? 'no estacionaria (tipo caminata)' : 'non-stationary (walk-like)')
                : alpha > 0.55 ? (es ? 'memoria persistente' : 'persistent memory')
                : (es ? 'sin memoria larga (~ruido)' : 'no long memory (~noise)')}
            </span>
          )}
        </p>
        <p className="cs-panel-sub">{es
          ? 'α~0.5 ruido blanco · ~1 ruido 1/f · ~1.5 caminata aleatoria. Para fGn H=α; el vínculo ARFIMA es d = H − 0.5.'
          : 'α~0.5 white noise · ~1 pink noise · ~1.5 random walk. For fGn H=α; the ARFIMA link is d = H − 0.5.'}</p>
      </div>
      {mode === 'baked' && bakedStationarity && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'Estacionariedad (horneado offline)' : 'Stationarity (baked offline)'} <span className="cs-badge replay">replay</span></div>
          <table className="cs-table">
            <thead><tr><th>test</th><th>stat</th><th>p</th><th>{es ? 'veredicto' : 'verdict'}</th></tr></thead>
            <tbody>
              {(bakedStationarity.tests ?? []).map((t: any) => (
                <tr key={t.name}>
                  <td>{t.name}</td><td>{fmt(t.stat, 3)}</td><td>{fmt(t.pvalue, 4)}</td>
                  <td><span className={`cs-badge ${t.stationary ? 'ok' : 'warn'}`}>{t.stationary ? (es ? 'estacionaria' : 'stationary') : (es ? 'no estacionaria' : 'non-stationary')}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="cs-panel-sub">{bakedStationarity.combined_verdict} · d = {bakedStationarity.recommended_d}</p>
        </div>
      )}
      {mode === 'baked' && bakedVolatility && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'Volatilidad (horneado)' : 'Volatility (baked)'} <span className="cs-badge replay">replay</span></div>
          <p>ARCH-LM p = <b>{fmt(bakedVolatility.arch_lm?.lm_pvalue, 4)}</b>{' '}
            <span className={`cs-badge ${bakedVolatility.arch_lm?.has_arch ? 'warn' : 'ok'}`}>
              {bakedVolatility.arch_lm?.has_arch ? (es ? 'varianza agrupada (GARCH ajustado)' : 'clustered variance (GARCH fitted)') : (es ? 'homocedástica' : 'homoscedastic')}
            </span>
            {bakedVolatility.garch?.persistence != null && <> · {es ? 'persistencia' : 'persistence'} {fmt(bakedVolatility.garch.persistence, 3)}</>}
          </p>
        </div>
      )}
      {mode === 'baked' && (bakedNonlinear || bakedFractal) && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'No linealidad, fractales y caos (horneado)' : 'Nonlinearity, fractals and chaos (baked)'} <span className="cs-badge replay">replay</span></div>
          {bakedFractal && <p>Hurst R/S = <b>{fmt(bakedFractal.hurst?.rs, 3)}</b> · DFA α = <b>{fmt(bakedFractal.hurst?.dfa_alpha, 3)}</b> · {bakedFractal.hurst?.interpretation}</p>}
          {bakedNonlinear && !bakedNonlinear.skipped && (
            <p>0-1 K = <b>{fmt(bakedNonlinear.zero_one_K, 3)}</b> · λ₁ = <b>{fmt(bakedNonlinear.largest_lyapunov, 4)}</b>{' '}
              <span className={`cs-badge ${bakedNonlinear.likely_chaotic ? 'warn' : 'ok'}`}>
                {bakedNonlinear.likely_chaotic ? (es ? 'caótica (gate de surrogates aprobado)' : 'chaotic (surrogate gate passed)') : (es ? 'sin caos confirmado' : 'no confirmed chaos')}
              </span></p>
          )}
          {bakedNonlinear?.skipped && <p className="cs-panel-sub">{es ? 'panel no lineal omitido honestamente (serie corta)' : 'nonlinear panel honestly skipped (short series)'}</p>}
        </div>
      )}
      {mode === 'synthetic' && (
        <p className="cs-panel-sub">{es
          ? 'Los veredictos pesados (ADF/KPSS, GARCH, surrogates de caos) corren OFFLINE y aparecen al elegir un caso horneado; el resto de este panel es en vivo.'
          : 'The heavy verdicts (ADF/KPSS, GARCH, chaos surrogates) run OFFLINE and appear when you pick a baked case; the rest of this panel is live.'}</p>
      )}
    </div>
  );

  // ---------------- FORECAST half ----------------

  const chartData: ChartData | null = activeData
    ? { history: activeData.history, actual: activeData.actual, horizon: activeData.horizon, methods: visibleMethods }
    : null;

  // ZOOM view: the last 2 seasons of history + the horizon only.
  const zoomData: ChartData | null = useMemo(() => {
    if (!activeData) return null;
    const keep = Math.min(activeData.history.length, Math.max(2 * activeData.m, 24));
    return {
      history: activeData.history.slice(-keep),
      actual: activeData.actual,
      horizon: activeData.horizon,
      methods: visibleMethods,
    };
  }, [activeData, visibleMethods]);

  const forecastFull = (
    <div className="cs-main">
      {chartData && chartData.history.length > 0
        ? <div className="cs-panel"><WorkbenchChart data={chartData} /></div>
        : <p className="cs-panel-sub">{es ? 'fuente con licencia solo-local: la serie no se publica; ver la tabla de métricas y el banco de streaming.' : 'local-only-licensed source: the series is not published; see the metrics table and the streaming bench.'}</p>}
      <p className="cs-panel-sub">{es
        ? 'Gris = historia, verde discontinuo = verdad reservada, color = pronóstico + intervalo por método. '
        : 'Grey = history, dashed green = held-out truth, colour = each method\'s forecast + interval. '}
        {mode === 'synthetic'
          ? (es ? 'Clásicos + ONNX computados EN VIVO en tu navegador (paridad verificada con el pipeline).' : 'Classical + ONNX computed LIVE in your browser (parity-checked against the pipeline).')
          : (es ? 'Escalera completa (18 métodos) del backtest horneado offline.' : 'The full 18-method ladder from the offline-baked backtest.')}</p>
    </div>
  );

  const forecastZoom = (
    <div className="cs-main">
      {zoomData && zoomData.history.length > 0 && <div className="cs-panel"><WorkbenchChart data={zoomData} /></div>}
      <p className="cs-panel-sub">{es
        ? 'ZOOM en la zona predicha: solo las últimas ~2 temporadas + el horizonte, para leer los intervalos y el error paso a paso (el cursor lee cada serie).'
        : 'ZOOM on the predicted zone: only the last ~2 seasons + the horizon, to read the intervals and per-step error (the cursor reads out every series).'}</p>
    </div>
  );

  const leaderboard = (
    <div className="cs-main">
      <div className="cs-panel cs-chart">
        <table className="cs-table">
          <thead><tr><th>{es ? 'método' : 'method'}</th><th>{es ? 'familia' : 'family'}</th><th>MASE</th><th>WQL</th><th>MSIS</th><th>{es ? 'cobertura' : 'coverage'}</th></tr></thead>
          <tbody>
            {rankedRows.map((r) => (
              <tr key={r.name} className={r.name === best ? 'best' : undefined}>
                <td style={{ color: colorFor(r.name) }}>{r.name}</td>
                <td>{r.family}</td>
                <td>{fmt(r.mase)}</td>
                <td>{fmt(r.wql)}</td>
                <td>{fmt(r.msis, 2)}</td>
                <td>{fmt(r.coverage, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cs-panel-sub">{es
        ? `MASE < 1 le gana al naive estacional; WQL puntúa los cuantiles; MSIS puntúa el intervalo (ancho + 2/α por cada falla, escalado como MASE): un intervalo angosto que falla no puede verse bien. Mejor en esta serie: ${best ?? '-'}. Ningún método gana en todas partes; en los controles, ganar por mucho es una bandera roja.`
        : `MASE < 1 beats the seasonal naive; WQL scores the quantiles; MSIS prices the interval (width + 2/α per miss, scaled like MASE): a narrow interval that misses cannot look good. Best on this series: ${best ?? '-'}. No method wins everywhere; on the controls, winning big is a red flag.`}</p>
    </div>
  );

  const horizonRows = mode === 'baked' && trace
    ? trace.methods
        .filter((m) => !hidden.has(m.name) && (m.backtest.per_horizon_scaled ?? []).some((v) => v != null && Number.isFinite(v)))
        .map((m) => ({ label: m.name, values: (m.backtest.per_horizon_scaled ?? []) as (number | null)[], color: colorFor(m.name) }))
    : [];
  const horizonPanel = (
    <div className="cs-main">
      {mode !== 'baked' && <p className="cs-panel-sub">{es
        ? 'La curva por horizonte se hornea offline por caso (media sobre todos los cortes del backtest): elige un caso horneado.'
        : 'The per-horizon curve is baked offline per case (mean over all backtest cutoffs): pick a baked case.'}</p>}
      {mode === 'baked' && trace && horizonRows.length > 0 && (
        <>
          <LinePlot
            xs={Array.from({ length: trace.horizon }, (_, i) => i + 1)}
            series={horizonRows}
            refLine={1}
            title={es ? 'Crecimiento del error por horizonte (MASE por paso)' : 'Error growth by lead time (per-lead MASE)'}
            subtitle={es
              ? 'media de |error| en el paso h sobre todos los cortes, escalada por el naive estacional; 1.0 = tan malo como el naive en ese paso.'
              : 'mean |error| at lead h over all backtest cutoffs, scaled by the seasonal naive; 1.0 = as wrong as the naive at that lead.'}
          />
          <p className="cs-panel-sub">{es
            ? 'La FORMA es el diagnóstico: meseta = reversión a la media (el error satura), crecimiento tipo raíz = caminata aleatoria (incertidumbre difusiva), crecimiento exponencial que satura = caos determinista (horizonte de Lyapunov). Desmarca métodos en la leyenda para aislar familias.'
            : 'The SHAPE is the diagnosis: a plateau = mean reversion (error saturates), square-root growth = a random walk (diffusive uncertainty), exponential growth that saturates = deterministic chaos (the Lyapunov horizon). Untick methods in the legend to isolate families.'}</p>
        </>
      )}
      {mode === 'baked' && trace && horizonRows.length === 0 && (
        <p className="cs-panel-sub">{es
          ? 'Este trace no trae curvas por horizonte (artefacto anterior a v2): re-hornea el caso.'
          : 'This trace carries no per-horizon curves (a pre-v2 artifact): re-bake the case.'}</p>
      )}
    </div>
  );

  const streamingBench = (
    <div className="cs-main">
      {mode !== 'baked' && <p className="cs-panel-sub">{es ? 'El banco de streaming se hornea offline por caso: elige un caso horneado.' : 'The streaming bench is baked offline per case: pick a baked case.'}</p>}
      {mode === 'baked' && streaming && (() => {
        const meths = (streaming as any).methods ?? {};
        const names = Object.keys(meths).filter((k) => !meths[k].error);
        const colors: Record<string, string> = { SeasonalNaive: '#58a6ff', Theta: '#56d364', 'Theta+ACI': '#d29922', 'Theta+PID': '#ff7b72' };
        const n = Math.max(...names.map((k) => meths[k].n_steps ?? 0), 0);
        const xs = Array.from({ length: n }, (_, i) => i);
        return (
          <>
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: k, values: meths[k].rolling_coverage ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'Cobertura rodante vs nominal (el resultado central)' : 'Rolling coverage vs nominal (the central result)'}
              subtitle={es
                ? `objetivo ${(streaming as any).nominal_coverage}: los calibrados (ACI/PID) deben pegarse a la línea; el crudo deriva cuando el régimen cambia.`
                : `target ${(streaming as any).nominal_coverage}: the calibrated variants (ACI/PID) should hug the line; the raw one drifts when the regime shifts.`}
              refLine={(streaming as any).nominal_coverage}
            />
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: k, values: meths[k].rolling_mase ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'MASE rodante (habilidad sobre el stream)' : 'Rolling MASE (skill over the stream)'}
            />
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: k, values: meths[k].cumulative_cost_ms ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'Costo de cómputo acumulado (ms)' : 'Cumulative compute cost (ms)'}
              subtitle={es ? 'la historia del costo-por-paso: la calibración añade casi nada sobre el pronosticador base.' : 'the cost-per-step story: calibration adds almost nothing over the base forecaster.'}
            />
            <p className="cs-panel-sub">{es
              ? 'Evaluación prequential (Dawid 1984) con preqts, NUESTRO paquete PyPI: predecir, luego observar, luego actualizar, con estado acarreado. Ningún harness público hace esto con política de covariables; es la pieza nueva del atlas.'
              : 'Prequential evaluation (Dawid 1984) with preqts, OUR PyPI package: predict, then observe, then update, state carried. No public harness does this with a covariate policy; it is the atlas\'s novel piece.'}</p>
          </>
        );
      })()}
    </div>
  );

  // ---------------- layout ----------------

  return (
    <section className="page-body">
      {err && <p style={{ color: 'var(--color-danger, #f85149)' }}>error: {err}</p>}
      <div className="cs-layout">
        <aside className="cs-controls">
          <div className="cs-panel">
            <div className="cs-panel-t">{es ? 'Fuente' : 'Source'}</div>
            <div className="cs-chips">
              <button className={`chip ${mode === 'baked' ? 'on' : ''}`} onClick={() => setMode('baked')}>{es ? 'Caso horneado' : 'Baked case'} </button>
              <button className={`chip ${mode === 'synthetic' ? 'on' : ''}`} onClick={() => setMode('synthetic')}>{es ? 'Sintética (en vivo)' : 'Synthetic (live)'}</button>
            </div>
            {mode === 'baked' ? (
              <div className="cs-ctl" style={{ marginTop: 8 }}>
                <span>{es ? 'caso' : 'case'}</span>
                <select className="cs-sel" value={caseId} onChange={(e) => setCaseId(e.target.value)}>
                  {index?.cases.map((c) => <option key={c.case_id} value={c.case_id}>{c.case_id}</option>)}
                </select>
                {manifest && <span className="cs-panel-sub">{manifest.category} · seed {manifest.seed} · <span className={`cs-badge ${manifest.provenance.public_artifact_ok ? 'real' : 'warn'}`}>{manifest.provenance.license}</span></span>}
              </div>
            ) : (
              <>
                <div className="cs-ctl" style={{ marginTop: 8 }}>
                  <span>{es ? 'patrón' : 'pattern'}</span>
                  <select className="cs-sel" value={knobs.kind} onChange={(e) => setK({ kind: e.target.value as SyntheticKind })}>
                    {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
                  </select>
                </div>
                {([
                  ['n', knobs.n, 40, 400, 10, (v: number) => setK({ n: v })],
                  ['m', knobs.seasonality, 1, 48, 1, (v: number) => setK({ seasonality: v })],
                  ['horizon', knobs.horizon, 1, 48, 1, (v: number) => setK({ horizon: v })],
                  ['amplitude', knobs.amp, 0, 40, 1, (v: number) => setK({ amp: v })],
                  ['slope', knobs.slope, -1, 1, 0.05, (v: number) => setK({ slope: v })],
                  ['noise', knobs.noise, 0, 15, 0.5, (v: number) => setK({ noise: v })],
                  ['seed', knobs.seed, 0, 50, 1, (v: number) => setK({ seed: v })],
                ] as [string, number, number, number, number, (v: number) => void][]).map(([label, value, min, max, step, on]) => (
                  <label key={label} className="cs-ctl">
                    <span className="cs-ctl-row"><span>{label}</span><b>{value}</b></span>
                    <input className="range" type="range" min={min} max={max} step={step} value={value} onChange={(e) => on(Number(e.target.value))} />
                  </label>
                ))}
              </>
            )}
          </div>
          <div className="cs-panel">
            <div className="cs-panel-t">{es ? 'Métodos' : 'Methods'}</div>
            <div className="cs-legend">
              {allMethods.map((m) => (
                <label key={m.name}>
                  <input type="checkbox" checked={!hidden.has(m.name)} onChange={() => toggle(m.name)} />
                  <span className="swatch" style={{ background: m.color }} /> {m.name}
                </label>
              ))}
            </div>
          </div>
        </aside>

        <main className="cs-main">
          <SubTabs
            ariaLabel="workbench views"
            tabs={[
              { id: 'series', label: es ? 'Serie' : 'Series', content: <PanelBoundary label="Series" es={es}>{understandSeries}</PanelBoundary> },
              { id: 'structure', label: es ? 'Estructura (ACF·espectro)' : 'Structure (ACF·spectrum)', content: <PanelBoundary label="Structure" es={es}>{understandStructure}</PanelBoundary> },
              { id: 'verdicts', label: es ? 'Veredictos (tests)' : 'Verdicts (tests)', content: <PanelBoundary label="Verdicts" es={es}>{understandVerdicts}</PanelBoundary> },
              { id: 'forecast', label: es ? 'Pronóstico' : 'Forecast', content: <PanelBoundary label="Forecast" es={es}>{forecastFull}</PanelBoundary> },
              { id: 'zoom', label: 'Zoom', content: <PanelBoundary label="Zoom" es={es}>{forecastZoom}</PanelBoundary> },
              { id: 'horizon', label: es ? 'Horizonte' : 'Horizon', content: <PanelBoundary label="Horizon" es={es}>{horizonPanel}</PanelBoundary> },
              { id: 'leaderboard', label: es ? 'Tabla' : 'Leaderboard', content: <PanelBoundary label="Leaderboard" es={es}>{leaderboard}</PanelBoundary> },
              { id: 'streaming', label: 'Streaming', content: <PanelBoundary label="Streaming" es={es}>{streamingBench}</PanelBoundary> },
            ]}
          />
        </main>
      </div>
    </section>
  );
}
