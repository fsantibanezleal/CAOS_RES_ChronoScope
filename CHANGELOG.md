# Changelog

All notable changes to this product. Format: `X.XX.XXX` (display); see `chronoscopelab.__version__`. Keep
`0.x` while on synthetic/early data. Tag every release.

## [0.04.000] - 2026-07-04

### Added
- ML tier: `engines/lightgbm_engine.py`, gradient boosting on lag features (LightGBM via Nixtla mlforecast),
  the M5-winning approach, behind the same `MethodForecast` contract (9 methods per case now). One point model
  on recursive lag features (lags derived from the seasonality), intervals from the in-sample residual sigma
  via the shared `gaussian_quantiles` helper. Offline-only, lazy import, graceful degradation if absent;
  bounded backtest (few windows + context cap).
- `docs/frameworks/02_mlforecast_lightgbm.md`; mlforecast/lightgbm/pandas pinned in requirements.

### Notes
- Next: the zero-shot foundation-model engines (TiRex-2, Chronos-2, TimesFM 2.5, Granite TTM r2, FlowState r1),
  the fev benchmark spine, and the streaming lane.

## [0.03.000] - 2026-07-04

### Added
- Statistical SOTA engines behind the `MethodForecast` contract: AutoARIMA, AutoETS, AutoTheta via Nixtla
  statsforecast (`engines/statsforecast_engine.py`), included in infer/evaluate/trace next to the classical
  ladder (8 methods per case now).
- A `Forecaster` abstraction (`quantiles` + `forecast` + `max_windows`) unifying the classical numpy ladder and
  the heavy engines; a `methods.all_forecasters()` combiner. The offline pipeline evaluates the combined set;
  the live lane stays classical-only (Pyodide-safe), and the pipeline degrades gracefully to classical if
  statsforecast is absent.
- Bounded backtest cost: cheap methods get many windows, AutoARIMA gets few windows plus a context cap.
- `docs/frameworks/01_statsforecast.md` (what/why/config/example); statsforecast pinned in requirements.

### Notes
- Honest results: seasonal AutoARIMA/AutoETS win on the seasonal and trend cases (MASE below 1); the
  intermittent, real-electricity, and control cases still favour the simple baselines. Next slices: the ML tier
  (mlforecast + LightGBM) and the zero-shot foundation models (TiRex-2 / Chronos-2 / TimesFM), plus a persisted
  deep reference library under `docs/research/`.

## [0.02.000] - 2026-07-03

### Changed
- Phase 3 engine swap: replaced the template EXAMPLE engine (SIR epidemic) with the real time-series
  forecasting core. The product is now about forecasting, not epidemics.

### Added
- `model/forecasters.py`: a real pure-numpy classical ladder (seasonal-naive, SES, Holt, Holt-Winters, Theta)
  with point + interval output and a normal-quantile helper; Pyodide-safe, shared by the offline stages and
  the live lane.
- Time-series ingestion CONTRACT 1 (`io/contract.py`): long-format `unique_id/ds/y` schema with a missing/
  outlier policy (reject too-short or too-missing series; flag outliers and unsorted timestamps).
- Stages rewritten for forecasting; `stages/evaluate.py` consumes the new `preqts` library for a leakage-safe
  rolling-origin backtest (MASE / WQL / coverage), and `stages/train.py` learns a global method selector.
- Real cases by category (seasonal, trend + seasonal, intermittent, near-random-walk honesty case, white-noise
  control) plus one real series: a UCI ElectricityLoadDiagrams client aggregated to hourly (`data/examples/`).
- Artifact/manifest schema `chronoscope.trace/v1` + `chronoscope.manifest/v1`; frontend contract mirror and
  replay chart updated (history + held-out actual + per-method forecast intervals + backtest metrics).

### Notes
- Later slices: heavier engines (Nixtla stack, LightGBM, zero-shot foundation models TiRex-2 / Chronos-2 /
  TimesFM 2.5 / TTM r2 / FlowState), the fev benchmark spine, the streaming lane, and the full 6-page web app.

## [0.01.000] - 2026-07-03

### Added
- ChronoScope: initial instantiation from the CAOS product-repo template (ADR-0057); package `chronoscopelab`.
  Kickoff plan + binding research dossiers: `_CAOS_MANAGE/wip/chronoscope/`.
- Offline `data-pipeline/` (`chronoscopelab`): the two data contracts (ingestion + artifact), the named staged
  pipeline (preprocess, feature_extraction, train, infer, evaluate, export), the seeded RNG, the compact trace,
  the manifest, and the measured live-vs-precompute gate.
- EXAMPLE engine: a deterministic SIR epidemic (numpy-only, Pyodide-safe), replaced in 0.02.000.
- Cases-by-category registry; a live-lane entrypoint (`live.py`); tests for both contracts + determinism.
