// The App: a per-case workbench in TWO HALVES behind a first-level source selector.
//  - UNDERSTAND: the analysis views (series + rolling stats, ACF/PACF, periodogram, distribution, memory)
//    computed LIVE in the browser for synthetic series, PLUS the baked heavy verdicts for committed cases.
//  - FORECAST: the ladder views (forecast + interval, ZOOM on the predicted zone, leaderboard, streaming
//    bench trajectories from the preqts prequential bake).
// Synthetic (LIVE): knobs regenerate the series; the TS classical engine + NLinear ONNX re-forecast
// instantly. Baked case (REPLAY): the full 19-method ladder + analysis + streaming artifacts, baked offline.
import { useEffect, useMemo, useState } from 'react';
import { formatNumber, TabGroups, useShellLang } from '@fasl-work/caos-app-shell';
import { loadAnalysis, loadIndex, loadManifest, loadReevaluation, loadStreaming, loadTrace } from '../api/artifacts';
import type { CaseIndex, CaseManifest, Trace } from '../lib/contract.types';
import type { Reevaluation } from '../lib/reevaluation.types';
import { methodColor } from '../lib/methodColors';
import { forecastAllLive } from '../lib/liveEngine';
import { coverage, mase, seasonalNaiveMae } from '../lib/liveMetrics';
import { useNLinearForecast } from '../lib/useNLinearForecast';
import { BROWSER_LINEAR_NAME } from '../lib/calibratedLinearIntervals';
import { DEFAULT_KNOBS, generateSeries, type SyntheticKind, type SyntheticKnobs } from '../lib/synthetic';
import { acf, bartlettBand, decompose, dfaAlpha, histogram, pacf, periodogram, qqPairs, rolling, summaryStats } from '../lib/tsAnalysis';
import { PanelBoundary } from '../render/PanelBoundary';
import { SeriesLegend, type LegendItem, type LegendMetric } from '../render/SeriesLegend';
import { UPlotChart, type RefLine, type USeries } from '../render/UPlotChart';
import { SequenceDiagnostics, type SequenceData } from '../render/SequenceDiagnostics';

// a method's forecast (point + interval), shared by synthetic (live) + baked (replay)
interface ChartSeries { name: string; color: string; point: number[]; lower: number[]; upper: number[]; }

const LEVELS = [0.1, 0.5, 0.9];
const ONNX_NAME = BROWSER_LINEAR_NAME;
const ATLAS_NAV_KEY = 'chronoscope-atlas-nav';
type AtlasNav = { group: 'understand' | 'forecast'; tab: string };
const ATLAS_TABS: Record<AtlasNav['group'], string[]> = {
  understand: ['series', 'structure', 'decompose', 'patterns', 'verdicts'],
  forecast: ['forecast', 'residuals', 'leaderboard', 'streaming'],
};
const colorFor = methodColor;
const KINDS: SyntheticKind[] = ['seasonal', 'trend_seasonal', 'intermittent', 'random_walk', 'white_noise'];

// Safe deep-getter for the baked analysis.json (chronoscope.analysis/v1); null on any missing link.
function dig(o: unknown, ...path: (string | number)[]): number | null {
  let cur: unknown = o;
  for (const k of path) { if (cur == null || typeof cur !== 'object') return null; cur = (cur as Record<string, unknown>)[k]; }
  return typeof cur === 'number' && Number.isFinite(cur) ? cur : null;
}

// group the 15 cases for the picker (Synthetic / Real / Control) from the case-id prefix.
function caseGroup(id: string): 'Real' | 'Control' | 'Synthetic' {
  if (id.startsWith('REAL_')) return 'Real';
  if (id.startsWith('CTRL_')) return 'Control';
  return 'Synthetic';
}

interface Row { name: string; family: string; mase: number; coverage: number; wql?: number; msis?: number; }

// ---------- interactive chart panels (uPlot: zoom/pan/crosshair/brush/reset, per-series readout) ----------

// ACF / PACF as interactive stems (uPlot bars) with the Bartlett significance band as two ref lines.
function StemPlot({ values, band, title }: { values: number[]; band: number; title: string }) {
  const xs = values.map((_, i) => i);
  const series: USeries[] = [{ label: 'r_k', values, color: 'var(--color-accent)', bars: true }];
  const refs: RefLine[] = [
    { y: band, color: 'var(--color-accent)', dash: [4, 3] },
    { y: -band, color: 'var(--color-accent)', dash: [4, 3] },
    { y: 0 },
  ];
  return (
    <div className="cs-panel">
      <div className="cs-panel-t">{title}</div>
      <UPlotChart xs={xs} series={series} refLines={refs} height={200} xLabel="lag" ariaSummary={title} precision={3} />
    </div>
  );
}

function LinePlot({ xs, series, title, subtitle, refLine, refLabel, height, xMarks = [] }: {
  xs: number[]; series: { label: string; values: (number | null)[]; color: string; dash?: number[] }[];
  title: string; subtitle?: string; refLine?: number; refLabel?: string; height?: number; xMarks?: RefLine[];
}) {
  const any = series.some((s) => s.values.some((v) => v != null && Number.isFinite(v)));
  if (!any) return null;
  const uSeries: USeries[] = series.map((s) => ({ label: s.label, values: s.values, color: s.color, dash: s.dash, width: 1.7 }));
  const refs: RefLine[] = [...xMarks, ...(refLine != null ? [{ y: refLine, label: refLabel, dash: [5, 4] }] : [])];
  return (
    <div className="cs-panel">
      <div className="cs-panel-t">{title}</div>
      {subtitle && <div className="cs-panel-sub">{subtitle}</div>}
      <UPlotChart xs={xs} series={uSeries} refLines={refs} height={height ?? 260} ariaSummary={title} />
    </div>
  );
}

// ---------------------------------------- the page ----------------------------------------

export default function AppPage() {
  const es = useShellLang() === 'es';
  const fmt = (v: number | null | undefined, nd = 3) => formatNumber(v, es ? 'es' : 'en', { digits: nd });
  const [nav, setNav] = useState<AtlasNav>(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(ATLAS_NAV_KEY) ?? 'null') as Partial<AtlasNav> | null;
      if (saved && (saved.group === 'understand' || saved.group === 'forecast') &&
          typeof saved.tab === 'string' && ATLAS_TABS[saved.group].includes(saved.tab)) {
        return { group: saved.group, tab: saved.tab };
      }
    } catch { /* use the first view when storage is unavailable or malformed */ }
    return { group: 'understand', tab: 'series' };
  });
  useEffect(() => {
    try { sessionStorage.setItem(ATLAS_NAV_KEY, JSON.stringify(nav)); } catch { /* navigation still works without storage */ }
  }, [nav]);
  const [mode, setMode] = useState<'synthetic' | 'baked'>('baked');
  const [knobs, setKnobs] = useState<SyntheticKnobs>(DEFAULT_KNOBS);
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [caseId, setCaseId] = useState('');
  const [manifest, setManifest] = useState<CaseManifest | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [reevaluation, setReevaluation] = useState<Reevaluation | null>(null);
  const [indexLoading, setIndexLoading] = useState(true);
  const [analysis, setAnalysis] = useState<Record<string, any> | null>(null);
  const [streaming, setStreaming] = useState<Record<string, any> | null>(null);
  const [artifactsLoading, setArtifactsLoading] = useState(false);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [err, setErr] = useState('');
  // one Forecast tab, four on-graph views: Full (whole context), Zoom (predicted zone), Horizon
  // (per-lead error growth), Errors (per-lead residuals). Was three separate tabs + a toggle.
  const [fcView, setFcView] = useState<'full' | 'zoom' | 'horizon' | 'errors'>('full');
  // the metric the Methods legend displays (all lower-is-better); WQL/MSIS are baked-only
  const [legendMetric, setLegendMetric] = useState<LegendMetric>('mase');

  useEffect(() => {
    let cancelled = false;
    Promise.all([loadIndex(), loadReevaluation()]).then(([ix, comparison]) => {
      if (cancelled) return;
      setIndex(ix); setReevaluation(comparison); setCaseId(ix.cases[0]?.case_id ?? '');
    }).catch((e) => { if (!cancelled) setErr(String(e)); })
      .finally(() => { if (!cancelled) setIndexLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (mode !== 'baked' || !caseId) { setArtifactsLoading(false); return; }
    let cancelled = false;
    setAnalysis(null); setStreaming(null); setTrace(null); setManifest(null);
    setErr('');
    setArtifactsLoading(true);
    (async () => {
      try {
        const m = await loadManifest(caseId);
        const [nextTrace, nextAnalysis, nextStreaming] = await Promise.all([
          loadTrace(m.artifact.path),
          m.analysis_artifact ? loadAnalysis(m.analysis_artifact.path) : Promise.resolve(null),
          m.streaming_artifact ? loadStreaming(m.streaming_artifact.path) : Promise.resolve(null),
        ]);
        if (cancelled) return;
        setManifest(m);
        setTrace(nextTrace);
        setAnalysis(nextAnalysis);
        setStreaming(nextStreaming);
      } catch (e) {
        if (!cancelled) setErr(String(e));
      } finally {
        if (!cancelled) setArtifactsLoading(false);
      }
    })();
    return () => { cancelled = true; };
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
    const comparison = reevaluation?.cases.find(c => c.case_id === trace.case_id);
    if (!comparison) return null;
    const methods: ChartSeries[] = comparison.methods.map((m) => ({ name: m.name, color: colorFor(m.name), point: m.point, lower: m.lower, upper: m.upper }));
    const rows: Row[] = comparison.methods.map((m) => ({
      name: m.name, family: m.family,
      mase: m.metrics.mase ?? NaN, coverage: m.metrics.coverage ?? NaN,
      wql: m.metrics.wql ?? NaN, msis: m.metrics.msis ?? NaN,
    }));
    return { history: comparison.history, actual: trace.actual, horizon: trace.horizon, m: trace.seasonality, methods, rows };
  }, [mode, trace, reevaluation]);

  const activeData = mode === 'synthetic' ? synthetic : baked;

  const learned = useNLinearForecast(activeData);
  const onnxLoading = learned.status === 'loading';
  const onnx = useMemo(() => {
    if (learned.status !== 'ready' || !activeData) return null;
    const { point, lower, upper } = learned.forecast;
    const scale = seasonalNaiveMae(activeData.history, activeData.m);
    return { name: ONNX_NAME, color: colorFor(ONNX_NAME), point, lower, upper,
      mase: mase(activeData.actual, point, scale), coverage: coverage(activeData.actual, lower, upper) };
  }, [learned, activeData]);

  const allMethods = activeData ? (onnx ? [...activeData.methods, onnx] : activeData.methods) : [];
  const allRows: Row[] = activeData
    ? (onnx ? [...activeData.rows, { name: onnx.name, family: 'linear (live)', mase: onnx.mase, coverage: onnx.coverage }] : activeData.rows)
    : [];
  const visibleMethods = allMethods.filter((mm) => !hidden.has(mm.name));
  const rankedRows = [...allRows].sort((a, b) => (Number.isFinite(a.mase) ? a.mase : Infinity) - (Number.isFinite(b.mase) ? b.mase : Infinity));
  const best = rankedRows.find((r) => Number.isFinite(r.mase))?.name;

  const setK = (patch: Partial<SyntheticKnobs>) => setKnobs((k) => ({ ...k, ...patch }));
  const toggle = (name: string) => setHidden((h) => { const n = new Set(h); if (n.has(name)) n.delete(name); else n.add(name); return n; });
  // isolate a single curve: hide every other method (click again on it via "all" to restore)
  const solo = (name: string) => setHidden(new Set(allMethods.map((m) => m.name).filter((n) => n !== name)));
  const setGroup = (names: string[], show: boolean) => setHidden((h) => {
    const n = new Set(h);
    for (const name of names) { if (show) n.delete(name); else n.add(name); }
    return n;
  });
  const legendItems: LegendItem[] = allRows.map((r) => ({ name: r.name, family: r.family, color: colorFor(r.name), mase: r.mase, wql: r.wql, msis: r.msis }));

  // ---------------- UNDERSTAND half (live analysis on the active series + baked verdicts) ----------------

  // Each live diagnostic degrades to its empty value instead of crashing the page on a pathological
  // series (the per-tab PanelBoundary is the second layer; this is the first).
  const safe = <T,>(f: () => T, fb: T): T => { try { return f(); } catch { return fb; } };
  const sequenceData = mode === 'baked' ? analysis?.sequence as SequenceData | undefined : undefined;
  const fullSeries = sequenceData && 'values' in sequenceData ? sequenceData.values : activeData ? [...activeData.history, ...activeData.actual] : [];
  const sequenceProfile = sequenceData && 'values' in sequenceData ? sequenceData.matrix_profile : null;
  const sequenceMarks: RefLine[] = sequenceProfile?.available ? sequenceProfile.regime_boundaries.map(x => ({ x, label: 'FLUSS' })) : [];
  const stats = fullSeries.length ? safe(() => summaryStats(fullSeries), null) : null;
  const nlags = Math.min(48, Math.max(10, Math.floor(fullSeries.length / 4)));
  const acfVals = fullSeries.length > 8 ? safe(() => acf(fullSeries, nlags), []) : [];
  const pacfVals = fullSeries.length > 8 ? safe(() => pacf(fullSeries, Math.min(nlags, 24)), []) : [];
  const pgram = fullSeries.length > 16 ? safe(() => periodogram(fullSeries), null) : null;
  const roll = fullSeries.length > 8 ? safe(() => rolling(fullSeries, Math.max(5, Math.floor(fullSeries.length / 12))), null) : null;
  const alpha = fullSeries.length >= 64 ? safe(() => dfaAlpha(fullSeries), null) : null;
  const hist = fullSeries.length ? safe(() => histogram(fullSeries), null) : null;
  const band = bartlettBand(fullSeries.length);
  const bakedCatch22 = analysis && ((analysis as any).distribution?.catch22 as { available?: boolean; reason?: string; features?: Record<string, number> } | undefined);
  const bakedStationarity = analysis && (analysis as any).stationarity;
  const bakedVolatility = analysis && (analysis as any).volatility;
  const bakedNonlinear = analysis && (analysis as any).nonlinear;
  const bakedFractal = analysis && (analysis as any).fractal;

  const covariate = (streaming as { covariate?: { name: string; kind: string; values: number[] } } | null)?.covariate ?? null;
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
          xMarks={sequenceMarks}
          subtitle={es ? 'Una media móvil que deriva = tendencia/quiebre; una desviación móvil que respira = heterocedasticidad.' : 'A drifting rolling mean = trend/break; a breathing rolling std = heteroscedasticity.'}
        />
      )}
      {covariate && (
        <LinePlot
          xs={covariate.values.map((_, i) => i)}
          series={[{ label: covariate.name, values: covariate.values, color: '#bc8cff' }]}
          title={es ? `Covariable exógena: ${covariate.name} (${covariate.kind === 'known_future' ? 'conocida-a-futuro' : 'pasada'})` : `Exogenous covariate: ${covariate.name} (${covariate.kind === 'known_future' ? 'known-future' : 'past'})`}
          subtitle={es
            ? 'un regresor programado (p. ej. promociones) alineado a la serie. Conocido-a-futuro: sus valores del horizonte se saben de antemano, así un método con la covariable anticipa los saltos que uno univariado debe rezagar. La ganancia se ve en la pestaña Streaming (aware vs blind).'
            : 'a scheduled regressor (e.g. promotions) aligned to the series. Known-future: its horizon values are known ahead, so a method with the covariate anticipates the jumps a univariate method must lag. The gain is visible in the Streaming tab (aware vs blind).'}
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
          <UPlotChart
            xs={hist.edges.slice(0, -1).map((e, i) => e + (hist.edges[i + 1] - e) / 2)}
            series={[{ label: es ? 'frecuencia' : 'count', values: hist.counts, color: 'var(--color-accent)', bars: true }]}
            height={240}
            xLabel={es ? 'valor' : 'value'}
            ariaSummary={es ? 'histograma de la serie' : 'series histogram'}
            precision={0}
          />
          <div className="cs-panel-sub">{es
            ? `curtosis en exceso ${fmt(stats?.kurtosisExcess, 2)}: > 0 = colas más pesadas que la normal (los intervalos gaussianos sub-cubren).`
            : `excess kurtosis ${fmt(stats?.kurtosisExcess, 2)}: > 0 = heavier tails than normal (Gaussian intervals under-cover).`}</div>
        </div>
      )}
    </div>
  );

  // ---------- Decompose (Understand): classical additive decomposition + strengths + remainder QQ ----------
  const m_ = activeData?.m ?? 1;
  const decomp = fullSeries.length && m_ >= 2 ? safe(() => decompose(fullSeries, m_), null) : null;
  const remQQ = decomp ? safe(() => qqPairs(decomp.remainder.filter((v): v is number => v != null)), { theoretical: [], sample: [] }) : { theoretical: [] as number[], sample: [] as number[] };
  const understandDecompose = (
    <div className="cs-main">
      {!decomp && <p className="cs-panel-sub">{es
        ? `Sin estacionalidad declarada (m = ${m_}) o serie demasiado corta: la descomposición clásica necesita m >= 2 y n >= 2m + 1. Ver la tendencia en la pestaña Serie (media móvil).`
        : `No declared seasonality (m = ${m_}) or the series is too short: the classical decomposition needs m >= 2 and n >= 2m + 1. Read the trend on the Series tab (rolling mean) instead.`}</p>}
      {decomp && (
        <>
          <LinePlot
            xs={fullSeries.map((_, i) => i)}
            series={[
              { label: es ? 'serie' : 'series', values: fullSeries, color: 'var(--color-fg-faint)' },
              { label: es ? 'tendencia (MA centrada)' : 'trend (centered MA)', values: decomp.trend, color: 'var(--color-accent)' },
            ]}
            title={es ? 'Tendencia (media móvil centrada de orden m)' : 'Trend (centered order-m moving average)'}
            subtitle={es ? 'promedio móvil centrado (FPP3 cap. 3): exacto para tendencia lineal; NaN honesto en los bordes (m/2 puntos).' : 'centered moving average (FPP3 ch. 3): exact for a linear trend; honestly NaN at the edges (m/2 points).'}
          />
          <LinePlot
            xs={Array.from({ length: Math.min(3 * m_, fullSeries.length) }, (_, i) => i)}
            series={[{ label: es ? 'componente estacional' : 'seasonal component', values: decomp.seasonal.slice(0, 3 * m_), color: '#56d364' }]}
            refLine={0}
            title={es ? `Componente estacional (indices por fase, m = ${m_})` : `Seasonal component (per-phase indices, m = ${m_})`}
            subtitle={es ? 'medias por fase de la serie sin tendencia, centradas a suma 0; se muestran 3 temporadas.' : 'per-phase means of the detrended series, centered to sum 0; three seasons shown.'}
          />
          <LinePlot
            xs={fullSeries.map((_, i) => i)}
            series={[{ label: es ? 'residuo' : 'remainder', values: decomp.remainder, color: '#d29922' }]}
            refLine={0}
            title={es ? 'Residuo (serie - tendencia - estacional)' : 'Remainder (series - trend - seasonal)'}
            subtitle={es ? 'estructura visible aquí = algo que el modelo estacional-más-tendencia no captura (ver Estructura y Veredictos).' : 'visible structure here = something the trend-plus-seasonal model does not capture (see Structure and Verdicts).'}
          />
          <div className="cs-kpis">
            <div className="cs-kpi"><div className="cs-kpi-v">{fmt(decomp.seasonalStrength, 2)}</div><div className="cs-kpi-l">{es ? 'fuerza estacional' : 'seasonal strength'}</div></div>
            <div className="cs-kpi"><div className="cs-kpi-v">{fmt(decomp.trendStrength, 2)}</div><div className="cs-kpi-l">{es ? 'fuerza de tendencia' : 'trend strength'}</div></div>
          </div>
          {remQQ.theoretical.length > 0 && (
            <div className="cs-panel">
              <div className="cs-panel-t">{es ? 'QQ normal del residuo' : 'Normal QQ of the remainder'}</div>
              <UPlotChart
                xs={remQQ.theoretical}
                series={[
                  { label: 'y = x', values: remQQ.theoretical, color: 'var(--color-fg-subtle)', dash: [5, 4], width: 1.2 },
                  { label: es ? 'residuo' : 'remainder', values: remQQ.sample, color: 'var(--color-accent)', scatter: true },
                ]}
                height={300}
                xLabel={es ? 'cuantiles teóricos (normal)' : 'theoretical quantiles (normal)'}
                yLabel={es ? 'cuantiles del residuo' : 'remainder quantiles'}
                ariaSummary={es ? 'QQ normal del residuo' : 'normal QQ of the remainder'}
              />
              <div className="cs-panel-sub">{es
                ? 'puntos sobre la diagonal = residuo gaussiano (los intervalos gaussianos son honestos); forma de S = colas pesadas (sub-cobertura, ver la curtosis en Serie).'
                : 'points on the diagonal = Gaussian remainder (Gaussian intervals are honest); an S-shape = heavy tails (under-coverage; see the kurtosis on Series).'}</div>
            </div>
          )}
          <p className="cs-panel-sub">{es
            ? 'Fuerzas según FPP3, capítulo 12: 1 - Var(residuo)/Var(componente + residuo). Los paneles precalculados (Veredictos) traen STL/MSTL robustos; esta descomposición clásica es el espejo en vivo que reacciona a los controles.'
            : 'Strengths per FPP3, capítulo 12: 1 - Var(remainder)/Var(component + remainder). The baked panels (Verdicts) carry robust STL/MSTL; this classical decomposition is the live mirror that reacts to the controls.'}</p>
        </>
      )}
    </div>
  );

  // ---------- Residuals (Forecast): per-method holdout residuals + bias table ----------
  const residualSeries = activeData
    ? allMethods
        .filter((mm) => !hidden.has(mm.name))
        .map((mm) => ({
          label: mm.name,
          values: activeData.actual.map((a, i) => (Number.isFinite(a) && Number.isFinite(mm.point[i]) ? a - mm.point[i] : null)),
          color: mm.color,
        }))
    : [];
  const residualRows = residualSeries
    .map((s) => {
      const e = s.values.filter((v): v is number => v != null);
      if (!e.length) return null;
      const bias = e.reduce((a, b) => a + b, 0) / e.length;
      const mae_ = e.reduce((a, b) => a + Math.abs(b), 0) / e.length;
      const worst = Math.max(...e.map(Math.abs));
      return { name: s.label, bias, mae: mae_, worst };
    })
    .filter((r): r is { name: string; bias: number; mae: number; worst: number } => r != null)
    .sort((a, b) => Math.abs(a.bias) - Math.abs(b.bias));
  const forecastResiduals = (
    <div className="cs-main">
      {residualSeries.length > 0 && (
        <LinePlot
          xs={Array.from({ length: activeData?.horizon ?? 0 }, (_, i) => i + 1)}
          series={residualSeries}
          refLine={0}
          title={es ? 'Residuos del pronóstico (verdad - punto) por paso' : 'Forecast residuals (truth - point) by lead'}
          subtitle={es ? 'signo sistemático = sesgo; dispersión creciente = la incertidumbre crece con el paso (comparar con Horizonte).' : 'a systematic sign = bias; growing spread = uncertainty growing with lead (compare with Horizon).'}
        />
      )}
      <div className="cs-panel cs-chart">
        <table className="cs-table">
          <thead><tr><th>{es ? 'método' : 'method'}</th><th>{es ? 'sesgo' : 'bias'}</th><th>MAE</th><th>{es ? 'peor |e|' : 'worst |e|'}</th></tr></thead>
          <tbody>
            {residualRows.map((r) => (
              <tr key={r.name}>
                <td style={{ color: 'var(--color-fg)' }}><code>{r.name}</code></td>
                <td>{fmt(r.bias, 2)}</td>
                <td>{fmt(r.mae, 2)}</td>
                <td>{fmt(r.worst, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="cs-panel-sub">{es
        ? 'Sesgo y errores sobre el mismo bloque final mostrado, con un origen por caso. La tabla resume este bloque y Horizonte muestra sus errores por paso; ninguna vista establece un resultado poblacional. Use la leyenda para aislar métodos.'
        : 'Bias and errors on the same displayed final block, with one origin per case. The table summarizes this block and Horizon shows its lead-specific errors; neither view establishes a population result. Use the legend to isolate methods.'}</p>
    </div>
  );

  const understandStructure = (
    <div className="cs-main">
      {acfVals.length > 0 && <StemPlot values={acfVals} band={band} title={`ACF (${es ? 'banda' : 'band'} ±${fmt(band, 3)})`} />}
      {pacfVals.length > 0 && <StemPlot values={pacfVals} band={band} title="PACF (Durbin-Levinson)" />}
      <div className="cs-panel">
        <div className="cs-panel-t">{es ? 'Lectura Box-Jenkins' : 'Box-Jenkins read'}</div>
        <p className="cs-panel-sub">{es
          ? 'Bajo estacionariedad, ACF y PACF sugieren órdenes candidatos; no identifican un proceso de forma única. Las bandas son aproximaciones puntuales. Valores dentro de ellas no prueban independencia, y un decaimiento lento admite explicaciones distintas de memoria larga.'
          : 'Under stationarity, ACF and PACF suggest candidate orders; they do not uniquely identify a process. The bands are pointwise approximations. Values inside them do not prove independence, and slow decay admits explanations other than long memory.'}</p>
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
          ? 'α~0,5 ruido blanco · ~1 ruido 1/f · ~1,5 caminata aleatoria. Para fGn H=α; el vínculo ARFIMA es d = H − 0,5.'
          : 'α~0.5 white noise · ~1 pink noise · ~1.5 random walk. For fGn H=α; the ARFIMA link is d = H − 0.5.'}</p>
      </div>
      {mode === 'baked' && bakedStationarity && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'Estacionariedad (precálculo offline)' : 'Stationarity (baked offline)'} <span className="cs-badge replay">replay</span></div>
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
          <div className="cs-panel-t">{es ? 'Volatilidad (precalculado)' : 'Volatility (baked)'} <span className="cs-badge replay">replay</span></div>
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
          <div className="cs-panel-t">{es ? 'No linealidad, fractales y caos (precalculado)' : 'Nonlinearity, fractals and chaos (baked)'} <span className="cs-badge replay">replay</span></div>
          {bakedFractal && <p>Hurst R/S = <b>{fmt(bakedFractal.hurst?.rs, 3)}</b> · DFA α = <b>{fmt(bakedFractal.hurst?.dfa_alpha, 3)}</b> · {es ? 'Estimaciones de muestra finita; no demuestran memoria poblacional ni estacionariedad.' : bakedFractal.hurst?.interpretation}</p>}
          {bakedNonlinear && !bakedNonlinear.skipped && (
            <p>0-1 K = <b>{fmt(bakedNonlinear.zero_one_K, 3)}</b> · λ₁ = <b>{fmt(bakedNonlinear.largest_lyapunov, 4)}</b>{' '}
              <span className={`cs-badge ${bakedNonlinear.likely_chaotic ? 'warn' : 'ok'}`}>
                {bakedNonlinear.likely_chaotic ? (es ? 'caótica (gate de surrogates aprobado)' : 'chaotic (surrogate gate passed)') : (es ? 'sin caos confirmado' : 'no confirmed chaos')}
              </span></p>
          )}
          {bakedNonlinear?.skipped && <p className="cs-panel-sub">{es ? 'panel no lineal omitido honestamente (serie corta)' : 'nonlinear panel honestly skipped (short series)'}</p>}
        </div>
      )}
      {mode === 'baked' && bakedCatch22 && (
        <div className="cs-panel">
          <div className="cs-panel-t">{es ? 'catch22 · huella canónica (precalculado)' : 'catch22 · canonical fingerprint (baked)'} <span className="cs-badge replay">replay</span></div>
          {bakedCatch22.available === false ? (
            <p className="cs-panel-sub">{es ? 'no disponible: ' : 'unavailable: '}{bakedCatch22.reason}</p>
          ) : (
            <>
              <div className="cs-panel-sub">{es
                ? 'Las 24 features canónicas (catch22 + media y desviación): destiladas de las ~7700 de hctsa seleccionando por desempeño de clasificación y baja redundancia. Es la respuesta rigurosa a "extraer muchas features": llevan la información de un banco grande sin la escopeta.'
                : 'The 24 canonical features (catch22 + mean and std): distilled from hctsa\'s ~7700 by selecting for classification performance and low redundancy. This is the rigorous answer to "extract many features": the information of a large bank without the shotgun.'}</div>
              <div className="cs-chart">
                <table className="cs-table">
                  <thead><tr><th>{es ? 'feature' : 'feature'}</th><th>{es ? 'valor' : 'value'}</th><th>{es ? 'feature' : 'feature'}</th><th>{es ? 'valor' : 'value'}</th></tr></thead>
                  <tbody>
                    {(() => {
                      const entries = Object.entries(bakedCatch22.features ?? {});
                      const half = Math.ceil(entries.length / 2);
                      return entries.slice(0, half).map(([k, v], i) => {
                        const right = entries[half + i];
                        return (
                          <tr key={k}>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{k}</td>
                            <td>{fmt(v as number, 4)}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>{right ? right[0] : ''}</td>
                            <td>{right ? fmt(right[1] as number, 4) : ''}</td>
                          </tr>
                        );
                      });
                    })()}
                  </tbody>
                </table>
              </div>
              <p className="cs-panel-sub">Lubba et al. 2019, Data Min. Knowl. Disc. 33(6):1821-1852 (DOI 10.1007/s10618-019-00647-x).</p>
            </>
          )}
        </div>
      )}
      {mode === 'synthetic' && (
        <p className="cs-panel-sub">{es
          ? 'Los veredictos pesados (ADF/KPSS, GARCH, surrogates de caos) se ejecutan offline y aparecen al elegir un caso precalculado; el resto de este panel es en vivo.'
          : 'The heavy verdicts (ADF/KPSS, GARCH, chaos surrogates) run offline and appear when a baked case is picked; the rest of this panel is live.'}</p>
      )}
    </div>
  );

  // ---------------- FORECAST half (interactive uPlot; Forecast <-> Errors toggle) ----------------

  // Build the forecast chart series over a shared index axis: history (grey), held-out truth (green dashed),
  // each visible method's point line over the forecast region, plus the focused method's interval band.
  const buildForecast = (histTail: number): { xs: number[]; series: USeries[]; refs: RefLine[] } | null => {
    if (!activeData || !activeData.history.length) return null;
    const histAll = activeData.history;
    const keep = histTail > 0 ? Math.min(histAll.length, histTail) : histAll.length;
    const hist = histAll.slice(-keep);
    const nHist = hist.length;
    const h = activeData.horizon;
    const total = nHist + h;
    const xs = Array.from({ length: total }, (_, i) => i);
    const pad = (fwd: (number | null)[]) => [...Array(nHist).fill(null), ...fwd];
    const series: USeries[] = [
      { label: es ? 'historia' : 'history', values: [...hist, ...Array(h).fill(null)], color: 'var(--color-fg-subtle)', width: 1.4 },
    ];
    if (activeData.actual.length) series.push({ label: es ? 'verdad' : 'truth', values: pad(activeData.actual.slice(0, h)), color: '#3fb950', width: 2.2, dash: [5, 3] });
    // the single focused method (only one visible) gets its interval band drawn
    const focus = visibleMethods.length === 1 ? visibleMethods[0] : null;
    if (focus) {
      series.push({ label: `${focus.name} ↑`, values: pad(focus.upper), color: focus.color, width: 0.6, fillToLabel: `${focus.name} ↓`, fillAlpha: 0.14 });
      series.push({ label: `${focus.name} ↓`, values: pad(focus.lower), color: focus.color, width: 0.6 });
    }
    for (const m of visibleMethods) series.push({ label: m.name, values: pad(m.point), color: m.color, width: 2 });
    const refs: RefLine[] = [{ x: nHist - 0.5, color: 'var(--color-fg-subtle)', label: es ? 'pronóstico ->' : 'forecast ->' }];
    return { xs, series, refs };
  };

  // Errors view: each visible method's residual (truth - point) by lead, with a zero baseline.
  const buildErrors = (): { xs: number[]; series: USeries[]; refs: RefLine[] } | null => {
    if (!activeData || !activeData.actual.length) return null;
    const h = activeData.horizon;
    const xs = Array.from({ length: h }, (_, i) => i + 1);
    const series: USeries[] = visibleMethods.map((m) => ({
      label: m.name,
      values: activeData.actual.slice(0, h).map((a, i) => (Number.isFinite(a) && Number.isFinite(m.point[i]) ? a - m.point[i] : null)),
      color: m.color, width: 2,
    }));
    return { xs, series, refs: [{ y: 0, dash: [5, 4] }] };
  };

  // ONE Forecast tab. Full: a recent context window (last ~5 seasons) + the horizon so the forecast
  // region is a meaningful fraction of the width; Zoom: tightens to ~2 seasons; Horizon: per-lead error
  // growth from the baked backtest; Errors: per-lead residuals on the displayed holdout.
  const fcHistTail = Math.max(5 * (activeData?.m ?? 12), 60);
  const fcData = fcView === 'errors' ? buildErrors()
    : fcView === 'zoom' ? buildForecast(Math.max(2 * (activeData?.m ?? 12), 24))
    : fcView === 'full' ? buildForecast(fcHistTail)
    : null;

  const horizonScale = activeData ? seasonalNaiveMae(activeData.history, activeData.m) : NaN;
  const horizonRows = activeData ? visibleMethods.map(m => ({ label: m.name,
    values: activeData.actual.map((a, i) => horizonScale > 0 ? Math.abs(a - m.point[i]) / horizonScale : null),
    color: colorFor(m.name), width: 2,
  })) : [];

  const fcTitles: Record<typeof fcView, string> = {
    full: es ? 'Pronóstico + intervalo' : 'Forecast + interval',
    zoom: es ? 'Zoom en la zona predicha' : 'Zoom on the predicted zone',
    horizon: es ? 'Error absoluto escalado por paso' : 'Scaled absolute error by lead',
    errors: es ? 'Errores por paso (verdad - punto)' : 'Errors by lead (truth - point)',
  };
  const fcNotes: Record<typeof fcView, string> = {
    full: (es
      ? 'Gris = historia, verde discontinuo = verdad reservada, color = pronóstico; con un método visible se dibujan sus límites de cuantiles. '
      : 'Grey = history, dashed green = held-out truth, colour = forecasts; with one method visible its quantile boundaries are drawn. ')
      + (mode === 'synthetic'
        ? (es ? 'Métodos de suavizamiento y ONNX calculados en el navegador.' : 'Smoothing methods and ONNX computed in the browser.')
        : (es ? `${allMethods.length} variantes sobre el bloque final común.` : `${allMethods.length} variants on the common final holdout.`)),
    zoom: es
      ? 'Las últimas dos temporadas aproximadas y el horizonte. El cursor lee valores; use arrastre, teclado y el control de restablecimiento del gráfico.'
      : 'Approximately the last two seasons and the horizon. The cursor reads values; use dragging, the keyboard and the chart reset control.',
    horizon: es
      ? 'Error absoluto de cada paso del bloque final dividido por la escala estacional histórica. Es una trayectoria observada, no una media de múltiples orígenes ni una identificación causal del proceso.'
      : 'Absolute error at each final-block lead divided by the historical seasonal scale. This is one observed trajectory, not a multiple-origin mean or a causal identification of the process.',
    errors: es
      ? 'El residuo por paso sobre el holdout mostrado: signo sistemático = sesgo; dispersión que crece con el paso = incertidumbre que crece. Aislar una curva con "solo" en la leyenda.'
      : 'The per-lead residual on the displayed holdout: a systematic sign = bias; spread growing with lead = growing uncertainty. Isolate a curve with "solo" in the legend.',
  };

  const forecastPanel = (
    <div className="cs-main">
      <div className="cs-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem', gap: '0.6rem', flexWrap: 'wrap' }}>
          <div className="cs-panel-t" style={{ marginBottom: 0 }}>{fcTitles[fcView]}</div>
          <div className="cs-seg" role="tablist" aria-label={es ? 'vista' : 'view'}>
            <button className={fcView === 'full' ? 'is-active' : ''} onClick={() => setFcView('full')} role="tab" aria-selected={fcView === 'full'}>{es ? 'Completo' : 'Full'}</button>
            <button className={fcView === 'zoom' ? 'is-active' : ''} onClick={() => setFcView('zoom')} role="tab" aria-selected={fcView === 'zoom'}>Zoom</button>
            <button className={fcView === 'horizon' ? 'is-active' : ''} onClick={() => setFcView('horizon')} role="tab" aria-selected={fcView === 'horizon'}>{es ? 'Horizonte' : 'Horizon'}</button>
            <button className={fcView === 'errors' ? 'is-active' : ''} onClick={() => setFcView('errors')} role="tab" aria-selected={fcView === 'errors'}>{es ? 'Errores' : 'Errors'}</button>
          </div>
        </div>
        {fcView === 'horizon' ? (
          horizonRows.length > 0 ? (
            <UPlotChart
              xs={Array.from({ length: activeData?.horizon ?? 0 }, (_, i) => i + 1)}
              series={horizonRows}
              refLines={[{ y: 1, dash: [5, 4], label: es ? 'escala histórica' : 'historical scale' }]}
              height={380}
              xLabel={es ? 'paso (lead)' : 'lead'}
              ariaSummary="per-lead scaled error growth"
            />
          ) : (
            <p className="cs-panel-sub">{es
              ? 'Este trace no trae curvas por horizonte (artefacto anterior a v2): re-precalcular el caso.'
              : 'This trace carries no per-horizon curves (a pre-v2 artifact): re-bake the case.'}</p>
          )
        ) : fcData ? (
          <UPlotChart xs={fcData.xs} series={fcData.series} refLines={fcData.refs} height={380} ariaSummary={fcTitles[fcView]} />
        ) : (
          <p className="cs-panel-sub">{fcView === 'errors'
            ? (es ? 'la vista de errores necesita la verdad reservada (fuente con licencia solo-local: no se publica).' : 'the errors view needs the held-out truth (local-only-licensed source: not published).')
            : (es ? 'fuente con licencia solo-local: la serie no se publica; ver la tabla y el banco de streaming.' : 'local-only-licensed source: the series is not published; see the table and the streaming bench.')}</p>
        )}
      </div>
      <p className="cs-panel-sub">{fcNotes[fcView]}</p>
      {onnx && <p className="cs-panel-sub">{es
        ? 'Lineal: intervalos marginales nominales del 80 %, calibrados por rugosidad de historias sintéticas. La cobertura en datos reales no está confirmada.'
        : 'Linear: nominal 80% marginal intervals, calibrated by synthetic-prefix roughness. Coverage on real data is unconfirmed.'}</p>}
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
                <td style={{ color: 'var(--color-fg)' }}><code>{r.name}</code></td>
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
        ? `Comparación sobre el mismo bloque final, con un origen por caso. MASE usa la escala estacional de la historia; WQL usa tres cuantiles; MSIS penaliza amplitud y fallas. Menor error en este bloque: ${best ?? '-'}. Los pronósticos pesados archivados se repuntúan; los métodos ligeros se recalcularon.`
        : `Comparison on the same final block, with one origin per case. MASE uses the historical seasonal scale; WQL uses three quantiles; MSIS penalizes width and misses. Lowest error on this block: ${best ?? '-'}. Archived heavy forecasts are rescored; light methods were recomputed.`}</p>
    </div>
  );

  const streamingBench = (
    <div className="cs-main">
      {mode !== 'baked' && <p className="cs-panel-sub">{es ? 'El banco de streaming se precalcula offline por caso: elegir un caso precalculado.' : 'The streaming bench is baked offline per case: pick a baked case.'}</p>}
      {mode === 'baked' && streaming && (() => {
        const meths = (streaming as any).methods ?? {};
        const names = Object.keys(meths).filter((k) => !meths[k].error);
        const labels: Record<string, string> = { Theta: 'S+D', 'Theta+ACI': 'S+D + ACI-style', 'Theta+PID': 'S+D + PID-style' };
        const displayName = (key: string) => labels[key] ?? key;
        const colors: Record<string, string> = { SeasonalNaive: '#58a6ff', Theta: '#56d364', 'Theta+ACI': '#d29922', 'Theta+PID': '#ff7b72', 'Ridge (blind)': '#8b949e', 'Ridge+exog (aware)': '#3fb950' };
        const n = Math.max(...names.map((k) => meths[k].n_steps ?? 0), 0);
        const xs = Array.from({ length: n }, (_, i) => i);
        const cov = (streaming as any).covariate;
        return (
          <>
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: displayName(k), values: meths[k].rolling_coverage ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'Cobertura rodante y nivel nominal' : 'Rolling coverage and nominal level'}
              subtitle={es
                ? `objetivo ${fmt((streaming as any).nominal_coverage)}: ventanas solapadas de hasta 25 observaciones; los controles adaptativos no garantizan cobertura condicional.`
                : `target ${fmt((streaming as any).nominal_coverage)}: overlapping windows of up to 25 observations; adaptive controllers do not guarantee conditional coverage.`}
              refLine={(streaming as any).nominal_coverage}
            />
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: displayName(k), values: meths[k].rolling_mase ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'MASE rodante (habilidad sobre el stream)' : 'Rolling MASE (skill over the stream)'}
            />
            <LinePlot xs={xs}
              series={names.map((k) => ({ label: displayName(k), values: meths[k].cumulative_cost_ms ?? [], color: colors[k] ?? colorFor(k) }))}
              title={es ? 'Costo de cómputo acumulado (ms)' : 'Cumulative compute cost (ms)'}
              subtitle={es ? 'Tiempos históricos de la ejecución original; no son una comparación normalizada de hardware ni una medición actual.' : 'Historical timings from the original run; these are not a normalized hardware comparison or a current measurement.'}
            />
            {cov && (
              <div className="cs-panel" style={{ borderColor: '#3fb95066' }}>
                <div className="cs-panel-t" style={{ color: 'var(--color-good)' }}>{es ? 'Política de llegada de covariables' : 'Covariate arrival policy'}</div>
                <div className="cs-panel-sub">{es
                  ? `Este caso trae una covariable ${cov.kind === 'known_future' ? 'conocida-a-futuro' : 'pasada'} (${cov.name}). Ridge+exog (aware, verde) la usa: conoce el driver del horizonte y anticipa los saltos; Ridge (blind, gris) es el mismo modelo sin la covariable. La brecha entre ambos es lo que compra la covariable. La política de arribo determina qué información estaba disponible en cada origen.`
                  : `This case carries a ${cov.kind === 'known_future' ? 'known-future' : 'past'} covariate (${cov.name}). Ridge+exog (aware, green) uses it: it knows the horizon's driver and anticipates the jumps; Ridge (blind, grey) is the same model without the covariate. The gap between them is what the covariate buys. The arrival policy determines which information was available at each origin.`}</div>
                <div className="cs-panel-sub" style={{ marginTop: '0.3rem' }}>
                  {es ? 'MASE final: ' : 'Final MASE: '}
                  <b style={{ color: '#3fb950' }}>aware {fmt(meths['Ridge+exog (aware)']?.final?.mase, 2)}</b>
                  {' vs '}
                  <b style={{ color: '#8b949e' }}>blind {fmt(meths['Ridge (blind)']?.final?.mase, 2)}</b>
                </div>
              </div>
            )}
            <p className="cs-panel-sub">{es
              ? 'Estudio histórico a un paso: S+D es una adaptación de suavizamiento más deriva, identificada como Theta en los archivos. El pronóstico se recalcula con toda la historia observada. ACI-style y PID-style ajustan intervalos; PID-style no replica el algoritmo Conformal PID publicado. La clave histórica no identifica el Theta corregido de la comparación de bloques finales.'
              : 'Historical one-step replay: S+D is the smoothing-plus-drift adaptation stored under the artifact key Theta. Point forecasts are recomputed from the full observed prefix. ACI-style and PID-style adapt intervals; PID-style does not replicate the published Conformal PID algorithm. The historical key does not identify the corrected Theta in the final-block comparison.'}</p>
          </>
        );
      })()}
    </div>
  );

  // ---------------- layout: full-width top control bar + (chart area | method legend rail) ----------------

  // the baked case fingerprint: the diagnostics that say WHAT this series is, as chips
  const fp: { label: string; value: string }[] = [];
  if (mode === 'baked' && trace) {
    fp.push({ label: 'm', value: String(trace.seasonality) });
    const ss = dig(analysis, 'seasonality', 'stl_at_dominant', 'strength_seasonal');
    if (ss != null) fp.push({ label: es ? 'estac.' : 'seasonal', value: fmt(ss, 2) });
    const a = dig(analysis, 'fractal', 'hurst', 'dfa_alpha');
    if (a != null) fp.push({ label: 'DFA α', value: fmt(a, 2) });
    const gp = dig(analysis, 'volatility', 'garch', 'persistence');
    if (gp != null) fp.push({ label: 'GARCH', value: fmt(gp, 2) });
    const k = dig(analysis, 'nonlinear', 'zero_one_K');
    if (k != null) fp.push({ label: es ? 'caos K' : 'chaos K', value: fmt(k, 2) });
    if (trace.summary.best_mase != null) fp.push({ label: es ? 'mejor MASE' : 'best MASE', value: fmt(trace.summary.best_mase, 2) });
  }

  const groups: ('Synthetic' | 'Real' | 'Control')[] = ['Synthetic', 'Real', 'Control'];
  const knobDefs: [string, number, number, number, number, (v: number) => void][] = [
    ['n', knobs.n, 40, 400, 10, (v) => setK({ n: v })],
    ['m', knobs.seasonality, 1, 48, 1, (v) => setK({ seasonality: v })],
    ['horizon', knobs.horizon, 1, 48, 1, (v) => setK({ horizon: v })],
    ['amp', knobs.amp, 0, 40, 1, (v) => setK({ amp: v })],
    ['slope', knobs.slope, -1, 1, 0.05, (v) => setK({ slope: v })],
    ['noise', knobs.noise, 0, 15, 0.5, (v) => setK({ noise: v })],
    ['seed', knobs.seed, 0, 50, 1, (v) => setK({ seed: v })],
  ];

  return (
    <section className="cs-app" data-state={indexLoading || artifactsLoading || onnxLoading ? 'loading' : 'ready'}>
      {err && <p style={{ color: 'var(--color-bad)' }}>error: {err}</p>}

      {/* full-width control bar: source, case/pattern picker, fingerprint */}
      <div className="cs-bar">
        <div className="cs-bar-group">
          <span className="cs-bar-label">{es ? 'Fuente' : 'Source'}</span>
          <div className="cs-seg" role="tablist" aria-label={es ? 'fuente' : 'source'}>
            <button className={mode === 'baked' ? 'is-active' : ''} onClick={() => setMode('baked')} role="tab" aria-selected={mode === 'baked'}>{es ? 'Caso precalculado' : 'Baked case'}</button>
            <button className={mode === 'synthetic' ? 'is-active' : ''} onClick={() => setMode('synthetic')} role="tab" aria-selected={mode === 'synthetic'}>{es ? 'Sintética (vivo)' : 'Synthetic (live)'}</button>
          </div>
        </div>
        {mode === 'baked' ? (
          <>
            <div className="cs-bar-group">
              <span className="cs-bar-label">{es ? 'Caso' : 'Case'}</span>
              <select className="cs-sel" aria-label={es ? 'Caso' : 'Case'} value={caseId} onChange={(e) => setCaseId(e.target.value)}>
                {groups.map((g) => {
                  const opts = (index?.cases ?? []).filter((c) => caseGroup(c.case_id) === g);
                  return opts.length ? <optgroup key={g} label={g}>{opts.map((c) => <option key={c.case_id} value={c.case_id}>{c.case_id.replace(/_/g, ' ')}</option>)}</optgroup> : null;
                })}
              </select>
            </div>
            {fp.length > 0 && (
              <div className="cs-fingerprint" aria-label={es ? 'huella del caso' : 'case fingerprint'}>
                {fp.map((f) => <span key={f.label} className="cs-fp"><span>{f.label}</span><b>{f.value}</b></span>)}
                {manifest && <span className={`cs-badge ${manifest.provenance.public_artifact_ok ? 'real' : 'warn'}`}>{manifest.provenance.license}</span>}
              </div>
            )}
          </>
        ) : (
          <div className="cs-bar-group">
            <span className="cs-bar-label">{es ? 'Patrón' : 'Pattern'}</span>
            <select className="cs-sel" aria-label={es ? 'Patrón sintético' : 'Synthetic pattern'} value={knobs.kind} onChange={(e) => setK({ kind: e.target.value as SyntheticKind })}>
              {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
            <span className="cs-badge live">LIVE</span>
          </div>
        )}
        <span className="spacer" />
      </div>

      {/* synthetic knobs, second bar row (compact, only in live mode) */}
      {mode === 'synthetic' && (
        <div className="cs-bar" style={{ gap: '0.5rem 1.2rem' }}>
          {knobDefs.map(([label, value, min, max, step, on]) => (
            <label key={label} className="cs-ctl" style={{ minWidth: 128 }}>
              <span className="cs-ctl-row"><span>{label}</span><b>{fmt(value)}</b></span>
              <input className="cs-range" type="range" min={min} max={max} step={step} value={value} onChange={(e) => on(Number(e.target.value))} />
            </label>
          ))}
        </div>
      )}

      {/* chart area (fills the width) + the interactive method-legend rail */}
      <div className="cs-plotwrap" style={{ marginTop: '0.8rem' }}>
        <div className="cs-plot">
          <TabGroups
            ariaLabel="workbench views"
            value={nav}
            onChange={(next) => setNav(next as AtlasNav)}
            groups={[
              { id: 'understand', label: es ? 'Entender' : 'Understand', tabs: [
                { id: 'series', label: es ? 'Serie' : 'Series', content: <PanelBoundary label="Series" es={es}>{understandSeries}</PanelBoundary> },
                { id: 'structure', label: es ? 'Estructura' : 'Structure', content: <PanelBoundary label="Structure" es={es}>{understandStructure}</PanelBoundary> },
                { id: 'decompose', label: es ? 'Descomponer' : 'Decompose', content: <PanelBoundary label="Decompose" es={es}>{understandDecompose}</PanelBoundary> },
                { id: 'patterns', label: es ? 'Patrones' : 'Patterns', content: <PanelBoundary label="Patterns" es={es}><SequenceDiagnostics data={sequenceData} /></PanelBoundary> },
                { id: 'verdicts', label: es ? 'Veredictos' : 'Verdicts', content: <PanelBoundary label="Verdicts" es={es}>{understandVerdicts}</PanelBoundary> },
              ] },
              { id: 'forecast', label: es ? 'Pronosticar' : 'Forecast', tabs: [
                { id: 'forecast', label: es ? 'Pronóstico' : 'Forecast', content: <PanelBoundary label="Forecast" es={es}>{forecastPanel}</PanelBoundary> },
                { id: 'residuals', label: es ? 'Residuos' : 'Residuals', content: <PanelBoundary label="Residuals" es={es}>{forecastResiduals}</PanelBoundary> },
                { id: 'leaderboard', label: es ? 'Tabla' : 'Leaderboard', content: <PanelBoundary label="Leaderboard" es={es}>{leaderboard}</PanelBoundary> },
                { id: 'streaming', label: 'Streaming', content: <PanelBoundary label="Streaming" es={es}>{streamingBench}</PanelBoundary> },
              ] },
            ]}
          />
        </div>
        {legendItems.length > 0 && (
          <SeriesLegend items={legendItems} hidden={hidden} onToggle={toggle} onSolo={solo} onSetGroup={setGroup} metric={legendMetric} onMetric={setLegendMetric} es={es} />
        )}
      </div>
    </section>
  );
}
