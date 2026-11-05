# Neural forecasting: distinct package models and direct adaptations

The offline comparison contains six separately named neural variants. Their
implementation identities are preserved in the source-bound procedure inventory
and complete study paths. They are not six independent implementations with
identical numerical behavior, and disagreement alone is not a parity failure.

## Package implementations

`data-pipeline/chronoscopelab/engines/neuralforecast_engine.py` wraps
`neuralforecast==3.1.9` models NLinear, DLinear and NHITS with a multi-quantile
pinball objective. The measured labels carry the `(nf)` suffix. The adapter's
context budget, optimization steps, seed and requested quantiles define the
experiment alongside the package version. A name from a paper is insufficient
to reconstruct that configuration. These models are opt-in through
`CHRONOSCOPE_ENABLE_NEURALFORECAST=1`; missing packages are an availability
condition, not evidence of poor forecasting accuracy.

## Direct adaptations

`data-pipeline/chronoscopelab/engines/neural_engine.py` implements separately
measured PyTorch variants. Its NLinear subtracts the final observed value and
uses quantile-specific linear outputs. DLinear decomposes its input using a
moving average and combines two linear maps. The NHITS-labeled direct variant
is a compact multi-rate pooled MLP adaptation. It does not reproduce the entire
NeuralForecast NHITS interpolation basis or training system. Those differences
must remain visible when comparing results or describing methods in a paper.
The direct variants are enabled through `CHRONOSCOPE_ENABLE_NEURAL=1`.

The original architectural references are [Zeng et al.](https://arxiv.org/abs/2205.13504)
for NLinear and DLinear, and [Challu et al.](https://arxiv.org/abs/2201.12886)
for NHITS. These citations identify the published ideas, not an assertion that
the local adaptations duplicate every published experiment. The adapter and
its source hash identify what actually ran.

## Quantiles, calibration and reproducibility

Training minimizes the pinball loss at the requested levels. Sorting or taking
a cumulative maximum across outputs enforces noncrossing values. Neither step
proves empirical coverage. Coverage, width, weighted quantile loss and interval
score must be measured on outcomes unavailable at fitting time. The existing
case study retains unfavorable interval results rather than treating a quantile
head as a calibration certificate.

Each fit uses windows from the observed prefix, with preprocessing quantities
estimated from that prefix. A comparison requires the same target block within
a case and an explicit fitting budget; a different rolling-origin count can
change the question being scored. The new fresh-case comparison records its
complete roster and checkpoint/runtime identities in
`data/derived/fresh-reevaluation.json`. Historical paths are retained separately.
Seeds and subprocess isolation reduce uncontrolled variation, but do not imply
bit-identical training across devices, library releases or CUDA kernels.
Reproduction claims are limited to the actual tested runtime and tolerances.

The browser's tiny `nlinear.onnx` is another execution identity: one global
instance-normalized least-squares map fitted to synthetic windows. It is not
one of these six per-prefix neural fits. Its held-out interval evaluation and
positive affine unit controls are documented separately in the browser-linear
study. See the [GPU guide](../guides/gpu-lane.md) for optional heavy setup;
ordinary application setup does not install every training stack.
