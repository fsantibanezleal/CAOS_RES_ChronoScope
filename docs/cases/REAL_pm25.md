# REAL_pm25 - Beijing PM2.5 (hourly air quality)

Source: **UCI Beijing PM2.5** (CC-BY-4.0, public-safe). Loader:
[`chronoscopelab/data/loaders.py`](../../data-pipeline/chronoscopelab/data/loaders.py) `load_uci_beijing_pm25`.
Committed sample: `data/examples/beijing_pm25_sample.csv` (480 hourly points, one meter-window from 2011).

## What it teaches

Real hourly PM2.5 concentration at a Beijing monitoring station. It carries two properties that stress a
forecaster in ways the synthetic cases do not:

- **A daily cycle** (traffic + diurnal boundary-layer mixing) - the seasonality diagnostics recover a
  ~24-hour period, but it is noisier and less regular than the synthetic seasonal case.
- **Heavy-tailed pollution spikes** - concentrations sit low for long stretches then spike sharply during
  pollution episodes. The distribution panel shows strong positive skew and large excess kurtosis (the series
  is decisively non-normal), which is exactly why Gaussian prediction intervals under-cover here and the
  volatility panel matters.

## Why it is in the matrix

It is the honest "real data is messy" counterweight to the clean synthetic seasonal case: same nominal daily
period, but non-stationary spikes, missing-value gaps (forward-filled at load with the gaps flagged), and a
heavy tail. It exercises the distribution, volatility, and seasonality panels on genuinely non-Gaussian data.

## Provenance

Liang, X. et al. (2015), Beijing PM2.5 Data, UCI Machine Learning Repository, CC-BY-4.0. The bulk raw file
stays in the private vault; only the small derived sample is committed (the source is public-safe, so the
derived excerpt may ship with attribution - see [../data/provenance.md](../data/provenance.md)).
