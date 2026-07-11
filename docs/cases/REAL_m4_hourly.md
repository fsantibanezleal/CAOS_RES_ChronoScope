# REAL_m4_hourly - M4 competition hourly series (m=24)

Source: **Monash Time Series Forecasting Repository / M4 competition** (CC-BY-4.0, public-safe), via the
`autogluon/chronos_datasets` `m4_hourly` snapshot cached in the private vault. Loader:
[`chronoscopelab/data/loaders.py`](../../data-pipeline/chronoscopelab/data/loaders.py) `load_m4_hourly`.
Committed sample: `data/examples/m4_hourly_sample.csv` (480 hourly points, one representative series;
the loader picks the first series with length >= 480, positive variance, and a lag-24 autocorrelation
>= 0.2, so the committed excerpt is genuinely seasonal rather than flat or too short).

## What it teaches

A real hourly series from the M4 competition, the most-cited modern forecasting benchmark. Its fingerprint
on the committed window: a strong daily cycle (lag-24 autocorrelation ~0.86) on genuine benchmark data,
not a generator. It is the REAL counterpart to the synthetic `SEAS_hourly` case:

- **Real seasonality is regular but not perfect** - the periodogram recovers the 24-hour period cleanly, but
  the amplitude drifts and the phase wanders slightly across days, so a fixed sinusoid (the synthetic case)
  overstates how clean real seasonality is.
- **Zero-shot foundation models earn their keep here** - because this is exactly the kind of series the
  foundation models were pre-trained near, the atlas shows whether a model that never saw THIS series still
  competes with the classical seasonal methods tuned on it. That comparison, on real competition data, is the
  central SOTA question the benchmark exists to answer.

## Why it is in the matrix

It grounds the seasonal story in real data: same nominal m=24 as `SEAS_hourly`, but with the irregularity,
drift, and noise structure of an actual measured series. It exercises the seasonality, autocorrelation, and
decomposition panels on data whose seasonality was measured, not designed.

## Provenance

Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61
forecasting methods. International Journal of Forecasting 36(1), 54-74. Redistributed under CC-BY-4.0 via the
Monash Time Series Forecasting Archive (Godahewa et al. 2021, arXiv:2105.06643). The bulk snapshot stays in
the private vault; only the small derived sample is committed (the source is public-safe, so the derived
excerpt may ship with attribution - see [../data/provenance.md](../data/provenance.md)).
