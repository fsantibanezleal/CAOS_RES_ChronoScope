# EXOG_promo - exogenous driver (known-future covariate)

The scenario that exercises the one capability the other 14 cases cannot: a covariate with an explicit
ARRIVAL POLICY. It is the reason `preqts` (our published harness) exists, and until this case nothing in
the atlas demonstrated it.

Generator:
[`cases/forecast_cases.py`](../../data-pipeline/chronoscopelab/cases/forecast_cases.py) `_synth_exog`
(kind `exog_promo`). Deterministic, seeded. Synthetic + labelled, so the full trace is public.

## What it is

A weekly-seasonal target (`m = 7`) plus a **scheduled promotion driver**: a pulse train of promotions at
seeded-irregular positions, each raising the level for 2-4 steps. The target is

```
y[t] = level + amp * sin(2*pi*t/7) + gain * driver[t] + noise
```

The driver is attached to the series as a `Covariate` with `kind = "known_future"` and `lag = 0`.

## The arrival policy (the point)

A covariate's value for time `s` is not automatically available when you forecast time `s`. `preqts`
makes the timing explicit:

- **known_future** (this case): calendar effects, holidays, *scheduled* promotions or interventions - the
  value is known for every time, including the forecast horizon. A covariate-aware forecaster may use the
  driver's future values ahead of time.
- **past with lag L**: a sensor or a reported metric whose value for time `s` only arrives at `s + L`. The
  hard case; the model must forecast the covariate too, or wait.

The promotions here are *scheduled*, so they are genuinely known-future - but they are NOT predictable from
the target's own history (they land at irregular times), so a univariate method must lag every promo while
a covariate-aware method anticipates it. That gap is the whole demonstration.

## How the atlas shows it

The 19-method ladder forecasts `y` **univariate** (honestly: classical/statistical/deep/foundation methods
here ignore the exog, so the point leaderboard is deliberately unexciting - the promos look like noise from
`y` alone). The **streaming bench** carries the covariate story: it builds a `preqts.Stream` with the
known-future covariate and runs

- **Ridge (blind)**: an online ridge on `[intercept, y[t-1], y[t-m]]` - the same model, no covariate;
- **Ridge+exog (aware)**: the same ridge plus the covariate column, reading the horizon's driver from the
  `known_future` channel.

On the committed bake the aware model reaches MASE ~0.49 vs the blind ~0.76 (both vs the seasonal-naive
denominator): a ~35% skill gain purely from knowing the scheduled driver ahead. The Series tab overlays
the driver; the Streaming tab frames the aware-vs-blind comparison.

## Why it is in the matrix

It is the only case where the covariate-arrival policy - the novel piece of the streaming bench - is
actually exercised. It also keeps the honesty line clear: the ladder is NOT covariate-aware (most of those
methods genuinely cannot use exog), and the case says so; the value of the covariate is shown exactly where
it is real (an online model that consumes it), not overclaimed across the board.

## References

- Prequential evaluation: Dawid, A. P. (1984). Statistical theory: the prequential approach. JRSS-A
  147(2), 278-292. DOI 10.2307/2981683.
- Regression with exogenous regressors and the known-future vs past distinction is standard in the Nixtla /
  fev covariate model (Shchur et al. 2025, arXiv:2509.26468); `preqts` makes the arrival policy a
  first-class property of the stream.
