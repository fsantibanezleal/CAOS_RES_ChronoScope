# ChronoScope software design description

Status: current product design; reviewed 2026-11-01 against repository source and committed artifacts.

## Problem and non-goals

ChronoScope packages time-series diagnostics, point forecasting, interval forecasts, and prequential streaming evaluations in a reproducible research atlas. Its primary boundary is analysis and comparison of selected cases. It is not a production forecasting service, a universal model ranking, a guarantee of coverage under arbitrary drift, or evidence of a new forecasting method.

The streaming study is finite: 15 selected cases, four real series, eleven generated series, one-step horizons, four forecasting/calibration configurations, and stored rolling trajectories. Runtime measurements are machine-dependent. The current artifact does not preserve individual online score-buffer states or complete execution provenance for an exact replay of each controller update.

## Executive brief

Data file: content/executive.json

The executive view is intended to summarize the atlas's evaluation scope and evidence boundaries for readers deciding whether a reported comparison applies to their forecasting workflow. A sourced, reviewable decision brief remains to be prepared.

## Research basis

- Dawid's prequential approach motivates predict-then-observe evaluation: https://doi.org/10.2307/2981683
- Gibbs and Candès specify adaptive conformal inference under distribution shift: https://arxiv.org/abs/2106.00170
- Angelopoulos, Candès, and Tibshirani describe conformal PID control for time-series prediction: https://arxiv.org/abs/2307.16895
- Hyndman and Koehler discuss forecast accuracy measures and their limitations: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Gneiting and Raftery establish proper scoring rules for probabilistic forecasts: https://doi.org/10.1198/016214506000001437

The implementation details in Sections III and IV of the manuscript were checked against `data-pipeline/chronoscopelab/stages/streaming.py`, the installed `preqts==0.3.0` package behavior, and `data/derived/*/streaming.json`.

UNVERIFIED: Stored trajectories do not contain per-step controller state, complete execution-environment identifiers, or repeated-seed replications; the released data therefore cannot establish exact state replay, runtime generalization, or sensitivity to controller gains.

## Sizing and contracts

The committed index lists 15 cases. Four are real-data excerpts and eleven are generated cases, including white-noise and near-random-walk controls. Each case can carry trace, analysis, streaming, and manifest artifacts. Contract 1 validates source provenance and license policy; Contract 2 connects pipeline artifacts to the TypeScript consumer. Redacted sources expose aggregate metrics without raw values or paths.

## Technology and versions

| component | package | version | use | alternative considered |
|---|---|---|---|---|
| frontend | @fasl-work/caos-app-shell | 0.19.11 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @testing-library/react | 16.3.2 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @types/katex | 0.16.8 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @types/node | 22.20.0 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @types/react | 19.2.17 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @types/react-dom | 19.2.3 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | @vitejs/plugin-react | 6.1.2 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | antropy | 0.2.2 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | arch | 8.0.0 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | chronos-forecasting | 2.3.1 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | coreforecast | 0.0.17 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | emd-signal | 1.9.0 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | hurst | 0.0.5 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | jsdom | 29.1.1 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | katex | 0.16.11 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | lightgbm | 4.6.0 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | lucide-react | 0.469.0 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | mfdfa | 0.4.3 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend/package.json overrides | minimatch | 11.0.1 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | mlforecast | 1.0.31 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | neuralforecast | 3.1.9 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | nolds | 0.6.3 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | numpy | 2.4.6 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | onnxruntime-web | 1.27.0 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | pandas | 2.3.3 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | playwright | 1.64.1 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | preqts | 0.3.0 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | pycatch22 | 0.4.5 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-dev.txt | pytest | 9.1.1 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | pywavelets | 1.8.0 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | react | 19.2.7 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | react-dom | 19.2.7 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | react-router | 8.5.1 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-dev.txt | ruff | 0.15.18 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | ruptures | 1.1.10 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | scipy | 1.15.3 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | statsforecast | 2.0.3 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | statsmodels | 0.14.6 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| requirements-precompute.txt | torch | 2.12.1 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | typescript | 5.9.3 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | uplot | 1.6.32 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| requirements-precompute.txt | utilsforecast | 0.2.16 | Python dependency; see pinned requirements | Not assessed as a substitute in this release. |
| frontend | vite | 8.3.5 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | vitest | 5.0.5 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
| frontend | zustand | 5.0.2 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |

## Resources

| stage | memory | disk | time | where it runs |
|---|---|---|---|---|
| bake | GPU lane depends on selected model; case artifacts are committed | writes case artifacts under data/derived | full run depends on enabled model lanes; not run in CI | local pipeline environment |
| tests | bounded by test process and selected fixtures | reads repository fixtures; tests isolate generated artifacts | local suite; not run in the static deployment workflow | developer environment |
| build | Node process; static bundle only | writes frontend/dist | npm build; no model training | frontend workspace and Pages CI |
| deploy | GitHub Pages static hosting | serves frontend/dist and committed artifacts | one Pages workflow run per deployment | GitHub Actions |

## Lanes

The offline pipeline creates forecast, analysis, and streaming artifacts. The browser replays those committed artifacts and runs a small set of methods client-side, including seasonal-naive, exponential smoothing, and NLinear ONNX. The optional FastAPI directory is dormant. GitHub Pages is the sole declared deployment target; no request-time Python backend is required.

## Method ladder

| id | tier | method | acceptance criterion | gate |
|---|---|---|---|---|
| CL-1 | classical | Seasonal-naive and local smoothing methods | Forecast outputs match the checked parity fixture and preserve declared horizon length. | `tests/test_forecasters.py` |
| ST-1 | sota | Selected statistical, machine-learning, neural, and pretrained model implementations | Committed artifacts validate against manifests and contain the declared methods or an explicit unavailable reason. | `scripts/check_artifacts.py` |

## Beyond the state of the art

No validated new forecasting method is claimed in this release. The preqts harness is an evaluation library; ACI and Conformal-PID are calibration procedures described in prior literature. The manuscript documents an empirical comparison on selected finite cases, not a method contribution. A qualifying method claim requires a defined algorithm, source implementation, adversarial validation, comparison against relevant prior work, and a manuscript supported by those results.

## Cases

The case matrix includes UCI Electricity, Beijing PM2.5, M4 daily, M4 hourly, and generated level-shift, GARCH, intermittent-demand, long-memory, seasonal, promotional, fractional, Mackey-Glass, white-noise, and near-random-walk cases. The two controls are limited protocol checks; they do not prove absence of leakage across all inputs or pretrained model corpora.

## Oracles

The artifact scripts compare committed output structure, manifest references, and method counts. Python unit tests cover forecasting implementations and streaming wrappers. The TypeScript contract test checks committed index-manifest-trace consistency; the parity test compares browser and Python point forecasts on a fixed fixture. Coverage target plots are computed from stored rolling trajectories. Current stored results show mean absolute deviation from nominal 0.8 coverage of 0.0057 for ACI, 0.0060 for PID, 0.0416 for Theta, and 0.0599 for seasonal-naive across the 15 cases; these are finite-case summaries, not general guarantees.

## Deploy driver

`.github/workflows/deploy-pages.yml` installs frontend dependencies, builds the static app over committed artifacts, uploads `frontend/dist`, and deploys GitHub Pages. The workflow is triggered from `main`; local validation does not establish a live deployment or owner acceptance.

## Risks and kill criteria

Do not publish a claim of a new forecasting method, universal calibration, general runtime advantage, or broad leaderboard superiority without new evidence. Stop a release if source licensing is unresolved, artifact and consumer shapes diverge, a control case reveals a material harness defect, or the deployed commit and artifact identity cannot be established. The required novel-method tier and an evidence-backed technical report are currently absent, so the corresponding template readiness checks remain open.

## ADR fit

| ADR | Decision in ChronoScope |
|---|---|
| ADR-0002 | The FastAPI service remains dormant; the product serves static committed artifacts. |
| ADR-0055 | GitHub Pages is the only deploy target. |
| ADR-0057 | The application keeps explicit pipeline and artifact boundaries. |
| ADR-0070 | Focus mode applies to the forecasting atlas surface. |
| ADR-0074 | CI checks repository integrity and artifact consistency without running the heavy bake. |
| ADR-0078 | The shell measurement gate is required before declaring the app-shell migration complete. |
