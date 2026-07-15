# ChronoScope — the time-series forecasting method atlas

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_RES_ChronoScope/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_RES_ChronoScope)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_RES_ChronoScope?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tags)
[![Live demo](https://img.shields.io/badge/demo-live-2ea44f)](https://chronoscope.fasl-work.com)

**Live app: <https://chronoscope.fasl-work.com>**

ChronoScope is an interactive research atlas of time-series forecasting. It takes a series, UNDERSTANDS
it with the classical diagnostic toolkit (ten analysis families: stationarity, autocorrelation,
seasonality, filters/decomposition, change points, volatility, distribution/complexity, fractals,
nonlinear dynamics, causality), runs a **19-method forecast ladder** across it (5 classical + 3
statistical + LightGBM + 6 deep + 4 foundation models), and shows honestly where each family wins and
where it fails. The thesis: **the diagnosis explains the leaderboard** — no free lunch, and the atlas
shows why.

- **15 committed cases** (seeded synthetic across regimes + CC-BY real data: UCI Electricity, Beijing
  PM2.5, two real M4/Monash series + honesty controls), each baked with the full ladder, the ten-family
  analysis panel, and a prequential streaming bench.
- **Foundation tier**: Chronos-Bolt, Chronos-2, TimesFM 2.5 (local Apache-2.0 checkpoints, GPU) and
  TiRex-2 via an opt-in **WSL2 lane** (its sLSTM kernels have no Windows wheels).
- **The novel lane**: prequential (predict → observe → update) evaluation of stateful forecasters with an
  explicit covariate-arrival policy and online conformal calibration (ACI / Conformal-PID) — extracted as
  the published PyPI package [`preqts`](https://pypi.org/project/preqts/).
- **The web app replays the committed artifacts** (nothing heavy runs in the browser) while the classical
  ladder + an ONNX NLinear run LIVE in-browser, parity-checked against the Python core.

## Quickstart

```bash
# 1. reproducible environments (pinned per lane; py3.12 for the pipeline)
./scripts/setup.sh                      # or scripts/setup.ps1 on Windows

# 2. bake every case: forecasts + analysis + streaming -> data/derived/ (+ manifests)
python scripts/bake.py all              # GPU lanes opt-in via CHRONOSCOPE_ENABLE_* env flags

# 3. the gates: determinism, both data contracts, artifact drift, TS<->Python parity
python -m pytest tests/ -q
python scripts/check_artifacts.py

# 4. the web app consumes the artifacts (copy-data enforces the artifact contract)
cd frontend && npm ci && npm run dev
```

## The two data contracts

1. **Ingestion contract — `raw → pipeline`** (`chronoscopelab/io/contract.py`): schema, dtypes, missing
   policy, and the per-source **license verdict** (`chronoscopelab/data/provenance.py`). The export stage
   ENFORCES it: a local-only-licensed source ships aggregate metrics only, never raw values.
2. **Artifact contract — `pipeline → web`** (`chronoscopelab.trace/v2`, `chronoscope.analysis/v1`,
   `chronoscope.streaming/v1` + per-case manifests): mirrored in TypeScript
   (`frontend/src/lib/contract.types.ts`); a schema divergence breaks the build, and
   `scripts/check_artifacts.py` (CI) fails on any byte/ladder/feature drift.

## Repo map

| Path | What lives there |
|---|---|
| `data-pipeline/chronoscopelab/` | the Python package: staged pipeline, 10 analysis families, engines (statsforecast, mlforecast, neuralforecast, torch-direct, Chronos/TimesFM/TiRex), provenance registry |
| `data/derived/` | the committed per-case artifacts (trace + analysis + streaming + manifests) — seed-deterministic, never hand-edited |
| `frontend/` | the React SPA (shared `@fasl-work/caos-app-shell`, uPlot workbench, onnxruntime-web live tier) |
| `docs/` | the wiki: research dossiers, per-family analysis theory, architecture, per-case write-ups, guides |
| `tools/tirex2_wsl/` | the WSL2 lane for TiRex-2 (CUDA-in-WSL bake bridge) |
| `tests/` | 170 tests in 26 modules: ground-truth analysis tests, contract + determinism + parity + gate tests |

## Hard rules

- **Honesty gates everywhere**: baked artifacts record what is unavailable rather than faking it; control
  cases (white noise, random walk) exist so a "win" there flags harness leakage; n_windows per method is
  recorded; local-only data never ships.
- **Determinism**: every bake is a pure function of (case, seed); no timestamps in artifacts; re-baking is
  a no-op diff unless code changed.
- **Tests never write canonical artifacts** (sandboxed via `CHRONOSCOPE_DERIVED_DIR`).

## License

[MIT](LICENSE). Third-party model weights and data keep their own terms: Chronos / TimesFM / TiRex
checkpoints are Apache-2.0; UCI Electricity, Beijing PM2.5 and Monash/M4 excerpts ship under CC-BY 4.0
with attribution (see `docs/data/provenance.md`).
