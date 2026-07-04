// LIVE lane (optional, Pyodide): load the inlined chronoscopelab sources (public/pyodide/sources.json) and call
// chronoscopelab.live.run_forecast_json for a bring-your-own-series interaction in the browser. This is a STUB;
// wiring Pyodide here is a later slice. The replay path (App.tsx) is the always-available fallback (ADR-0054), so
// the product ships fully functional with this lane dormant.
export interface LiveRequest {
  case_id?: string;
  series?: { y: number[]; seasonality?: number; horizon?: number };
  seed?: number;
}

export interface LiveForecast {
  history: number[];
  horizon: number;
  seasonality: number;
  quantile_levels: number[];
  methods: Array<{ name: string; family: string; point: number[]; lower: number[]; upper: number[] }>;
}

export async function runLive(_req: LiveRequest): Promise<LiveForecast> {
  throw new Error('live (Pyodide) lane not wired yet; replay is the always-available fallback (ADR-0054)');
}
