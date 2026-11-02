# ChronoScope: the time-series forecasting method atlas

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_RES_ChronoScope/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_RES_ChronoScope)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_RES_ChronoScope?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tags)
[![Live demo](https://img.shields.io/badge/demo-live-2ea44f)](https://chronoscope.fasl-work.com)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21508920-blue)](https://doi.org/10.5281/zenodo.21508920)

**Live app: <https://chronoscope.fasl-work.com>**

Preprint (CC-BY-4.0): *"Prequential Streaming Evaluation of Stateful Time-Series
Forecasters with Online Conformal Calibration"*, concept DOI
[10.5281/zenodo.21508920](https://doi.org/10.5281/zenodo.21508920) (source in
[`manuscripts/prequential-streaming-conformal/`](manuscripts/prequential-streaming-conformal/)).

ChronoScope is an interactive research atlas of time-series forecasting. It takes a series, understands
it with the classical diagnostic toolkit (ten analysis families: stationarity, autocorrelation,
seasonality, filters/decomposition, change points, volatility, distribution/complexity, fractals,
nonlinear dynamics, causality), and compares **22 forecast variants on common final holdouts**.
The default comparison freshly executes all 22 variants on original contiguous histories, with
exact package versions and checkpoint revisions. An explicit selector retains the earlier
comparison of fourteen frozen paths, five corrected light methods and three combinations.
ContextMemory did not improve mean MASE
over its recency-only ablation. Every case and the negative result remain available.

The [implementation reassessment](docs/research/2026-11-01-method-reevaluation.md) records the
HoltWinters seasonal-phase and finite-history Theta corrections, original unequal rolling-origin
budgets, method provenance and the limits of the comparison. Diagnostic associations do not establish
a causal explanation of model rankings.

- **15 committed cases** (seeded synthetic across regimes + CC-BY real data: UCI Electricity, Beijing
  PM2.5, two real M4/Monash series + honesty controls), each baked with the full ladder, the ten-family
  analysis panel, and a prequential streaming bench.
- **Foundation tier**: Chronos-Bolt, Chronos-2, TimesFM 2.5 (local Apache-2.0 checkpoints, GPU) and
  TiRex-2 via native Linux/WSL CUDA inference (its sLSTM kernels have no Windows wheels).
  TimesFM 3.0 is documented separately with its noncommercial, nonproduction weight terms.
- **Prequential streaming evaluation**: predict, score, then ingest, with an explicit covariate-arrival
  policy and online interval calibration (ACI / Conformal-PID), implemented through
  the published PyPI package [`preqts`](https://pypi.org/project/preqts/).
- **The web app replays the committed artifacts** (nothing heavy runs in the browser) while the classical
  ladder + an ONNX NLinear run live in-browser, parity-checked against the Python core.

## Quickstart

```bash
# Numbered scripts have PowerShell equivalents in scripts/local.
./scripts/local/00_install-prereqs.sh
./scripts/local/01_init.sh
# Existing admitted artifacts are sufficient for development.
./scripts/local/03_dev.sh
# Optional generation creates an external candidate; promotion is explicit.
CAOS_TEMP_ROOT=/your/external/scratch ./scripts/local/02_generate-data.sh
```

See [local workflows](scripts/local/README.md) for staged generation and
[fresh model execution](docs/guides/fresh-reevaluation.md) for the separate Linux/GPU
runtime. The default generation path verifies the admitted fresh experiment; it does not
pretend to rerun foundation models. Local scientific tests, notebook reproduction,
frontend checks and the browser matrix are recorded separately from remote delivery.

The [manuscript review set](manuscripts/README.md) contains the detailed report, the
contextual-combination paper and a revision of the streaming study. These are local
candidates; external publication and the strict manuscript release gate remain pending.


## Areas

| Area | Folder | Status | What it holds |
|---|---|---|---|
| Web | [frontend/](frontend/) | active | Interactive atlas and static app shell integration |
| API | [app/](app/) | dormant: static Pages deployment serves committed artifacts | Optional read-only FastAPI service |
| Core pipelines | [data-pipeline/](data-pipeline/) | active | Forecasting engines analysis stages and artifact export |
| Packages | [preqts on PyPI](https://pypi.org/project/preqts/) | active | Prequential forecast evaluation and calibration library |
| Notebooks | [notebooks/](notebooks/) | active | Eight executed English and Spanish worked forecasting lessons |
| Data | [data/](data/) | active | Case inputs provenance and committed derived artifacts |
| Contracts | [docs/contracts/](docs/contracts/) | active | Artifact schemas compatibility and boundary records |
| Documentation | [docs/](docs/) | active | Methods cases architecture and user guides |
| Tests and gates | [tests/](tests/) [scripts/](scripts/) | active | Python TypeScript and artifact validation gates |
| Deploy | [deploy/](deploy/) | active | GitHub Pages target and deployment notes |

## The two data contracts

1. **Ingestion contract: `raw → pipeline`** (`chronoscopelab/io/contract.py`): schema, dtypes, missing
   policy, and the per-source **license verdict** (`chronoscopelab/data/provenance.py`). The export stage
   enforces it: a local-only-licensed source ships aggregate metrics only, never raw values.
2. **Artifact contract: `pipeline → web`** (`chronoscopelab.trace/v2`, `chronoscope.analysis/v1`,
   `chronoscope.streaming/v1` + per-case manifests): mirrored in TypeScript
   (`frontend/src/lib/contract.types.ts`); a schema divergence breaks the build, and
   `scripts/check_artifacts.py` (CI) fails on any byte/ladder/feature drift.

## Repo map

| Path | What lives there |
|---|---|
| `data-pipeline/chronoscopelab/` | the Python package: staged pipeline, 10 analysis families, engines (statsforecast, mlforecast, neuralforecast, torch-direct, Chronos/TimesFM/TiRex), provenance registry |
| `data/derived/` | the committed per-case artifacts (trace + analysis + streaming + manifests), seed-deterministic, never hand-edited |
| `frontend/` | the React SPA (shared `@fasl-work/caos-app-shell`, uPlot workbench, onnxruntime-web live tier) |
| `docs/` | the wiki: research dossiers, per-family analysis theory, architecture, per-case write-ups, guides |
| `tools/tirex2_wsl/` | the WSL2 lane for TiRex-2 (CUDA-in-WSL bake bridge) |
| `tests/` | Scientific, contract, numerical parity, fresh admission, notebook, guard and planted-defect checks |

## Hard rules

- **Evidence boundaries**: baked artifacts record what is unavailable rather than faking it; the white-noise
  and near-random-walk cases provide limited baseline checks, not proof against all leakage; n_windows per
  method is recorded; local-only data never ships.
- **Reproduction**: seeded lightweight numerical artifacts and notebook outputs have byte checks.
  Fresh GPU runs record packages, checkpoints and execution timings; cross-runtime bitwise identity
  and identical hardware timing are not promised.
- **Tests never write canonical artifacts** (sandboxed via `CHRONOSCOPE_DERIVED_DIR`).

## License

[MIT](LICENSE). Third-party model weights and data keep their own terms: Chronos / TimesFM / TiRex
checkpoints are Apache-2.0; UCI Electricity, Beijing PM2.5 and Monash/M4 excerpts ship under CC-BY 4.0
with attribution (see `docs/data/provenance.md`).
