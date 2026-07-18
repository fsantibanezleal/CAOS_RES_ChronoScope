# BRKV_level_shift - structural break

**Category:** structural break · **Seasonality:** 12 · **Horizon:** 12 · **Synthetic** (seed-deterministic)

## What generates it

A piecewise-constant mean with two clean level shifts (at 1/3 and 2/3 of the sample: +15 then -25), a mild
monthly cycle, and Gaussian noise. Every fitted parameter that averages across the whole history is wrong in
every regime - which is exactly the point.

## What it teaches

A **structural break** violates the one-process-generated-all-of-it assumption behind every fitted model
(see [docs/analysis/changepoints.md](../analysis/changepoints.md)). Right after each break:

- Methods with long memory of the level (SES with a small alpha, mean-reverting fits) lag the new regime.
- The seasonal-naive adapts within one season; fast-adapting smoothers (high-alpha SES, Theta) recover next.
- The analysis panel diagnoses it precisely: PELT localizes both breaks to within a few samples, the OLS-CUSUM
  test rejects stability, and the Markov-switching view assigns the three regimes their own means.

## Expected honest outcome

No method should "win" dramatically here; the interesting read-out is the error trajectory around the breaks
(the streaming bench shows the coverage dip and recovery, and the ACI/PID-calibrated intervals re-widen and
re-tighten). A model that looks great on the full-sample average while failing at the breaks is exactly the
overclaim the case exists to expose.
