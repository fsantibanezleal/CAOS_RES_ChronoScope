# Cases + categories

Each case (`data-pipeline/chronoscopelab/cases/forecast_cases.py`) declares a CATEGORY (the forecasting
problem-type taxonomy), its seasonality and horizon, an expected band (what a domain expert should see), and a
real/synthetic flag. `registry.list_categories()` groups them. The App shows ONE selected case; Experiments and
Benchmark show cross-case summaries by category (never mixed into the App).

## Coverage matrix (this slice)

| id | category | expected band | source |
|---|---|---|---|
| `SEAS_hourly` | seasonal (m=24) | strong daily cycle; seasonal methods beat naive | synthetic |
| `TRND_seasonal` | trend + seasonal (m=12) | upward trend with a yearly cycle | synthetic |
| `INTM_demand` | intermittent demand | mostly zeros with sparse demand | synthetic |
| `RWLK_noise` | near-random-walk (honesty) | random walk; beating the naive is essentially noise | synthetic |
| `REAL_electricity` | real: electricity load (hourly) | real hourly load, daily seasonality + weekday effects | real |
| `CTRL_white_noise` | control: white noise | iid noise; nothing should beat the naive by much | synthetic |

The near-random-walk and white-noise cases are deliberate honesty/negative controls: on them, a large MASE gap
would be a red flag that the harness is leaking. The target is 12+ cases across more categories and more real
datasets (M-competition, LTSF, additional UCI/Kaggle series from `E:\_Datos\chronoscope`) in later slices, each
with a `docs/cases/<category>/<case-id>.md` write-up.
