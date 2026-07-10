# The staged precompute pipeline

`data-pipeline/chronoscopelab/pipeline.py` orchestrates the **named stages** (frozen names/signatures, rework bodies):

| Stage | Module | Does |
|---|---|---|
| preprocess | `stages/preprocess.py` | read raw and apply CONTRACT 1 (validate the series + missing/outlier policy) |
| analyze | `stages/analyze.py` | run the 10-family analysis toolkit and bake the per-case analysis panel (the "understand" half) |
| feature_extraction | `stages/feature_extraction.py` | a series to a compact fingerprint (trend/seasonal strength, acf1, intermittency) |
| train | `stages/train.py` | learn a global method selector by backtesting across the synthetic training cases (OFFLINE) |
| infer | `stages/infer.py` | fit every method on the case history and forecast the horizon |
| evaluate | `stages/evaluate.py` | leakage-safe rolling-origin backtest via preqts (MASE / WQL / coverage) |
| export | `stages/export.py` | CONTRACT 2: compact trace artifact + analysis artifact + manifest |

Run: `python -m chronoscopelab.pipeline [all|<case_id>] [--seed N]` (or `scripts/precompute.{sh,ps1}`). It writes
`data/derived/<case>/trace.json` (the forecast replay), `data/derived/<case>/analysis.json` (the diagnostics
panel), `data/derived/manifests/<case>.json` (which references both), and `index.json`.

## The `analyze` stage (the "understand the series" half of CONTRACT 2)

`stages/analyze.py` runs `chronoscopelab.analysis` (the 10 diagnostic families: stationarity, autocorrelation,
seasonality, filters, change-points, volatility, distribution/complexity, fractal/multifractal, nonlinear
dynamics, causality) on the case series and bakes one JSON-ready `analysis.json` per case. The web App's
Understand workbench reads this artifact, and the browser recomputes a live subset to match it (parity).

Guardrails keep the bake honest and tractable: heavy panels are length-gated (the nonlinear surrogate loop
needs n >= 400; MF-DFA needs >= 200) and record an explicit `skipped` marker otherwise; every panel is wrapped
so a degenerate case records `{"error": ...}` instead of crashing the whole bake; and change-point detection
runs on the STL-deseasonalized series when seasonality is strong (Fs >= 0.64), so a clean seasonal series does
not report every peak and trough as a spurious regime shift. Causality runs only when a case carries a
covariate series (otherwise it is honestly skipped as univariate). The manifest carries the analysis artifact
path + byte size under `analysis_artifact` (mirrored by `frontend/src/lib/contract.types.ts`).

The stage names and signatures are frozen; the bodies hold the real engine. This slice ships the pure-numpy
classical ladder scored by preqts; later slices add the heavier engines (Nixtla, LightGBM, zero-shot foundation
models) pinned in `data-pipeline/requirements.txt` and documented in [../frameworks/](../frameworks/), behind the
same MethodForecast contract. No hand-rolled toy substitute for an engine the research prescribed.
