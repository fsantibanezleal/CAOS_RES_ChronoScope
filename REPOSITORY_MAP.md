# ChronoScope repository map

| Area | Location | Responsibility |
|---|---|---|
| Interface | `frontend/` | Shared shell, guided views, retained-result inspection and TypeScript/ONNX live computation |
| Experiment tooling | `data-pipeline/engine/` | Case definitions, source admission, native model adapters, stage orchestration and artifact export |
| Published numerics | ForecastScope and preqts | Installed reusable methods; pinned distributions, source hashes and historical compatibility checks |
| Admitted evidence | `data/derived/`, `docs/research/`, `manuscripts/` | Original input/forecast identities, protocols, full audits and published papers |
| Teaching | `notebooks/en/`, `notebooks/es/` | Eighteen mirrored lessons with actual methods, sensitivity and own-data extensions |
| Contracts | `docs/contracts/` | Versioned schemas, producers, consumers and missing-data rules |
| Validation | `tests/`, `scripts/` | Numerical controls, adversarial admission, reproducibility, unit and delivery checks |
| Documentation | `docs/` | Methods, architecture, data sources and runtime/reproduction guides |
| Optional API | `app/` | Dormant scaffold; the deployed app has no forecasting backend |
| Static delivery | `deploy/`, `.github/workflows/` | GitHub Pages build/deploy over the admitted corpus; no CI training |

The product declares no internal Python distribution. Fourteen thin adapters resolve to published ForecastScope modules; product-specific stages remain path tooling. See [provider ownership](docs/guides/numerical-provider.md).

Offline model paths are retained results. Five TypeScript forecasting rules and one self-hosted ONNX graph execute in the browser; there is no Python worker. The [architecture overview](docs/architecture/01_overview.md) and [live computation guide](docs/architecture/04_live-computation.md) describe their separate boundaries.

New numerical candidates are generated outside the repository, validated against source and execution identities, and explicitly promoted. Archived experiments retain their original implementation bytes when current providers change. The canonical public corpus cannot be replaced by a reduced local bake or redirected by a machine's global raw-data setting.
