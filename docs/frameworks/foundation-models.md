# Pretrained forecasting models and execution boundaries

The current fifteen-case fresh comparison executes four separately identified
pretrained families: Chronos-Bolt, Chronos-2, TimesFM-2.5 and TiRex-2. All four
are implemented; they are not planned future placeholders. The study retains
exact package/runtime identities, checkpoint revisions, complete forecast paths
and independently recomputed scores. These records identify a bounded numerical
experiment, not a standing claim that one family is best on every series.

## Python adapters and checkpoint identity

`chronos_engine.py` serves the two Amazon families from local checkpoint
folders. `timesfm_engine.py` serves TimesFM with its own package/API mapping.
Both consume observed prefixes and produce the explicitly requested future
horizon. Per-engine context caps remain part of the experimental configuration.
A common target block does not imply every model uses the same number of past
observations. Where a package returns a larger quantile set, the mapping to the
scored levels is recorded; noncrossing output does not establish calibration.

The canonical checkpoint identifiers in the fresh experiment include
`amazon/chronos-bolt-small`, `amazon/chronos-2` and
`google/timesfm-2.5-200m-pytorch`. Their exact revisions are recorded in
`data/derived/fresh-reevaluation.json`, which is preferable to a mutable
latest-model alias. A framework license does not automatically license every
checkpoint published for that framework. Reproduction and redistribution must
respect the recorded model-card terms for the particular weights used.

## TiRex and the WSL boundary

`engines/tirex2_wsl_engine.py` and `tools/tirex2_wsl/tirex2_bake.py` provide the
WSL execution bridge. The optional flag is `CHRONOSCOPE_ENABLE_TIREX_WSL=1`.
Its Linux/CUDA dependencies are isolated from the native Windows application
environment. A missing WSL runtime means the optional lane is unavailable; a
complete declared-roster experiment cannot replace that missing execution with
a synthetic path or silently omit it. See the [WSL guide](../guides/tirex2-wsl-lane.md)
and [fresh evaluation recipe](../guides/fresh-reevaluation.md) for the actual
runtime and checkpoint requirements. Reuse of cached weights is distinct from
reuse of a forecaster's evolving state; the fifteen-case experiment does not
measure native recurrent update performance.

## What the browser executes

The browser replays the admitted pretrained paths. It does not download these
large checkpoints or train them on user inputs. The live ONNX model is a small
global instance-normalized linear regression fitted to synthetic windows. Its
separate [held-out study](../research/browser-linear/README.md) confirms an
interval-score improvement for prefix-stratified calibration while retaining
an unfavorable ridge point-error result. Neither observation is a performance
claim about Chronos, TimesFM or TiRex.

The default setup installs a CPU application role. Complete heavy evaluation
requires the pinned optional packages, specific checkpoint revisions and the
recorded hardware/runtime. Local legacy environments are not silently replaced
with new versions because their package names resemble the study's runtime.
Additional surveyed model families remain literature or future integration
candidates until their implementation, licensing and complete evaluation are
actually admitted.
