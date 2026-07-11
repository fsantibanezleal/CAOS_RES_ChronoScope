# REAL_m4_daily - M4 competition daily series (m=7)

Source: **Monash Time Series Forecasting Repository / M4 competition** (CC-BY-4.0, public-safe), via the
`autogluon/chronos_datasets` `m4_daily` snapshot cached in the private vault. Loader:
[`chronoscopelab/data/loaders.py`](../../data-pipeline/chronoscopelab/data/loaders.py) `load_m4_daily`.
Committed sample: `data/examples/m4_daily_sample.csv` (400 daily points, one representative series selected
by the same length / variance / lag-7 autocorrelation criteria as the hourly case).

## What it teaches

A real M4 daily series with a weekly cycle (lag-7 autocorrelation ~0.92 on the committed window). It adds a
DIFFERENT real seasonality to the matrix (m=7 vs the hourly m=24), so the benchmark is not anchored to a
single frequency:

- **Weekly structure on real data** - the periodogram peaks at period 7, and the decomposition's seasonal
  strength is high, but the trend component wanders (real daily series drift with the underlying process),
  which is what separates the seasonal-plus-trend methods (Holt-Winters, AutoETS) from the pure-seasonal
  naive here.
- **Shorter horizon, weekly reasoning** - the case forecasts h=14 (two weeks) at m=7, so a method has to carry
  the weekly pattern forward twice; the per-horizon error curve (the Horizon tab) shows whether skill decays
  smoothly or jumps at the weekly boundary.

## Why it is in the matrix

Frequency diversity: paired with `REAL_m4_hourly` it shows the ladder is not tuned to one cadence. Real weekly
seasonality, real drift, real noise - the honest daily-frequency counterpart to the hourly seasonal cases.

## Provenance

Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61
forecasting methods. International Journal of Forecasting 36(1), 54-74. Redistributed under CC-BY-4.0 via the
Monash Time Series Forecasting Archive (Godahewa et al. 2021, arXiv:2105.06643). The bulk snapshot stays in
the private vault; only the small derived sample is committed (public-safe, may ship with attribution - see
[../data/provenance.md](../data/provenance.md)).
