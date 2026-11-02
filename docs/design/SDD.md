# ChronoScope software design description

Status: current product design; reviewed 2026-11-01 against repository source and committed artifacts.

## Problem and non-goals

ChronoScope packages time-series diagnostics, point forecasting, interval forecasts, and prequential streaming evaluations in a reproducible research atlas. Its primary boundary is analysis and comparison of selected cases. It is not a production forecasting service, a universal model ranking, a guarantee of coverage under arbitrary drift, or evidence of a new forecasting method.

The streaming study is finite: 15 selected cases, four real series, eleven generated series, one-step horizons, four forecasting/calibration configurations, and stored rolling trajectories. Runtime measurements are machine-dependent. The current artifact does not preserve individual online score-buffer states or complete execution provenance for an exact replay of each controller update.

## Executive brief

Data file: content/executive.json

The executive view frames demand-planning decisions, forecasting adjustments, uncertainty, roles and review actions. Its source trail and the distinction between measured figures and author-estimated cause weights are recorded in `docs/research/2026-11-01-executive-evidence.md`.

## Research basis

- Dawid's prequential approach motivates predict-then-observe evaluation: https://doi.org/10.2307/2981683
- Gibbs and Candès specify adaptive conformal inference under distribution shift: https://arxiv.org/abs/2106.00170
- Angelopoulos, Candès, and Tibshirani describe conformal PID control for time-series prediction: https://arxiv.org/abs/2307.16895
- Hyndman and Koehler discuss forecast accuracy measures and their limitations: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Gneiting and Raftery establish proper scoring rules for probabilistic forecasts: https://doi.org/10.1198/016214506000001437
- Hyndman and Billah derive the finite-history Theta point equation: https://robjhyndman.com/papers/Theta.pdf
- Hyndman and Athanasopoulos specify additive seasonal phase continuation: https://otexts.com/fpp3/holt-winters.html
- Montero-Manso et al. learn feature-dependent forecast weights across a reference collection: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Cerqueira et al. predict expert losses for dynamic aggregation: https://doi.org/10.1007/s10994-018-05774-y

The refreshed implementation audit and sources are in `docs/research/2026-11-01-method-reevaluation.md`; the fixed experimental proposal and its refutation criteria are in `docs/research/2026-11-01-context-memory-proposal.md`. The executive brief has a separate evidence ledger.

The implementation details in Sections III and IV of the manuscript were checked against `data-pipeline/chronoscopelab/stages/streaming.py`, the installed `preqts==0.3.0` package behavior, and `data/derived/*/streaming.json`.

UNVERIFIED: Stored trajectories do not contain per-step controller state, complete execution-environment identifiers, or repeated-seed replications; the released data therefore cannot establish exact state replay, runtime generalization, or sensitivity to controller gains.

## Sizing and contracts

The committed index lists 15 cases. Four are real-data excerpts and eleven are generated cases, including white-noise and near-random-walk controls. Each case can carry trace, analysis, streaming, and manifest artifacts. Contract 1 validates source provenance and license policy; Contract 2 connects pipeline artifacts to the TypeScript consumer. Redacted sources expose aggregate metrics without raw values or paths.

## Technology and versions

| component | package | version | use | alternative considered |
|---|---|---|---|---|
| notebooks/requirements.txt | ipykernel | 7.4.0 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | matplotlib | 3.10.8 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | nbclient | 0.11.0 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | nbformat | 5.11.1 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| frontend | @fasl-work/caos-app-shell | 0.19.12 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
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
| requirements-dev.txt | jsonschema | 4.26.0 | Normative artifact validation and planted-defect guards. | Partial structural checks were removed. |
| frontend | openapi-typescript | 7.13.0 | Browser types generated from artifact schemas. | Handwritten mirrors were removed to prevent schema drift. |
| frontend | katex | 0.19.1 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
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
| ST-1 | sota | AutoETS, AutoTheta and AutoARIMA via statsforecast | Source adapters and frozen paths are identified; common-holdout scores use the same actual values and scaling. | `tests/test_engines.py`, `frontend/src/test/reevaluation.test.ts` |
| ST-2 | sota | LightGBM with lag features | Fresh fits and archived predictions retain distinct provenance and share the same targets and historical scale. | `tests/test_reevaluation.py`, `frontend/src/test/reevaluation.test.ts` |
| ST-3 | sota | NLinear, DLinear and NHITS via neuralforecast, plus documented direct-torch adaptations | Reference and adapted implementations keep distinct method identities; quantile-head adaptations do not count as exact paper replication. | `tests/test_reevaluation.py`, `frontend/src/test/reevaluation.test.ts` |
| ST-4 | sota | Chronos-Bolt, Chronos-2, TimesFM 2.5 and TiRex-2 | Fresh inference records all four checkpoint revisions and runtime versions; archived provenance stays selectable; no absence of pretraining overlap is asserted. | `frontend/src/test/reevaluation.test.ts` |
| BS-1 | beyond | ContextMemory within-series forecast combination | On fixed final holdouts compare against identical-expert EqualMean and RecencyMean ablations; preserve negative results. | `tests/test_reevaluation.py`, `scripts/reevaluate.py` |

## Beyond the state of the art

BS-1 proposes ContextMemory, a causal within-series combination of SeasonalNaive, SES, Holt, HoltWinters and Theta. Its hypothesis is that similar historical contexts give more useful expert-loss estimates than recency alone. At each completed historical origin it records normalized slope, level shift, volatility change, seasonal correlation and the experts' realised multi-step absolute errors. A distance kernel and fixed recency weights estimate the query-context loss; shrinkage toward the global recency estimate and a uniform floor determine convex forecast weights.

The method is implemented in `data-pipeline/chronoscopelab/model/context_memory.py`, integrated in the offline method registry, and compared in `data/derived/reevaluation.json`. FFORMA and arbitrated dynamic ensembles already establish context-dependent combinations. This proposal makes no priority claim; it tests a particular low-data, within-series recurrence rule. A calibration wrapper or the preqts harness is not represented as this forecasting proposal.

Evaluation fixes all hyperparameters before scoring the final blocks. The common experiment has 15 selected cases, one final forecast origin per case and the same truth and horizon for every admitted method. It refutes the present hypothesis at aggregate level: mean MASE is approximately 1.4504 for ContextMemory and 1.4489 for RecencyMean; EqualMean gives 1.8970. This is a negative finite-sample result, not a claim about all recurrence models. The archived comparison rescores frozen heavy paths. The separate fresh experiment executes all 22 variants on the same original histories and targets, binds package/checkpoint/source identities and independently verifies all metrics.

## Cases

The case matrix includes UCI Electricity, Beijing PM2.5, M4 daily, M4 hourly, and generated level-shift, GARCH, intermittent-demand, long-memory, seasonal, promotional, fractional, Mackey-Glass, white-noise, and near-random-walk cases. The two controls are limited protocol checks; they do not prove absence of leakage across all inputs or pretrained model corpora.

## Oracles

The artifact scripts compare committed output structure, manifest references, and method counts. Python unit tests cover forecasting implementations and streaming wrappers. The TypeScript contract test checks committed index-manifest-trace consistency; the parity test compares browser and Python point forecasts on a fixed fixture. Coverage target plots are computed from stored rolling trajectories. Current stored results show mean absolute deviation from nominal 0.8 coverage of 0.0057 for ACI, 0.0060 for PID, 0.0416 for Theta, and 0.0599 for seasonal-naive across the 15 cases; these are finite-case summaries, not general guarantees.

## Deploy driver

`.github/workflows/deploy-pages.yml` installs frontend dependencies, builds the static app over committed artifacts, uploads `frontend/dist`, and deploys GitHub Pages. The workflow is triggered from `main`; local validation does not establish a live deployment or owner acceptance.

## Risks and kill criteria

Do not publish a claim of a new forecasting method, universal calibration, general runtime advantage, or broad leaderboard superiority without new evidence. Stop a release if source licensing is unresolved, artifact and consumer shapes diverge, a control case reveals a material harness defect, or the deployed commit and artifact identity cannot be established. The forecasting proposal and detailed report are implemented and available as local reviewable drafts. Their separate Zenodo publication records remain pending under the external-publication boundary; the strict manuscript release gate remains open until publication is authorized and verified.

## ADR fit

| ADR | Decision in ChronoScope |
|---|---|
| ADR-0002 | The FastAPI service remains dormant; the product serves static committed artifacts. |
| ADR-0055 | GitHub Pages is the only deploy target. |
| ADR-0057 | The application keeps explicit pipeline and artifact boundaries. |
| ADR-0070 | Focus mode applies to the forecasting atlas surface. |
| ADR-0074 | CI checks repository integrity and artifact consistency without running the heavy bake. |
| ADR-0078 | The shell measurement gate is required before declaring the app-shell migration complete. |
