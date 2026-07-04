# data-pipeline/ : the offline engine (`chronoscopelab`)

The single source of algorithm truth for ChronoScope; `frontend/` and `app/` consume it, never re-implement it.
Its own venv: `.venv-pipeline` (the forecasting engines, local-only).

## Layout (the package lives directly under `data-pipeline/`)
- `chronoscopelab/pipeline.py` — orchestrator + CLI (`python -m chronoscopelab.pipeline [all|<case>] [--seed N]`)
- `chronoscopelab/registry.py` — cases grouped by CATEGORY · `chronoscopelab/live.py` — Pyodide live entrypoint
- `chronoscopelab/io/` — `contract.py` (**CONTRACT 1**) · `formats.py` (standard readers/writers) · `schema.py` (types)
- `chronoscopelab/core/` — `rng.py` (seeded determinism) · `trace.py` · `manifest.py` (**CONTRACT 2**) · `gate.py`
- `chronoscopelab/model/` : the shared pure-numpy forecasting core (Pyodide-safe): classical method ladder
- `chronoscopelab/stages/` — `preprocess → feature_extraction → train → infer → evaluate → export`
- `chronoscopelab/cases/` — documented cases

Setup + run: `scripts/setup.{sh,ps1}` then `scripts/precompute.{sh,ps1}`. See
[../docs/architecture/05_precompute-pipeline.md](../docs/architecture/05_precompute-pipeline.md).
