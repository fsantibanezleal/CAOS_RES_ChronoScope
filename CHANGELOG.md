# Changelog

All notable changes to this product. Format: `X.XX.XXX` (display); see `chronoscopelab.__version__`. Keep
`0.x` while on synthetic/early data. Tag every release.

## [0.08.001] - 2026-07-04

### Added
- Analysis unit #2 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/autocorrelation.py`
  - ACF (FFT) + PACF (Durbin-Levinson `method='ld'`) with the Bartlett +/-1.96/sqrt(n) band and
    significant-lag read-out; Ljung-Box + Box-Pierce portmanteau (with `model_df` for residual diagnostics);
    Durbin-Watson; lag-plot pairs; a JSON-ready `autocorrelation_report` + a conservative Box-Jenkins
    `_identify` hint (AR/MA/ARMA/white-noise). NaN-safe.
  - `tests/test_analysis_autocorrelation.py`: 10 ground-truth tests (AR(1), MA(1), white-noise, DW).
  - `docs/analysis/autocorrelation.md` (theory, KaTeX, DOIs) + `docs/analysis/assets/correlograms.svg`.
- Infra: neuralforecast 3.1.9 installed in `.venv-pipeline` (deep-ladder training spine; pin follows).

## [0.08.000] - 2026-07-04

### Added
- Analysis toolkit (the "understand the series" half), built backend-first per the re-grounded plan.
  - `chronoscopelab/analysis/stationarity.py`: ADF, KPSS, Phillips-Perron, DF-GLS, Zivot-Andrews (each
    delegated to its authoritative library - statsmodels + `arch` - in one NaN-safe API that carries the
    primary DOI), the four-quadrant `combined_verdict`, and the FPP3 differencing-order selection
    (`ndiffs` KPSS-sequential, `nsdiffs` via seasonal strength `Fs >= 0.64`; no pmdarima). Full
    `stationarity_report` for the baked artifact.
  - `tests/test_analysis_stationarity.py`: 10 ground-truth tests (opposite-null polarity, white-noise vs
    random-walk verdicts, differencing recovery, seasonal strength, NaN-safety).
  - `docs/analysis.md` + `docs/analysis/stationarity.md`: deep page (theory, KaTeX equations, DOIs, what
    it is/is NOT) with a theme-aware SVG decision diagram (`docs/analysis/assets/`).
  - `requirements-precompute.txt`: pins the offline/GPU lane engines (adds `arch==8.0.0`).

### Notes
- Vertical build: code + tests + deep doc + SVG in one commit per method (Entry_point rule 7). Next analysis
  units: autocorrelation (ACF/PACF/Ljung-Box), seasonality (periodogram/MSTL), decomposition, then the ladder.

## [0.07.000] - 2026-07-04

### Added
- Web app slice B: the six-page structure with hash-routed nav (works on Pages without 404 tricks), a header
  with the product mark + GitHub link, and the ADR-0016 footer.
  - App = the interactive workbench (refactored into `pages/AppPage.tsx`).
  - `pages/Introduction.tsx`, `Methodology.tsx` (term-by-term math via KaTeX), `Implementation.tsx`,
    `Experiments.tsx`, `Benchmark.tsx` (a cross-case MASE table built live from every committed manifest/trace,
    winner-per-case highlighted, never hand-typed).
  - `components/{Math,doc}.tsx` shared primitives; KaTeX dependency added.
- Render smoke updated to assert the six-page nav; 8 frontend tests + tsc/vite green.

### Notes
- Next: i18n (EN/ES) + light/dark theming, the ADR-0058 architecture modal, the ONNX live deep tier
  (onnxruntime-web), the preqts streaming tab, and full light/dark screenshot-verify.

## [0.06.000] - 2026-07-04

### Added
- Web app slice A: the App is now a real interactive workbench (not the minimal replay page).
  - `frontend/src/lib/liveEngine.ts`: a TypeScript port of the classical ladder (seasonal-naive, SES, Holt,
    Holt-Winters, Theta) + normal quantile, so the classical tier is genuinely LIVE in the browser.
  - Parity: `scripts/gen_parity_fixture.py` + `frontend/src/lib/__fixtures__/parity.json` +
    `src/test/parity.test.ts` assert the TS engine matches the Python core within tolerance (honest "live").
  - `frontend/src/lib/synthetic.ts`: seeded synthetic generators (seasonal, trend+seasonal, intermittent,
    random-walk, white-noise) driven by live knobs.
  - `render/WorkbenchChart.tsx`: interactive SVG chart with a hover cursor that reads out every visible
    series' value; history + held-out actual + per-method point and prediction interval.
  - `App.tsx`: source selector (Synthetic live / Baked case replay), method toggles across the whole ladder,
    and a per-method leaderboard (classical live-computed; statistical/ML/foundation from the baked backtest).
  - `src/test/app-render.test.tsx`: server-render smoke (the workbench mounts, the live engine runs).
- 8 frontend tests (parity + contract + render) + tsc/vite green.

### Notes
- Next web-app slices (wip/chronoscope/webapp-plan.md): the six documentation pages + nav, i18n + theming,
  the ADR-0058 architecture modal, the ONNX live deep tier (onnxruntime-web), and the preqts streaming tab.

## [0.05.001] - 2026-07-04

### Changed
- Public-readiness for the GitHub Pages deploy at `chronoscope.fasl-work.com` (the correct deploy class for a
  static, no-backend showcase; VPS is only for a hard backend or private content): added the MIT `LICENSE`,
  removed the stale SIR `data/examples/params.csv`, and changed `deploy-pages.yml` to build the SPA over the
  COMMITTED foundation-baked artifacts (no CI regeneration, which would drop the foundation tier CI cannot run).

## [0.05.000] - 2026-07-04

### Added
- Zero-shot foundation-model tier (SOTA), run OFFLINE on local checkpoints: `engines/chronos_engine.py`
  wires Amazon Chronos-Bolt (Apache-2.0) behind the same `MethodForecast` contract, with a module-level
  pipeline cache so a checkpoint loads once per process. On the seasonal case it reaches the lowest MASE of
  the whole ladder (below AutoARIMA and the seasonal-naive baseline), baked into the committed artifacts.
- The tier is OPT-IN and heavy: deps in `data-pipeline/requirements-foundation.txt` (torch CPU +
  chronos-forecasting), checkpoints in the model vault (`CHRONOSCOPE_MODEL_ROOT`), enabled with
  `CHRONOSCOPE_ENABLE_FOUNDATION=1` for canonical baking. It degrades gracefully to the classical +
  statistical + ML ladder when absent, so CI and the test suite stay fast.
- `docs/frameworks/03_chronos.md`.

### Notes
- The offline pipeline now does the hard processing (foundation-model inference) and bakes it into the
  artifacts. Follow-ups: Chronos-2 / TimesFM 2.5 / Granite TTM r2 / FlowState r1 / TiRex-2 (own loaders),
  ONNX export of a small deep model for the browser live lane, and the real interactive 6-page web app
  (the core deliverable: play with the whole ladder live or via replay).

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
