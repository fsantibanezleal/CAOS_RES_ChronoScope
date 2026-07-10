# The streaming bench (the flagship novel piece)

Stage: [`chronoscopelab/stages/streaming.py`](../../data-pipeline/chronoscopelab/stages/streaming.py)
· Tests: [`tests/test_stage_streaming.py`](../../tests/test_stage_streaming.py)
· Package: [`preqts` on PyPI](https://pypi.org/project/preqts/) (ours, Apache-2.0)

## Why this exists

Real forecasting is **streaming**: observations arrive one by one, the model updates, and its intervals must
stay calibrated as the series drifts. Every public benchmark harness (fev, GIFT-Eval, the GluonTS/Darts
backtests) evaluates forecasters STATELESSLY on rolling windows - no state carries across windows, and there
is no test-then-train loop (verified adversarially in the research dossiers; fev's own window API confirms
it). The verified gap: **no public library evaluates stateful streaming forecasters prequentially with an
explicit covariate-arrival policy.** ChronoScope's answer is `preqts`, our extracted, published package
(PyPI `preqts>=0.2`), and this stage bakes its demonstration per case.

## The prequential principle

Prequential ("predictive sequential") evaluation is Dawid's test-then-train protocol (Dawid 1984, *JRSS-A*
147(2):278-292, DOI [10.2307/2981683](https://doi.org/10.2307/2981683)): at each step the model **predicts**
the next horizon, the truth is **revealed and scored**, and only then does the model **update**. Skill is a
trajectory over the stream, not a single number - a model that adapts shows a falling error curve; a static
one drifts.

## What is baked per case

For each streaming method, four trajectories (the web streaming bench renders them):

1. **Rolling MASE** - skill as the stream lengthens.
2. **Rolling empirical coverage** vs the nominal 80% target - the calibration story.
3. **Interval width** - the price paid for coverage (a calibrator that only widens is not impressive).
4. **Cumulative compute cost (ms)** - the constant-cost-per-step story that separates genuinely stateful
   models from replay-everything wrappers.

## The roster: raw vs calibrated (SOTA and beyond)

- **SeasonalNaive** - the honest floor.
- **Theta** - the strong classical live method, raw intervals.
- **Theta + ACI** - wrapped in Adaptive Conformal Inference (Gibbs & Candes 2021, NeurIPS,
  arXiv:[2106.00170](https://arxiv.org/abs/2106.00170)): the effective miscoverage is nudged each step by
  `gamma * (alpha_target - miss)`, so long-run coverage converges to the target under arbitrary distribution
  shift.
- **Theta + Conformal-PID** (Angelopoulos, Candes & Tibshirani 2023, NeurIPS,
  arXiv:[2307.16895](https://arxiv.org/abs/2307.16895)): calibration as PID control on the coverage error;
  ACI is the integral-only special case. The P and D terms buy better transients - faster coverage recovery
  after a regime change.

The calibrated variants are the "beyond SOTA in practice" demonstration: the same point forecaster, but with
intervals that self-correct online. The stage's tests assert the calibrated coverage error does not exceed
the raw forecaster's on a mid-stream noise-tripling regime shift.

## License note

The streaming artifact carries **aggregate metric trajectories only** (no raw series values are recoverable
from rolling MASE/coverage/cost), so it ships for every source - including the local-only-licensed real
datasets whose raw excerpts are redacted from the public artifacts.

## References

- Dawid, A.P. (1984). Present Position and Potential Developments: Some Personal Views. *JRSS-A* 147(2):278-292. DOI [10.2307/2981683](https://doi.org/10.2307/2981683).
- Gibbs, I. & Candes, E. (2021). Adaptive Conformal Inference Under Distribution Shift. *NeurIPS 2021*. arXiv:[2106.00170](https://arxiv.org/abs/2106.00170).
- Angelopoulos, A.N., Candes, E. & Tibshirani, R.J. (2023). Conformal PID Control for Time Series Prediction. *NeurIPS 2023*. arXiv:[2307.16895](https://arxiv.org/abs/2307.16895).
- Shchur, O. et al. (2025). fev-bench: A Realistic Benchmark for Time Series Forecasting. arXiv:[2509.26468](https://arxiv.org/abs/2509.26468) (the stateless-window contrast).
