# Framework: statsforecast (Nixtla)

The auto-tuned statistical SOTA tier of ChronoScope's method ladder. Used by
`data-pipeline/chronoscopelab/engines/statsforecast_engine.py`.

## What and why

[statsforecast](https://github.com/Nixtla/statsforecast) (Apache-2.0) is Nixtla's high-performance library
of classical and statistical forecasting models, JIT-compiled with numba. It is the healthiest, best-maintained
implementation of the auto-order-selection models that a forecasting atlas must include:

- **AutoARIMA**: automatic ARIMA/SARIMA order selection (Hyndman-Khandakar), the canonical statistical model
  the domain expects. It searches over (p, d, q)(P, D, Q) and returns the fitted model with analytic prediction
  intervals.
- **AutoETS**: automatic exponential-smoothing state-space model selection (error/trend/seasonal components),
  the state-space generalisation of the Holt-Winters family.
- **AutoTheta**: the automatic Theta method, a strong, cheap benchmark that won the M3 competition.

These sit above ChronoScope's pure-numpy classical ladder (seasonal-naive, SES, Holt, Holt-Winters, Theta):
same method families, but with automatic order/parameter selection and proper analytic intervals.

## Why offline-only (not the live lane)

statsforecast depends on numba, which is not available in Pyodide, so these engines run only in the offline
`.venv-pipeline` and are never imported by the browser live lane (`chronoscopelab/live.py`, which uses the
pure-numpy classical core). The engine module imports statsforecast lazily and the pipeline degrades gracefully
to the classical ladder if statsforecast is not installed.

## Install

Pinned in `data-pipeline/requirements.txt`:

```
statsforecast==2.0.3
```

## How ChronoScope uses it

Each method is wrapped into the `Forecaster` contract (`quantiles(y, m, h, levels)` and `forecast(...)`). For a
forecast origin, the model is fit on the context and asked for its analytic prediction intervals; ChronoScope
maps each requested quantile level `p` to a symmetric coverage percent (`|1 - 2p| * 100`) and reads the
corresponding `lo-`/`hi-`/`mean` output:

```python
from statsforecast.models import AutoARIMA
model = AutoARIMA(season_length=m, stepwise=True, approximation=True)
model.fit(y)
f = model.predict(h, level=[80])   # -> {"mean": ..., "lo-80": ..., "hi-80": ...}
```

The evaluate stage backtests each method with `preqts` (rolling origin, out-of-sample). Because AutoARIMA
refits per origin and its order search is expensive, it is given a small window budget (`max_windows=3`) and a
context cap (`ctx_cap=360`); AutoETS and AutoTheta are cheap and get more windows. A method that cannot fit a
given case is omitted for that case rather than crashing the run.

## Configuration notes and gotchas

- `season_length` must be the seasonal period `m` (1 for non-seasonal). For `m < 2` the seasonal models fall
  back to non-seasonal behaviour.
- `stepwise=True, approximation=True` on AutoARIMA trade a little accuracy for a large speed-up; without them
  the order search on long or high-frequency series can take tens of seconds per fit.
- statsforecast emits benign warnings when a series has no frequency metadata (ChronoScope passes bare numpy
  arrays); these are cosmetic.
- The first AutoARIMA call in a process pays a one-time numba JIT compile cost.

## Result (this slice)

On the built-in cases, seasonal AutoARIMA/AutoETS win on the seasonal and trend cases (MASE below 1, beating the
seasonal-naive baseline); the intermittent, real-electricity, and control cases still favour the simple
baselines. Numbers are recomputed by the pipeline and shown in each case's Benchmark/App view, never hand-typed.
