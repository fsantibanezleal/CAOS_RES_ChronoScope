# Framework: mlforecast + LightGBM (Nixtla)

The machine-learning tier of ChronoScope's method ladder. Used by
`data-pipeline/chronoscopelab/engines/lightgbm_engine.py`.

## What and why

Gradient boosting on lagged and date features is the approach that won the M5 competition and remains the
standard ML baseline any forecasting atlas must include. [LightGBM](https://github.com/microsoft/LightGBM)
(MIT) is the gradient-boosting library; [mlforecast](https://github.com/Nixtla/mlforecast) (Nixtla,
Apache-2.0) supplies the time-series feature machinery (lag features, target transforms) and the recursive
multi-step forecasting loop, so the model sees a proper tabular design matrix instead of a hand-rolled one.

This tier sits above the classical numpy ladder and the statistical (statsforecast) tier: instead of a fixed
functional form, it learns a nonlinear map from recent lags to the next value.

## Why offline-only (not the live lane)

LightGBM is a native library and mlforecast pulls pandas; neither is Pyodide-safe, so this engine runs only in
the offline `.venv-pipeline` and is never imported by the browser live lane (which uses the pure-numpy classical
core). The engine module imports lazily and the pipeline degrades gracefully to the classical + statistical
tiers if these deps are absent.

## Install

Pinned in `data-pipeline/requirements.txt`:

```
mlforecast==1.0.31
lightgbm==4.6.0
pandas==2.3.3
```

## How ChronoScope uses it

For a forecast origin, the engine builds lag features from the seasonality `m` (base lags 1, 2, 3 plus `m`,
`m+1`, `2m` when seasonal), fits a single LightGBM point model with mlforecast, and forecasts recursively:

```python
from mlforecast import MLForecast
from lightgbm import LGBMRegressor
mlf = MLForecast(models={"lgb": LGBMRegressor(n_estimators=100, num_leaves=31, learning_rate=0.05)},
                 freq=1, lags=[1, 2, 3, m, m + 1, 2 * m])
mlf.fit(df, fitted=True)                 # fitted=True to get in-sample predictions
point = mlf.predict(h)["lgb"].to_numpy()
```

Prediction intervals come from the in-sample one-step residual sigma (`y - fitted`), widened by sqrt(step)
through the shared `gaussian_quantiles` helper, exactly as the classical ladder does. This is deliberately
simpler and faster than fitting three quantile-objective models and recursing each: recursive quantile models
drift because each feeds its own (biased) prediction back as a lag. A native quantile-objective variant is a
documented future refinement.

## Configuration notes and gotchas

- Lags must be shorter than the usable history; the engine filters lags to those that fit the context.
- The backtest refits per origin, so LightGBM gets a small window budget (`max_windows=6`) and a context cap
  (`ctx_cap=500`) to keep the pipeline runtime practical.
- `verbosity=-1` silences LightGBM's per-iteration logging; mlforecast may warn about missing frequency
  metadata when passed bare integer timestamps (cosmetic).

## Result (this slice)

LightGBM is competitive on the seasonal cases (MASE near the seasonal-naive baseline) and, like every method,
is scored by the preqts rolling backtest, never by a hand-typed number. On the built-in cases the auto-tuned
seasonal statistical models (AutoARIMA/AutoETS) still tend to win; the ML tier's advantage grows with more
data, covariates, and cross-series learning, which later slices explore.
