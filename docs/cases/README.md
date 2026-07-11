# Cases + categories

Each case (`data-pipeline/chronoscopelab/cases/forecast_cases.py`) declares a CATEGORY (the forecasting
problem-type taxonomy), its seasonality and horizon, an expected band (what a domain expert should see), a
real/synthetic flag, and a provenance `source` (drives the license export guard). `registry.list_categories()`
groups them. The App shows ONE selected case; Experiments and Benchmark show cross-case summaries by category
(never mixed into the App).

## Coverage matrix (14 cases)

| id | category | expected band | source | deep write-up |
|---|---|---|---|---|
| `SEAS_hourly` | seasonal (m=24) | strong daily cycle; seasonal methods beat naive | synthetic | - |
| `TRND_seasonal` | trend + seasonal (m=12) | upward trend with a yearly cycle | synthetic | - |
| `INTM_demand` | intermittent demand | mostly zeros with sparse demand | synthetic | - |
| `RWLK_noise` | near-random-walk (honesty) | random walk; beating the naive is essentially noise | synthetic | - |
| `REAL_electricity` | real: electricity load (hourly) | real hourly load, daily seasonality + weekday effects | UCI (CC-BY) | - |
| `REAL_pm25` | real: Beijing PM2.5 (hourly) | daily cycle + heavy-tailed pollution spikes | UCI (CC-BY) | [REAL_pm25](REAL_pm25.md) |
| `REAL_m4_hourly` | real: M4 hourly (m=24) | real competition daily cycle; the real counterpart to SEAS_hourly | Monash/M4 (CC-BY) | [REAL_m4_hourly](REAL_m4_hourly.md) |
| `REAL_m4_daily` | real: M4 daily (m=7) | real competition weekly cycle; frequency diversity | Monash/M4 (CC-BY) | [REAL_m4_daily](REAL_m4_daily.md) |
| `CTRL_white_noise` | control: white noise | iid noise; nothing should beat the naive by much | synthetic | - |
| `BRKV_level_shift` | structural break | two clean level shifts; regime-averaging models lag at each break | synthetic | [BRKV_level_shift](BRKV_level_shift.md) |
| `MSEA_daily_weekly` | multi-seasonal (24+168) | daily AND weekly cycles; single-m methods miss the weekly | synthetic | [MSEA_daily_weekly](MSEA_daily_weekly.md) |
| `HETV_garch` | heteroscedastic (GARCH) | volatility clusters; fixed-width intervals fail, calibrated ones hold | synthetic | [HETV_garch](HETV_garch.md) |
| `LMEM_fractional` | long memory (ARFIMA d=0.35) | hyperbolic ACF decay, H~0.85; long-context methods hold an edge | synthetic | [LMEM_fractional](LMEM_fractional.md) |
| `CHAO_mackey` | deterministic chaos (Mackey-Glass) | forecastable short-horizon, error grows at the Lyapunov rate | synthetic | [CHAO_mackey](CHAO_mackey.md) |

## Design principles

- **Each scenario exercises one analysis family**: the break case is diagnosed by the change-point panel, the
  GARCH case by the volatility panel, the long-memory case by the fractal panel, the chaos case by the
  nonlinear-dynamics panel, the multi-seasonal case by the periodogram/MSTL panel. The analysis pillar and
  the forecasting ladder tell one coherent story per case.
- **Honesty/negative controls stay in**: near-random-walk and white noise - a large MASE gap on them is a red
  flag that the harness is leaking, and the GARCH case makes the point forecast deliberately boring so the
  INTERVAL calibration story (the streaming bench) carries the value.
- **Real data is license-guarded**: real cases carry their provenance source; a local-only-licensed source
  ships aggregate metrics only (see `docs/data/provenance.md`).

The remaining growth path to ~20 cases: the M-competition pair (`REAL_m4_hourly` m=24, `REAL_m4_daily` m=7)
landed as real Monash/M4 CC-BY data; still open are a known-future-covariates case (the one that would exercise
the preqts streaming bench's covariate-arrival policy, which needs covariate-aware forecasters), more real
datasets (OPSD load, additional UCI/GIFT-Eval series from `E:\_Datos\chronoscope`), and further frequency
coverage - each landing with its own deep write-up here.
