# Forecasting frameworks and execution identities

ChronoScope distinguishes a published model family from the particular code,
objective, checkpoint and fitting schedule used in each experiment. A shared
architecture name does not establish numerical parity between implementations.
The [source-bound inventory](design/method-inventory.json) identifies individual
procedures; the study receipts identify the executions behind reported scores.

- [StatsForecast](frameworks/01_statsforecast.md): AutoETS, AutoTheta and
  AutoARIMA adapters. Eligibility and context budgets belong to the particular
  study; they are not interchangeable with the browser smoothing methods.
- [Lag regression and LightGBM](frameworks/02_mlforecast_lightgbm.md): supervised
  lag-feature forecasting, with the package and fitting schedule stated.
- [Chronos adapters](frameworks/03_chronos.md): Chronos-Bolt and Chronos-2 are both
  implemented. They consume local checkpoint revisions and execute offline.
- [Pretrained model roster](frameworks/foundation-models.md): the four evaluated
  families include Chronos-Bolt, Chronos-2, TimesFM-2.5 and TiRex-2. The WSL
  execution boundary is explicit; these models are not pending placeholders.
- [Neural implementation identities](frameworks/deep-torch.md): direct PyTorch
  adaptations and NeuralForecast implementations remain separate measured
  variants. Quantile training is not a coverage guarantee.
- [Held-out browser linear study](research/browser-linear/README.md): the small
  global least-squares ONNX map is distinct from per-prefix neural fitting.
  Independent synthetic calibration improves interval score around unchanged
  points; the selected ridge point candidate did not improve test error.

The fifteen-case fresh comparison contains 22 fitted or pretrained variants.
The external combination study and the M4 Daily selection study have their own
smaller, explicitly declared rosters and different evaluation schedules. Their
results must not be pooled as if every model ran on every collection. Default
setup provides the CPU application environment; optional training and notebook
roles use configured external environments. The [fresh evaluation guide](guides/fresh-reevaluation.md)
records the heavy execution recipe and [GPU guide](guides/gpu-lane.md) explains
hardware-specific requirements. Published study runtime and checkpoint receipts
remain the authority for historical computations.
