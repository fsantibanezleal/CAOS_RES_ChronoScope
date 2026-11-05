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

The original aggregate trajectories did not retain every controller state or the complete historical execution environment. The v0.25 reconstruction now retains 21,296 per-step updates, independently matches archived coverage and final weighted quantile loss, and includes 630 sensitivity settings plus 66 additional-seed results. Those calculations support finite-stream replay and sensitivity analysis; they do not restore the missing historical timing environment or establish native state-update performance. The separate external combination study retains favorable ValidationMix point-error comparisons against RecencyMean on two admitted collections, alongside unfavorable comparisons against AutoTheta. The new independent synthetic browser confirmation improves interval score by 49.60 percent around unchanged points, with full prefix-bin, family and lead outcomes in `docs/research/browser-linear/README.md`. These are measured gains with explicit population boundaries, not a record containing only negative outcomes.

UNVERIFIED: the exact historical timing environment, native state-update performance, and coverage of the synthetic browser calibration on arbitrary authentic series remain unconfirmed. These limits do not negate the independently reproduced finite-study results above.

- Sequence/corpus extension primary reference: https://cschoel.github.io/nolds/nolds.html
- Sequence/corpus extension primary reference: https://doi.org/10.1103/PhysRevLett.89.068102
- Sequence/corpus extension primary reference: https://doi.org/10.1109/ICDM.2016.0179
- Sequence/corpus extension primary reference: https://doi.org/10.1109/ICDM.2017.21
- Sequence/corpus extension primary reference: https://doi.org/10.1109/TIT.1976.1055501
- Sequence/corpus extension primary reference: https://doi.org/10.5281/zenodo.4656548
- Sequence/corpus extension primary reference: https://tsfresh.readthedocs.io/en/v0.21.0/text/feature_filtering.html

## Sizing and contracts

The committed index lists 15 cases. Four are real-data excerpts and eleven are generated cases, including white-noise and near-random-walk controls. Each case can carry trace, analysis, streaming, and manifest artifacts. Contract 1 validates source provenance and license policy; Contract 2 connects pipeline artifacts to the TypeScript consumer. Redacted sources expose aggregate metrics without raw values or paths. The separate M4 Daily study accounts for all 4,227 source identities, including explicit exclusions, and publishes forty prefix features with disjoint-series confirmation.


## Technology and versions

| component | package | version | use | alternative considered |
|---|---|---|---|---|
| requirements-browser-model.txt | onnx | 1.23.2 | Check and export the held-out CPU linear model; IR 9, opset 13 retained for browser compatibility. | Handwritten protobuf export would omit ONNX structural validation. |
| requirements-browser-model.txt | onnxruntime | 1.27.0 | Verify actual float32 execution against NumPy before admitting new held-out results. | NumPy alone would not verify the deployed graph backend. |
| requirements-combinations.txt | numba | 0.68.1 | Compile unchanged recursive expert loops for the CPU-only combination study; fastmath disabled. | Reference execution retained with independent parity checks. |
| requirements-precompute.txt | stumpy | 1.14.1 | Exact Matrix Profile and FLUSS; primary API verified 2026-11-02. | Exhaustive normalized-distance oracle retained in tests. |
| requirements-precompute.txt | scikit-learn | 1.9.1 | Explicitly seeded robust slopes and discovery-only corpus selector. | Unseeded nolds fitting rejected by determinism tests. |
| notebooks/requirements.txt | ipykernel | 7.4.0 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | matplotlib | 3.10.8 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | nbclient | 0.11.0 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| notebooks/requirements.txt | nbformat | 5.11.1 | Isolated executed lesson dependency. | Separately installed to preserve the offline engine environment. |
| frontend | @fasl-work/caos-app-shell | 0.20.0 | web runtime or build dependency; see frontend/package.json | Not assessed as a substitute in this release. |
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
| ST-5 | sota | Exact Matrix Profile/FLUSS and dependent feature filtering via STUMPY and SciPy | Exhaustive distance and entropy oracles, prefix-only features, independent BY/Kendall confirmation and discovery-only selection; original-axis consumer. | `tests/test_sequence_diagnostics.py`, `tests/test_forecastability.py`, `scripts/check_research_extensions.py` |
| BS-1 | beyond | ContextMemory within-series forecast combination | On fixed final holdouts compare against identical-expert EqualMean and RecencyMean ablations; preserve negative results. | `tests/test_reevaluation.py`, `scripts/reevaluate.py` |

## Beyond the state of the art

BS-1 proposes ContextMemory, a causal within-series combination of SeasonalNaive, SES, Holt, HoltWinters and Theta. Its hypothesis is that similar historical contexts give more useful expert-loss estimates than recency alone. At each completed historical origin it records normalized slope, level shift, volatility change, seasonal correlation and the experts' realised multi-step absolute errors. A distance kernel and fixed recency weights estimate the query-context loss; shrinkage toward the global recency estimate and a uniform floor determine convex forecast weights.

The method is implemented in `data-pipeline/chronoscopelab/model/context_memory.py`, integrated in the offline method registry, and compared in `data/derived/reevaluation.json`. FFORMA and arbitrated dynamic ensembles already establish context-dependent combinations. This proposal makes no priority claim; it tests a particular low-data, within-series recurrence rule. A calibration wrapper or the preqts harness is not represented as this forecasting proposal.

Evaluation fixes all hyperparameters before scoring the final blocks. The common experiment has 15 selected cases, one final forecast origin per case and the same truth and horizon for every admitted method. It refutes the present hypothesis at aggregate level: mean MASE is approximately 1.4504 for ContextMemory and 1.4489 for RecencyMean; EqualMean gives 1.8970. This is a negative finite-sample result, not a claim about all recurrence models. The archived comparison rescores frozen heavy paths. The separate fresh experiment executes all 22 variants on the same original histories and targets, binds package/checkpoint/source identities and independently verifies all metrics.

## Novel contributions

NC-1 is the admitted fifteen-series replay protocol and empirical adaptive-interval comparison, implemented with preqts. Its paper is **Prequential Evaluation of Adaptive Prediction Intervals: A Fifteen-Series Replay Study**, version 2.5, concept DOI 10.5281/zenodo.21508920. This is an evaluation contribution, not a new forecasting method or a comparison of native state updates. The v0.25 reconstruction preserves per-step states and sensitivity outcomes; historical runtime provenance remains unavailable. The separate working v2.6 revision has not been published or independently reviewed.

## Cases

The case matrix includes UCI Electricity, Beijing PM2.5, M4 daily, M4 hourly, and generated level-shift, GARCH, intermittent-demand, long-memory, seasonal, promotional, fractional, Mackey-Glass, white-noise, and near-random-walk cases. The two controls are limited protocol checks; they do not prove absence of leakage across all inputs or pretrained model corpora.

## Oracles

The artifact scripts compare committed output structure, manifest references, and method counts. Python unit tests cover forecasting implementations and streaming wrappers. The TypeScript contract test checks committed index-manifest-trace consistency; the parity test compares browser and Python point forecasts on a fixed fixture. Coverage target plots are computed from stored rolling trajectories. Current stored results show mean absolute deviation from nominal 0.8 coverage of 0.0057 for ACI, 0.0060 for PID, 0.0416 for Theta, and 0.0599 for seasonal-naive across the 15 cases; these are finite-case summaries, not general guarantees.

## Deploy driver

`.github/workflows/deploy-pages.yml` installs frontend dependencies, builds the static app over committed artifacts, uploads `frontend/dist`, and deploys GitHub Pages. The workflow is triggered from `main`; local validation does not establish a live deployment or owner acceptance.

## Risks and kill criteria

Do not publish a claim of a new forecasting method, universal calibration, general runtime advantage, or broad leaderboard superiority without new evidence. Stop a release if source licensing is unresolved, artifact and consumer shapes diverge, a control case reveals a material harness defect, or the deployed commit and artifact identity cannot be established. The forecasting proposal and detailed report are implemented and published under separate verified Zenodo concepts. The proposal retains its negative aggregate result. Publication does not replace remote CI, exact deployment identity, canonical live checks or owner acceptance.

## ADR fit

| ADR | Decision in ChronoScope |
|---|---|
| ADR-0002 | The FastAPI service remains dormant; the product serves static committed artifacts. |
| ADR-0055 | GitHub Pages is the only deploy target. |
| ADR-0057 | The application keeps explicit pipeline and artifact boundaries. |
| ADR-0070 | Focus mode applies to the forecasting atlas surface. |
| ADR-0074 | CI checks repository integrity and artifact consistency without running the heavy bake. |
| ADR-0078 | The shell measurement gate is required before declaring the app-shell migration complete. |

## Temporal-validation combination extension

Requirements VC-1 to VC-5 are specified in `features/validated-combinations/requirements.md`.
ContextMemoryCV and ValidationMix retain the existing experts and context definition, select
only from completed historical validation blocks, and preserve the original fixed-rule result.
The full external source inventories are M4 Weekly, https://doi.org/10.5281/zenodo.4656522,
and M3 Monthly, https://doi.org/10.5281/zenodo.4656298, both CC BY 4.0. Source and code
hashes, explicit exclusions, common prefixes, up to three origins and independent scoring
bind the browser index and per-series records to their computation. The empirical point
improvements are collection-specific; interval quality and attribution to the context kernel
remain separate questions. The second bilingual combination lesson executes both variants.

## Numerical procedure inventory

The [source-bound procedure inventory](method-inventory.json) expands the family
rows above into individual numerical procedures and execution identities.
It distinguishes each measured forecast, components returned by combined
diagnostic APIs, the browser least-squares export, the per-prefix neural fits,
the historical streaming reconstruction and the two different selection rules.
The technical report and teaching set must account for these individual
procedures; a family label alone does not establish complete coverage.

`python scripts/method_inventory.py` verifies the inventory, its implementation
symbols, validation locations and the names in both measured forecast studies.
Its source hashes bind documentation to code. An inventory count establishes
implementation scope; scientific validity, teaching depth and publication
coverage require their own evidence. Requirements MI-1 through MI-3 are in
`features/method-inventory/requirements.md`.
