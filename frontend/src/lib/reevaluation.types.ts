export interface HoldoutMetrics {
  mae: number; rmse: number; mase: number | null; coverage: number;
  mean_width: number; msis: number | null; wql: number | null;
}
export interface ReevaluatedMethod {
  name: string; family: string; source: string;
  point: number[]; lower: number[]; upper: number[];
  metrics: HoldoutMetrics;
  expert_weights?: Record<string, number>;
  training_origins?: number[];
}
export interface ReevaluatedCase {
  case_id: string; category: string; seasonality: number; horizon: number;
  history_length: number; actual: number[]; methods: ReevaluatedMethod[];
  legacy_backtest_window_counts: Record<string, number>;
}
export interface Reevaluation {
  schema: 'chronoscope.reevaluation/v1';
  protocol: { name: string; heavy_forecasts: string; light_forecasts: string; limits: string };
  source_engine_version: string;
  trace_sha256: Record<string, string>; code_sha256: Record<string, string>;
  cases: ReevaluatedCase[];
  summary: { name: string; cases: number; mean_mase: number; mean_coverage: number }[];
}
