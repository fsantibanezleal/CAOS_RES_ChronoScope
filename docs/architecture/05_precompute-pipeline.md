# The staged precompute pipeline

`data-pipeline/chronoscopelab/pipeline.py` orchestrates the **named stages** (frozen names/signatures, rework bodies):

| Stage | Module | Does |
|---|---|---|
| preprocess | `stages/preprocess.py` | read raw and apply CONTRACT 1 (validate the series + missing/outlier policy) |
| feature_extraction | `stages/feature_extraction.py` | a series to a compact fingerprint (trend/seasonal strength, acf1, intermittency) |
| train | `stages/train.py` | learn a global method selector by backtesting across the synthetic training cases (OFFLINE) |
| infer | `stages/infer.py` | fit every method on the case history and forecast the horizon |
| evaluate | `stages/evaluate.py` | leakage-safe rolling-origin backtest via preqts (MASE / WQL / coverage) |
| export | `stages/export.py` | CONTRACT 2: compact artifact + manifest |

Run: `python -m chronoscopelab.pipeline [all|<case_id>] [--seed N]` (or `scripts/precompute.{sh,ps1}`). It writes
`data/derived/<case>/trace.json` + `data/derived/manifests/<case>.json` + `index.json`.

The stage names and signatures are frozen; the bodies hold the real engine. This slice ships the pure-numpy
classical ladder scored by preqts; later slices add the heavier engines (Nixtla, LightGBM, zero-shot foundation
models) pinned in `data-pipeline/requirements.txt` and documented in [../frameworks/](../frameworks/), behind the
same MethodForecast contract. No hand-rolled toy substitute for an engine the research prescribed.
