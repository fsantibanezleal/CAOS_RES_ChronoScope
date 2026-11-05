# Chronos-Bolt and Chronos-2 adapters

ChronoScope implements both Chronos-Bolt and Chronos-2 through
`data-pipeline/chronoscopelab/engines/chronos_engine.py`; neither is a future
placeholder. These are pretrained forecasting models, consumed from local
checkpoint folders and evaluated without per-case weight fitting. They remain
distinct variants in the fifteen-case fresh comparison. Their exact checkpoint
revisions and runtime versions are retained with that study, rather than
identified only by a mutable model-family name.

## Input, output and availability

The adapter receives an observed univariate prefix, an explicit forecast
horizon and requested quantile levels. A configured context cap can restrict
how many of the available observations the model consumes. Available history
and consumed context are different quantities and should both be recorded.
The package pipeline returns quantile paths that the adapter maps to the
product's forecast contract and makes monotone across levels. This monotonicity
operation is not a calibration theorem.

Local model discovery uses `CHRONOSCOPE_MODEL_ROOT`, with the configured model
vault as the default location. The legacy opt-in flag is
`CHRONOSCOPE_ENABLE_FOUNDATION=1`. An absent dependency or checkpoint omits an
optional engine from an ordinary run. A complete-roster scientific experiment
instead requires every declared model and fails admission when one is missing;
an omitted engine is never silently counted as an evaluated poor performer.
Default application setup should not be confused with recreating that heavy
experimental runtime.

## Interpretation and reproducibility

The [fresh evaluation guide](../guides/fresh-reevaluation.md) distinguishes
archived-path scoring from new execution. Both can be auditable, but they answer
different questions. Original rolling-backtest aggregates also differ from the
common final-block experiment when their origin counts or context budgets
differ. A favorable result for one seasonal case does not establish an advantage
across all series, forecast horizons or benchmark collections.

The browser replays admitted pretrained forecast paths. Its small live linear
ONNX model is a separately trained global regression map, not a browser export
of Chronos-Bolt or Chronos-2. This separation prevents a client-side execution
claim from being transferred to a model that only ran offline.

The primary implementation is maintained by
[Amazon Science](https://github.com/amazon-science/chronos-forecasting).
[Chronos](https://arxiv.org/abs/2403.07815) and
[Chronos-2](https://arxiv.org/abs/2510.15821) describe the model families.
Package licensing and checkpoint licensing must be checked for the exact
revision consumed; a framework license is not a substitute for a model-card
license. The [complete pretrained roster](foundation-models.md) records the
additional TimesFM and TiRex execution boundaries.
