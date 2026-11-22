# Architecture: overview

ChronoScope combines retained research artifacts, live browser computations and executed teaching material. The adopted shell and repository template supply the shared interface and delivery workflow; product-specific numerical and evidence contracts are described in the [SDD](../design/SDD.md).

| Lane | Implementation | Execution boundary |
|---|---|---|
| Offline analysis | `data-pipeline/engine`, using published `forecastscope` and `preqts` | Declared external `.venv-product`; heavy model references use their recorded environments |
| Live browser | TypeScript kernels and self-hosted ONNX/WASM | Five classical rules plus the fixed normalized linear graph; no Python worker |
| Retained studies | Committed `data/derived` and source-bound archives | Rendered and independently rescored; opening a view does not refit a model |
| Teaching | Eighteen English/Spanish notebooks | External `.venv-lessons`; seven actual references execute in a separately pinned Linux runtime |
| API | Optional `app/` scaffold | Dormant; the deployed application requires no API |

The staged pipeline validates source inputs, preprocesses, extracts features, trains, forecasts, evaluates and exports. [Data contracts](08_data-contracts.md) bind admitted source descriptors, manifests and traces. The local workflow generates into an external candidate stage, validates it and explicitly promotes accepted artifacts. Research studies retain their original implementation and protocol identities when the active provider changes.

Reusable numerical methods come from published ForecastScope modules through thin path-tooling adapters. The product root is not an internal method distribution. Product stages, case definitions, rendering and provenance remain here. The [provider guide](../guides/numerical-provider.md) identifies adapter ownership and the verified historical implementation archive.

The [live computation guide](04_live-computation.md) states actual browser methods, normalization and refusal conditions. Native statistical, tree and foundation-model paths displayed from retained studies remain offline results. No inactive Pyodide scaffold is presented as a working execution path.
