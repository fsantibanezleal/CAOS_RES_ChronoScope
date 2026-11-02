# Fresh final-block execution

The original released traces and corrected mixed-provenance comparison remain immutable
reference evidence. `scripts/reevaluate_fresh.py` separately refits or infers every released
method on the verified original contiguous histories. It requires the complete roster;
a missing dependency, checkpoint, case, quantile column or failed fit aborts admission.

The measured Linux runtime uses Python 3.12, torch 2.9.1 with CUDA 12.8, NumPy 2.1.3,
SciPy 1.15.3, pandas 2.3.3, statsforecast 2.0.3, LightGBM 4.6.0, MLForecast 1.0.31,
neuralforecast 3.1.9, chronos-forecasting 2.3.2, timesfm 2.0.2 and tirex-2 0.1.1.
NumPy follows TiRex's compatible minor line here; this is a distinct environment from
the NumPy 2.4.6 browser-parity and notebook environments. The actual runtime and
checkpoint revisions are recorded in the fresh artifact. `pip check` must pass.

Provision a separate Linux virtual environment; preserve existing environments. Install
the CUDA-compatible torch build, the stated packages and Ninja. TiRex additionally needs
the CUDA toolkit and a working C++ compiler for its fused recurrent extensions. Its
upstream package defines those build requirements. Make the tool executables available
on `PATH` and configure `CUDA_HOME` for the actual toolkit. GPU fits use the installed
hardware; the Chronos adapter currently uses CPU inference. Timings include fitting,
first-use imports/model loading and inference, so they are not a warm-inference ranking.

Download only the admitted Apache-licensed checkpoints to an external model root:

- `amazon/chronos-bolt-small` into `chronos-bolt-small/`.
- `amazon/chronos-2` into `chronos-2/`.
- `google/timesfm-2.5-200m-pytorch` into `timesfm-2.5/`.

Use `huggingface_hub.snapshot_download` so download metadata binds each local checkpoint
to its exact revision. The runner checks those bindings and hashes the weights and
configuration. TiRex's `NX-AI/TiRex-2` revision is supplied explicitly to its loader and
remains in the local Hugging Face cache. Model weights are never committed or bundled
into the browser. The separate live ONNX model remains the small product asset.

Set `CHRONOSCOPE_MODEL_ROOT` to that external root. Enable the model implementations
with `CHRONOSCOPE_ENABLE_NEURAL=1`, `CHRONOSCOPE_ENABLE_NEURALFORECAST=1`,
`CHRONOSCOPE_ENABLE_FOUNDATION=1` and `CHRONOSCOPE_ENABLE_TIREX=1`. Bound BLAS/OpenMP
threads explicitly; the recorded run uses one library thread and four torch CPU threads.
LightGBM explicitly uses one worker, and compiler workers are bounded to one. An
unbounded LightGBM run stalled inside its native training update after pretrained-model
initialization; that candidate was stopped and never admitted. The complete admitted run
uses the bounded source configuration rather than relabeling predictions from that run.

Run a one-case trial first:

```sh
python scripts/reevaluate_fresh.py --case TRND_seasonal \
  --cache-dir "$CAOS_TEMP_ROOT/model-cache" --output "$CAOS_TEMP_ROOT/trial.json"
```

Then omit `--case` and write a different external candidate. The source-bound per-case,
per-method cache permits safe resumption; all implementation files, package versions,
checkpoint identities and input artifact bytes contribute to its key. A source change
during execution refuses the candidate. Trials never satisfy complete-corpus admission.

```sh
python scripts/reevaluate_fresh.py \
  --cache-dir "$CAOS_TEMP_ROOT/model-cache" --output "$CAOS_TEMP_ROOT/fresh.json"
python scripts/check_fresh_reevaluation.py "$CAOS_TEMP_ROOT/fresh.json"
```

The admission checker independently recomputes every metric using standard-library
arithmetic and checks the complete case/method inventory, original histories and targets,
checkpoint revisions, source bindings and aggregates. Promote only the admitted complete
candidate, then run the schema, browser-consumer, product and browser checks. Warning
categories are retained with each fit; a finite prediction does not establish optimizer
convergence or predictive calibration.

The current [TimesFM upstream](https://github.com/google-research/timesfm) identifies
TimesFM 3.0 as its latest model. Its downloaded weights have a separate non-commercial,
non-production licence, while 2.5 weights retain Apache licensing. It remains a guide-only
candidate here. This roster does not claim to contain the latest model of every family.
