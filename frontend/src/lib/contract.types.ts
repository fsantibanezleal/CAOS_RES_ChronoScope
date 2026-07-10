// CONTRACT 2 mirror (frontend side). MUST stay in lock-step with the Python schemas in
// data-pipeline/chronoscopelab/core/{trace.py, manifest.py}. A drift here makes `tsc` fail, so the contract is
// enforced at BUILD time (the web cannot ship reading a shape the pipeline does not produce).

export interface MethodBacktest {
  mase: number | null;
  wql: number | null;
  coverage: number | null;
  n_windows: number | null;
}

export interface MethodForecast {
  name: string;
  family: string; // "classical" | "ml" | "deep" | "foundation"
  // point/lower/upper are OMITTED for a license-redacted (local-only) source: only the aggregate backtest
  // ships, so the method still appears in the public Benchmark without leaking the source's values.
  point?: number[];
  lower?: number[];
  upper?: number[];
  backtest: MethodBacktest;
}

export interface TraceSummary {
  best_method: string | null;
  best_mase: number | null;
  nominal_coverage: number | null;
}

export interface Trace {
  schema: string; // "chronoscope.trace/v1"
  case_id: string;
  seasonality: number;
  horizon: number;
  quantile_levels: number[];
  redacted: boolean; // true = source license forbids redistribution; history/actual/paths omitted (metrics only)
  history_len: number; // forecast x-positions start at history_len .. history_len + horizon - 1
  history_index: number[]; // x positions of the (decimated) history points ([] when redacted)
  history: number[]; // [] when redacted
  actual: number[]; // held-out truth over the horizon ([] when redacted)
  methods: MethodForecast[];
  summary: TraceSummary;
}

export interface ArtifactRef {
  path: string;
  format: string;
  trace_schema: string;
  bytes: number;
}

export interface GateVerdict {
  lane: string;
  pure_python: boolean;
  wheels: string[];
  trace_bytes: number;
  run_ms_budget: number;
  trace_bytes_budget: number;
  reasons: string[];
}

export interface SeriesDescriptors {
  n_obs: number;
  seasonality: number;
  horizon: number;
  source: string;
  mean: number;
  std: number;
  trend_slope: number;
  seasonal_strength: number;
  acf1: number;
  pct_zeros: number;
}

// The "understand the series" half of CONTRACT 2 (chronoscope.analysis/v1): a pointer to the baked analysis
// panel the App's Understand workbench reads. Optional so cases without a baked analysis still validate.
export interface AnalysisArtifactRef {
  path: string;
  format: string;
  analysis_schema: string; // "chronoscope.analysis/v1"
  bytes: number;
}

// The streaming bench artifact (chronoscope-streaming-v1): preqts prequential trajectories (rolling MASE,
// rolling coverage vs nominal, cumulative compute cost) for the raw vs ACI- vs PID-calibrated methods.
// Aggregate metrics only, so it ships for every source regardless of license.
export interface StreamingArtifactRef {
  path: string;
  format: string;
  streaming_schema: string; // "chronoscope-streaming-v1"
  bytes: number;
}

export interface CaseManifest {
  schema: string; // "chronoscope.manifest/v1"
  case_id: string;
  category: string;
  real_or_synthetic: string;
  expected_band: string;
  engine: { package: string; version: string; model: string };
  provenance: { source: string; license: string; citation: string; public_artifact_ok: boolean };
  analysis_artifact: AnalysisArtifactRef | null;
  streaming_artifact: StreamingArtifactRef | null;
  series: SeriesDescriptors;
  seed: number;
  artifact: ArtifactRef;
  lane: 'live' | 'precompute';
  gate: GateVerdict;
  flags: Array<Record<string, string>>;
  best_method: string | null;
  metrics: Record<string, number | null>;
}

export interface CaseIndexEntry {
  case_id: string;
  category: string;
  manifest_path: string;
}

export interface CaseIndex {
  schema: string; // "chronoscope.index/v1"
  engine_version: string;
  n_cases: number;
  cases: CaseIndexEntry[];
}
