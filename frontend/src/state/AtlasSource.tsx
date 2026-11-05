import { createContext, useContext, useEffect, useMemo, useState, type Dispatch, type ReactNode, type SetStateAction } from 'react';
import { useSearchParams } from 'react-router';
import { loadAnalysis, loadCombinationCase, loadIndex, loadManifest, loadReevaluation, loadStreaming, loadTrace } from '../api/artifacts';
import type { CaseIndex, CaseManifest, CombinationCase, Trace } from '../lib/contract.types';
import type { Reevaluation } from '../lib/reevaluation.types';
import { forecastAllLive } from '../lib/liveEngine';
import { coverage, mase, seasonalNaiveMae } from '../lib/liveMetrics';
import { methodColor } from '../lib/methodColors';
import { DEFAULT_KNOBS, generateSeries, type SyntheticKind, type SyntheticKnobs } from '../lib/synthetic';
import { useNLinearForecast } from '../lib/useNLinearForecast';
import { BROWSER_LINEAR_NAME } from '../lib/calibratedLinearIntervals';

export interface ChartSeries { name: string; color: string; point: number[]; lower: number[]; upper: number[]; }
export interface ScoreRow { name: string; family: string; mase: number; coverage: number; wql?: number; msis?: number; }
export interface AtlasData { history: number[]; actual: number[]; horizon: number; m: number; methods: ChartSeries[]; rows: ScoreRow[]; }
const KINDS: SyntheticKind[] = ['seasonal', 'trend_seasonal', 'intermittent', 'random_walk', 'white_noise'];

export function parseSyntheticKnobs(raw: string | null): { knobs: SyntheticKnobs; error: string } {
  if (!raw) return { knobs: DEFAULT_KNOBS, error: '' };
  try {
    const value = JSON.parse(raw) as SyntheticKnobs;
    const keys = Object.keys(DEFAULT_KNOBS) as (keyof SyntheticKnobs)[];
    if (Object.keys(value).length !== keys.length || !KINDS.includes(value.kind)
        || keys.some(key => key !== 'kind' && !Number.isFinite(value[key]))
        || !Number.isInteger(value.n) || value.n < 4 || value.n > 2000
        || !Number.isInteger(value.horizon) || value.horizon < 1 || value.horizon >= value.n || value.horizon > 200
        || !Number.isInteger(value.seasonality) || value.seasonality < 1 || value.seasonality > 500
        || !Number.isInteger(value.seed) || value.seed < 0 || value.seed > 0xffffffff) throw new Error('Invalid synthetic configuration');
    return { knobs: value, error: '' };
  } catch { return { knobs: DEFAULT_KNOBS, error: 'Invalid synthetic configuration in this link' }; }
}

/** Only combine records with the same origin, seasonal lag and entire reserved target block. */
export function matchingCombinationOrigin(document: CombinationCase | null, data: AtlasData | null, prefixSha256: string | null) {
  if (!document || !data || !prefixSha256 || document.horizon !== data.horizon || document.seasonality !== data.m) return null;
  return document.origins.find(origin => origin.origin === data.history.length && origin.prefix_start === 0
    && origin.prefix_length === data.history.length && origin.prefix_sha256 === prefixSha256 && origin.actual.length === data.actual.length
    && origin.actual.every((value, i) => Math.abs(value - data.actual[i]) <= .000051)) ?? null;
}

interface Snapshot {
  owner: string; manifest: CaseManifest; trace: Trace; analysis: Record<string, any> | null;
  streaming: Record<string, any> | null; combination: CombinationCase | null; combinationError: string;
}

function useSource() {
  const [params, setParams] = useSearchParams();
  const mode = params.get('source') === 'synthetic' ? 'synthetic' : 'baked';
  const rawKnobs = params.get('knobs');
  const parsed = useMemo(() => parseSyntheticKnobs(rawKnobs), [rawKnobs]);
  const knobs = parsed.knobs;
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [reevaluation, setReevaluation] = useState<Reevaluation | null>(null);
  const [indexLoading, setIndexLoading] = useState(true);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [failure, setFailure] = useState({ owner: '', message: '' });
  const caseId = params.get('case') ?? index?.cases[0]?.case_id ?? '';
  const owned = mode === 'baked' && snapshot?.owner === caseId ? snapshot : null;
  const err = mode === 'synthetic' ? parsed.error : failure.owner === caseId ? failure.message : '';
  const setCaseId = (id: string) => setParams(previous => { const next = new URLSearchParams(previous); next.set('case', id); return next; }, { replace: true });
  const setMode = (nextMode: 'synthetic' | 'baked') => setParams(previous => { const next = new URLSearchParams(previous); next.set('source', nextMode); return next; }, { replace: true });
  const setKnobs: Dispatch<SetStateAction<SyntheticKnobs>> = value => {
    const nextKnobs = typeof value === 'function' ? value(knobs) : value;
    setParams(previous => { const next = new URLSearchParams(previous); next.set('knobs', JSON.stringify(nextKnobs)); return next; }, { replace: true });
  };

  useEffect(() => {
    let cancelled = false;
    Promise.all([loadIndex(), loadReevaluation()]).then(([nextIndex, comparison]) => {
      if (!cancelled) { setIndex(nextIndex); setReevaluation(comparison); }
    }).catch(error => { if (!cancelled) setFailure({ owner: caseId, message: String(error) }); })
      .finally(() => { if (!cancelled) setIndexLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (mode !== 'baked' || !caseId || !index) return;
    let cancelled = false;
    setFailure({ owner: caseId, message: '' });
    if (!index.cases.some(item => item.case_id === caseId)) {
      setFailure({ owner: caseId, message: 'The requested case is not in the admitted inventory' }); return;
    }
    (async () => {
      try {
        const manifest = await loadManifest(caseId);
        const [trace, analysis, streaming, combination] = await Promise.all([
          loadTrace(manifest.artifact.path),
          manifest.analysis_artifact ? loadAnalysis(manifest.analysis_artifact.path) : Promise.resolve(null),
          manifest.streaming_artifact ? loadStreaming(manifest.streaming_artifact.path) : Promise.resolve(null),
          loadCombinationCase(`combinations/selected_cases/${caseId}.json`).then(document => ({ document, error: '' }))
            .catch(error => ({ document: null, error: String(error) })),
        ]);
        if (manifest.case_id !== caseId || trace.case_id !== caseId) throw new Error('Artifact subject differs from the selected case');
        if (!cancelled) setSnapshot({ owner: caseId, manifest, trace, analysis, streaming,
          combination: combination.document, combinationError: combination.error });
      } catch (error) { if (!cancelled) setFailure({ owner: caseId, message: String(error) }); }
    })();
    return () => { cancelled = true; };
  }, [mode, caseId, index]);

  const synthetic = useMemo<AtlasData | null>(() => {
    if (mode !== 'synthetic' || parsed.error) return null;
    const values = generateSeries(knobs);
    const history = values.slice(0, values.length - knobs.horizon), actual = values.slice(-knobs.horizon);
    const forecasts = forecastAllLive(history, knobs.seasonality, knobs.horizon, [.1, .5, .9]);
    const scale = seasonalNaiveMae(history, knobs.seasonality);
    return { history, actual, horizon: knobs.horizon, m: knobs.seasonality,
      methods: forecasts.map(value => ({ name: value.name, color: methodColor(value.name), point: value.point, lower: value.lower, upper: value.upper })),
      rows: forecasts.map(value => ({ name: value.name, family: 'classical', mase: mase(actual, value.point, scale), coverage: coverage(actual, value.lower, value.upper) })) };
  }, [mode, knobs, parsed.error]);
  const baked = useMemo<AtlasData | null>(() => {
    const comparison = owned && reevaluation?.cases.find(item => item.case_id === owned.trace.case_id);
    if (!owned || !comparison) return null;
    return { history: comparison.history, actual: owned.trace.actual, horizon: owned.trace.horizon, m: owned.trace.seasonality,
      methods: comparison.methods.map(value => ({ name: value.name, color: methodColor(value.name), point: value.point, lower: value.lower, upper: value.upper })),
      rows: comparison.methods.map(value => ({ name: value.name, family: value.family, mase: value.metrics.mase ?? NaN,
        coverage: value.metrics.coverage ?? NaN, wql: value.metrics.wql ?? NaN, msis: value.metrics.msis ?? NaN })) };
  }, [owned, reevaluation]);
  const activeData = mode === 'synthetic' ? synthetic : baked;
  const [prefixBinding, setPrefixBinding] = useState<{ history: number[]; sha256: string } | null>(null);
  useEffect(() => {
    if (!activeData || mode !== 'baked' || !owned?.combination || !globalThis.crypto?.subtle) return;
    let cancelled = false;
    const history = activeData.history;
    const bytes = new ArrayBuffer(history.length * 8);
    const view = new DataView(bytes);
    history.forEach((value, i) => view.setFloat64(i * 8, value, true));
    crypto.subtle.digest('SHA-256', bytes).then(digest => {
      if (!cancelled) setPrefixBinding({ history, sha256: Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('') });
    }).catch(() => { /* An unverified prefix never acquires combination weights. */ });
    return () => { cancelled = true; };
  }, [activeData, mode, owned?.combination]);
  const prefixSha256 = prefixBinding?.history === activeData?.history ? prefixBinding?.sha256 ?? null : null;
  const learned = useNLinearForecast(activeData);
  const onnx = useMemo(() => {
    if (learned.status !== 'ready' || !activeData) return null;
    const { point, lower, upper } = learned.forecast;
    return { name: BROWSER_LINEAR_NAME, color: methodColor(BROWSER_LINEAR_NAME), point, lower, upper,
      mase: mase(activeData.actual, point, seasonalNaiveMae(activeData.history, activeData.m)), coverage: coverage(activeData.actual, lower, upper) };
  }, [learned, activeData]);
  const allMethods = useMemo(() => activeData ? onnx ? [...activeData.methods, onnx] : activeData.methods : [], [activeData, onnx]);
  const allRows = useMemo<ScoreRow[]>(() => activeData ? onnx ? [...activeData.rows, { name: onnx.name, family: 'linear (live)', mase: onnx.mase, coverage: onnx.coverage }] : activeData.rows : [], [activeData, onnx]);
  return { mode, setMode, knobs, setKnobs, caseId, setCaseId, index, indexLoading, reevaluation,
    trace: owned?.trace ?? null, manifest: owned?.manifest ?? null, analysis: owned?.analysis ?? null,
    streaming: owned?.streaming ?? null, combination: owned?.combination ?? null,
    combinationError: owned?.combinationError ?? '', combinationOrigin: matchingCombinationOrigin(owned?.combination ?? null, activeData, prefixSha256),
    activeData, allMethods, allRows, onnx, onnxLoading: learned.status === 'loading',
    artifactsLoading: mode === 'baked' && !!caseId && !owned && !err, err };
}

const AtlasContext = createContext<ReturnType<typeof useSource> | null>(null);
export function AtlasSourceProvider({ children }: { children: ReactNode }) {
  const source = useSource();
  return <AtlasContext.Provider value={source}>{children}</AtlasContext.Provider>;
}
export function useAtlasSource() {
  const source = useContext(AtlasContext);
  if (!source) throw new Error('Atlas source provider is missing');
  return source;
}
