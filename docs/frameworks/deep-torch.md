# The deep tier: NLinear, DLinear, NHITS (direct PyTorch)

Code: [`chronoscopelab/engines/neural_engine.py`](../../data-pipeline/chronoscopelab/engines/neural_engine.py)
· Tests: [`tests/test_engine_neural.py`](../../tests/test_engine_neural.py) · GPU lane:
[`../guides/gpu-lane.md`](../guides/gpu-lane.md)

The deep tier of the ladder is three real forecasting architectures, trained per case on the GPU with a
multi-quantile (pinball) loss so each forecast carries a calibrated interval. They plug into the same
`Forecaster.quantiles(y, m, h, levels)` contract as every other engine and are baked (replay) in the web app.

## Why implemented directly (not via neuralforecast)

The usual wrapper, **neuralforecast, is not installable in this environment**: it hard-requires `ray>=2.2.0`,
which has **no Python-3.13 wheel** (verified 2026-07-04; `pip index versions ray` returns no distribution,
including `--pre`). Rather than downgrade the whole repo's interpreter or patch a third-party package, the
models are implemented **directly against their papers**. This is faithful, not a toy substitute: DLinear and
NLinear are literally single linear layers on a decomposition, and NHITS is a documented multi-rate MLP stack.
Decision record: `wip/chronoscope/deep-engine-decision-2026-07-04.md` (in the CAOS_MANAGE vault).

## The models

- **NLinear** (Zeng et al. 2023, AAAI-23, arXiv:2205.13504): subtract the last observed value, apply one
  linear layer over the lookback window, add the value back. A per-quantile output head turns the point map
  into a quantile forecast. Deceptively strong: it was the paper's evidence that a single linear layer rivals
  deep transformers on the LTSF benchmarks.
- **DLinear** (same paper): decompose the input into a **trend** (a moving average) and a **remainder**, put a
  linear layer on each, and sum. Captures level + seasonal shape with two linear maps.
- **NHITS** (Challu et al. 2023, AAAI-23, arXiv:2201.12886): a stack of MLP blocks operating at **decreasing
  pooling rates** (multi-rate sampling), whose forecasts are summed hierarchically - long-range structure from
  the coarse blocks, fine detail from the fine ones. Kept compact (3 blocks, 128 hidden) for the 8 GB budget
  and the short case histories.

## Training

Each model is trained per case: the history is cut into sliding `(lookback -> horizon)` windows, standardized
to unit scale, and fit with the **pinball loss** summed over the requested quantile levels
(Koenker & Bassett 1978) - the same objective neuralforecast's `MQLoss` uses. Training is **seeded** for
determinism (a re-bake at the same seed reproduces the forecast bit-for-bit within tolerance), runs on the GPU
via `chronoscopelab.gpu.device()` with a transparent CPU fallback, and the output quantiles are made monotone
across levels (`cumulative max`).

## Availability and gating

The deep tier is **opt-in** (`CHRONOSCOPE_ENABLE_NEURAL=1`), so the fast unit-test path stays on the classical
+ statistical + ML ladder; the engine has its own GPU-gated test that skips when torch is absent (CI). It
degrades gracefully: `neural_forecasters()` returns `[]` when torch is missing or the flag is off, and the rest
of the ladder runs. The full-ladder bake (with the deep tier on) runs **offline on the GPU box** and is
committed as artifacts.

## What it is, and is NOT

- These are the **real architectures**, trained on the real case data with a real quantile objective - they
  are compared honestly against the classical/statistical/ML/foundation tiers on the same leakage-safe
  backtest.
- They are **not** the neuralforecast implementations (which add engineering niceties like learning-rate
  schedules, early stopping, and the full N-HiTS interpolation basis). The direct implementations are compact
  and faithful to the core idea, sufficient for the atlas's purpose of showing where each family wins.
- On a near-random-walk or white-noise case they will not beat the naive by much - which is the honest,
  expected result the no-free-lunch story wants.

## References

- Zeng, A., Chen, M., Zhang, L. & Xu, Q. (2023). Are Transformers Effective for Time Series Forecasting? *AAAI-23*. arXiv:[2205.13504](https://arxiv.org/abs/2205.13504).
- Challu, C., Olivares, K.G., Oreshkin, B.N., Garza, F., Mergenthaler-Canseco, M. & Dubrawski, A. (2023). NHITS: Neural Hierarchical Interpolation for Time Series Forecasting. *AAAI-23*. arXiv:[2201.12886](https://arxiv.org/abs/2201.12886).
- Koenker, R. & Bassett, G. (1978). Regression Quantiles. *Econometrica* 46(1):33-50. DOI [10.2307/1913643](https://doi.org/10.2307/1913643).
