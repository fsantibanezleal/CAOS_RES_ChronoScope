# Changelog

All notable changes to this product. Format: `X.XX.XXX` (display); see `chronoscopelab.__version__`. Keep
`0.x` while on synthetic/early data. Tag every release.

## [0.12.000] - 2026-07-04

### Added
- GPU lane enabled (BL-113): CUDA torch `2.12.1+cu126` on the build box (RTX 4070 Laptop, ~8.5 GB, driver
  560.94 = CUDA 12.6; wheel verified to exist for the exact version, cu128 has no 2.12.1). `chronoscopelab/gpu.py`
  (`device()`/`cuda_available()`/`gpu_info()`/`summary()`) selects CUDA when present with a transparent CPU
  fallback (nothing imports torch at module load; CI/CPU clones just fall back). The pipeline logs the device
  per bake.
- `tests/test_gpu.py` (5): the device selector works with OR without a GPU (never raises), consistent info.
- `docs/guides/gpu-lane.md`: the verified install command, the 8 GB budget, and the honesty note (full
  foundation-ladder bake runs offline on this box, committed as artifacts; CI skips gracefully).
- `requirements-precompute.txt`: the cu126 install note for the GPU build box vs plain torch for CPU clones.

## [0.11.001] - 2026-07-04

### Added
- Real-dataset loaders (`chronoscopelab/data/loaders.py`): `load_uci_electricity` (15-min -> hourly, one
  meter) and `load_uci_beijing_pm25` (hourly pm2.5, NA forward-fill) read the private vault and emit
  license-cleared Contract-1 samples; `refresh_samples` regenerates the committed public-safe excerpts.
- New PUBLIC-safe real case `REAL_pm25` (Beijing PM2.5, CC-BY-4.0): daily cycle + heavy-tailed pollution
  spikes (excess kurtosis ~5, strongly non-normal) - the "real data is messy" counterweight to the synthetic
  seasonal case. Committed `data/examples/beijing_pm25_sample.csv` (480 hourly points).
- `data/examples/electricity_sample.csv` regenerated reproducibly from the vault (480 hourly points via the
  documented loader, replacing the prior opaque sample).
- `tests/test_data_loaders.py` (4): committed samples validate against Contract 1; the real cases reference
  public-safe sources; PM2.5 is heavy-tailed. `docs/cases/REAL_pm25.md`.
- 7 cases baked (was 6).

### Changed
- REAL_electricity re-baked from the regenerated (now reproducible) sample.

## [0.11.000] - 2026-07-04

### Added
- Data provenance + license registry (`chronoscopelab/data/provenance.py`): a `DataSource` record per source
  (id/name/url/license/citation + `public_artifact_ok` verdict) transcribed from the verified license dossier;
  `get_source`/`public_artifact_ok`/`public_safe_ids`/`local_only_ids`. Public-safe core: synthetic + UCI
  Electricity + UCI Beijing PM2.5 + OPSD + Monash (CC-BY). Local-only: M5/Favorita (Kaggle rules), ETT/LTSF
  (CC-BY-NC-ND), Kaggle mining-flotation + Stooq (unverified -> safe default local-only).
- License enforcement in the pipeline: the `Case` gains a `source` field; the manifest carries a `provenance`
  block; the export stage REDACTS the raw series excerpt for a local-only source (trace omits history/actual
  and per-step forecast paths, keeps only aggregate backtest metrics + sets `redacted:true`; the analysis
  artifact drops series-derived arrays, keeps scalar verdicts). So a redistribution-restricted dataset still
  contributes to the public Benchmark without leaking its values.
- Frontend contract mirror updated: `Trace.redacted`, optional `point/lower/upper`, manifest `provenance`;
  `AppPage` filters redacted methods out of the forecast chart; the contract test handles both cases. tsc clean.
- `tests/test_data_provenance.py` (8) + `tests/test_data_export_guard.py` (3): the public-safe/local-only sets
  match the dossier, and a local-only case ships metrics only (verified end to end).
- `docs/data.md` + `docs/data/provenance.md`: the per-source table + the enforcement policy.

## [0.10.000] - 2026-07-04

### Added
- `analyze` pipeline stage (`stages/analyze.py`): runs the 10-family analysis toolkit per case and bakes a
  compact `data/derived/<case>/analysis.json` (CONTRACT 2, schema `chronoscope.analysis/v1`) - the "understand
  the series" half the web workbench reads. Wired into the pipeline orchestrator (new stage between preprocess
  and feature_extraction); the manifest now carries `analysis_artifact` {path, bytes}; the frontend contract
  mirror (`contract.types.ts`) gains `AnalysisArtifactRef` so a drift fails the build.
- Honest guardrails in the bake: heavy panels length-gated (nonlinear n>=400, MF-DFA n>=200) with explicit
  `skipped` markers; per-panel error capture (a degenerate case records `{"error": ...}`, never crashes the
  bake); change-point detection on the STL-deseasonalized series when seasonality is strong (Fs>=0.64) so a
  clean seasonal series does not report spurious regime shifts; causality skipped honestly for univariate cases.
- `tests/test_stage_analyze.py`: 10 tests (all panels present, seasonal period recovered, deseasonalized
  change-points, short-series/univariate skips, degenerate-input safety, no-crash across case regimes).
- `docs/architecture/05_precompute-pipeline.md`: the analyze stage documented in the staged-pipeline table.
- Re-baked all 6 cases at seed 42 (deterministic; traces unchanged, manifests gain the analysis reference).

## [0.09.000] - 2026-07-04

### Added
- Analysis unit #10 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/causality.py`
  - Cross-correlation function with an explicit lead/lag sign convention + significance band; bidirectional
    Granger causality (`grangercausalitytests`, SSR F-test, best lag per direction); Engle-Granger
    (`coint`) + Johansen (`coint_johansen`, trace rank) cointegration WITH the enforced I(1) precondition
    (ADF on levels vs differences) marking each verdict valid/invalid. JSON-ready `causality_report`. NaN-safe.
  - `tests/test_analysis_causality.py`: 7 ground-truth tests (CCF finds the lead, Granger directionality,
    cointegrated vs independent walks, I(1)-precondition invalidation on stationary series).
  - `docs/analysis/causality.md` (theory, KaTeX, DOIs; Granger=predictability-not-mechanism + the I(1) gate) +
    `docs/analysis/assets/causality-cointegration.svg`.

### Milestone
- **The analysis toolkit ("understand the series") is COMPLETE**: all 10 diagnostic families implemented,
  tested (86 ground-truth tests green), and documented with deep pages + theme-aware SVGs -
  stationarity, autocorrelation, seasonality, filters, change-points, volatility, distribution/complexity,
  fractal/multifractal, nonlinear-dynamics/chaos, and causality/cointegration. Every method delegates to its
  authoritative library and carries the primary DOI. Next: the `analyze` pipeline stage baking these per case.

## [0.08.008] - 2026-07-04

### Added
- Analysis unit #9 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/nonlinear.py`
  - Takens time-delay embedding; Grassberger-Procaccia correlation dimension + Rosenstein largest Lyapunov
    (`nolds`); recurrence quantification (RQA: RR/DET/LAM/L_max) implemented directly (recurrence matrix +
    diagonal/vertical line statistics, truncated not subsampled to preserve diagonals); Gottwald-Melbourne
    0-1 test; IAAFT surrogates (spectrum + distribution preserving). THE SURROGATE HONESTY GATE: `likely_chaotic`
    is True only when Lyapunov>0 AND 0-1 K>0.5 AND the surrogate test rejects linearity (Osborne-Provenzale:
    colored noise fakes a low D2). JSON-ready `nonlinear_report`. NaN-safe.
  - `tests/test_analysis_nonlinear.py`: 9 ground-truth tests (logistic map flagged chaotic, white noise NOT;
    Lyapunov chaos>regular, 0-1 test separation, RQA determinism regular>noise, IAAFT invariants).
  - `docs/analysis/nonlinear.md` (theory, KaTeX, DOIs; the full surrogate-gate rationale) +
    `docs/analysis/assets/nonlinear-chaos.svg`.

## [0.08.007] - 2026-07-04

### Added
- Analysis unit #8 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/fractal.py`
  - Hurst exponent by R/S (`hurst.compute_Hc`, Anis-Lloyd) and DFA (`nolds.dfa`) with the fGn/fBm alpha->H
    mapping and an interpretation; MF-DFA generalized Hurst h(q), mass exponent tau(q), and the Legendre
    singularity spectrum f(alpha) with its width = degree of multifractality (`MFDFA`); Higuchi/Katz/Petrosian
    fractal dimension (`antropy`); the ARFIMA long-memory link d = H - 0.5; a direct DCCA cross-correlation
    coefficient. Reliability flag for short series; MF-DFA failure recorded honestly. JSON-ready `fractal_report`.
  - `tests/test_analysis_fractal.py`: 9 ground-truth tests (Hurst orders noise<random-walk, DFA alpha ~1.5
    for a walk, roughness ordering, MF-DFA narrow spectrum for a monofractal, DCCA sign for coupled vs
    independent series, short-series guards).
  - `docs/analysis/fractal.md` (theory, KaTeX, DOIs; the DFA-always-returns-alpha + H-not-equal-predictability
    honesty gate) + `docs/analysis/assets/multifractal-spectrum.svg`.
- Pins: `nolds==0.6.3`, `hurst==0.0.5`, `MFDFA==0.4.3` in requirements-precompute.txt.

## [0.08.006] - 2026-07-04

### Added
- Analysis unit #7 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/distribution.py`
  - Distribution: moments (skew, excess kurtosis), Gaussian KDE, normal Q-Q points, Jarque-Bera + Shapiro-Wilk
    normality with a combined verdict. Complexity: sample / permutation / spectral entropy (`antropy`,
    normalized), the BDS i.i.d.-vs-nonlinear test (`statsmodels`). catch22 (Lubba 2019) is OPTIONAL and
    recorded HONESTLY as unavailable when `pycatch22`'s C extension is not built (never fabricated). JSON-ready
    `distribution_report`. NaN-safe.
  - `tests/test_analysis_distribution.py`: 9 ground-truth tests (normal vs heavy-tailed vs skewed verdicts,
    Q-Q linearity, entropy orders regular<random, BDS i.i.d. vs sine, honest catch22 marker).
  - `docs/analysis/distribution.md` (theory, KaTeX, DOIs; distribution-constrains-intervals-not-the-mean
    caveat) + `docs/analysis/assets/distribution-complexity.svg`.
- Pin: `antropy==0.2.2`; pycatch22 noted optional (C-toolchain) in requirements-precompute.txt.

## [0.08.005] - 2026-07-04

### Added
- Analysis unit #6 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/volatility.py`
  - Engle ARCH-LM test for conditional heteroscedasticity (`het_arch`); GARCH/EGARCH/FIGARCH conditional
    volatility via `arch` (persistence read-out, fitted only when ARCH is significant); Box-Cox transform
    with MLE (scipy) or Guerrero seasonal lambda (`coreforecast.scalers.boxcox_lambda`), with a recorded
    positivity shift; rolling mean/std band. JSON-ready `volatility_report`. NaN-safe; fit failures recorded.
  - `tests/test_analysis_volatility.py`: 8 ground-truth tests (simulated GARCH(1,1) ARCH detection + ~0.95
    persistence recovery, homoscedastic null, MLE variance stabilization, Guerrero seasonal lambda, shift).
  - `docs/analysis/volatility.md` (theory, KaTeX, DOIs; the "GARCH informs intervals not the point" caveat) +
    `docs/analysis/assets/volatility.svg`. Research grounding: wip/chronoscope/research-volatility-transforms-2026-07-04.md.

## [0.08.004] - 2026-07-04

### Added
- Analysis unit #5 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/changepoints.py`
  - PELT (exact penalized segmentation, BIC-style default penalty recorded in the artifact) and Binary
    Segmentation via `ruptures`; OLS-CUSUM parameter-stability test (Brownian-bridge bounds); Hamilton
    Markov-switching regimes (per-point smoothed probabilities, per-regime means read from named params,
    transition matrix; fit failures recorded honestly, never crashing the bake). JSON-ready
    `changepoints_report`. NaN-safe.
  - `tests/test_analysis_changepoints.py`: 7 ground-truth tests (known break locations within +/-5 samples,
    stable-series null, CUSUM verdicts, two-regime mean recovery, honest report).
  - `docs/analysis/changepoints.md` (theory, KaTeX, DOIs; why Chow is not wrapped; BOCPD deferred to the
    streaming lane) + `docs/analysis/assets/changepoints-regimes.svg`.
- Pin: `ruptures==1.1.10` in requirements-precompute.txt.

## [0.08.003] - 2026-07-04

### Added
- Analysis unit #4 (vertical: code + tests + doc + SVG): `chronoscopelab/analysis/filters.py`
  - Hodrick-Prescott (penalized trend + cycle, exact two-way split), Baxter-King (symmetric band-pass,
    K-point end-loss) and Christiano-Fitzgerald (asymmetric full-length band-pass); EMD / CEEMDAN intrinsic
    mode functions via `EMD-signal` (completeness IMFs+residue == series asserted); CWT wavelet scalogram
    via PyWavelets (Morlet, linear detrend by default - the trend-swamps-long-scales caveat is documented;
    `scipy.signal.cwt` is removed in scipy 1.15). JSON-ready `filters_report` bakes HP/CF/EMD + a compact
    per-scale-energy scalogram summary. NaN-safe.
  - `tests/test_analysis_filters.py`: 8 ground-truth tests (HP trend recovery + exact reconstruction, BK
    end-loss, CF cycle correlation, EMD completeness + fastest-first ordering, scalogram dominant period).
  - `docs/analysis/filters.md` (theory, KaTeX, DOIs, honest caveats incl. the Hamilton critique of HP) +
    `docs/analysis/assets/filters-scales.svg`.
- Pins: `EMD-signal==1.9.0`, `PyWavelets==1.8.0`, `neuralforecast==3.1.9` in requirements-precompute.txt.

### Notes
- 0.08.002 (seasonality unit) and 0.08.001 (autocorrelation unit) are recorded below; 37 analysis tests green.

## [0.08.002] - 2026-07-04

### Added
- Analysis unit #3 (vertical): `chronoscopelab/analysis/seasonality.py` - periodogram/Welch dominant period,
  seasonal strength Fs, STL/MSTL (multi-seasonal; 2D-seasonal columns summed), seasonal subseries; 10 tests;
  `docs/analysis/seasonality.md` + `docs/analysis/assets/seasonality.svg`.

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
