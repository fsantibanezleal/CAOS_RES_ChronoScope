# HETV_garch - heteroscedastic volatility clustering

**Category:** heteroscedastic (GARCH) · **Seasonality:** 1 · **Horizon:** 12 · **Synthetic**

## What generates it

GARCH(1,1) innovations (omega 0.2, alpha 0.15, beta 0.80: persistence 0.95, strongly clustered volatility)
accumulated onto a level - a finance-style path whose POINT dynamics are near-random-walk but whose VARIANCE
is highly structured.

## What it teaches

This is the case where the point-forecast leaderboard is deliberately boring and the INTERVAL story is
everything (see [docs/analysis/volatility.md](../analysis/volatility.md)):

- Point MASE: nothing should beat the naive by much - the conditional mean is almost unforecastable, and any
  method that appears to win on the point is fitting noise.
- The **analysis panel** flags it precisely: ARCH-LM fires (variance clusters), the fitted GARCH recovers the
  ~0.95 persistence, and the rolling-std band shows the calm/turbulent regimes.
- The **streaming bench** is the payoff: a fixed-width interval under-covers in turbulent stretches and
  over-covers in calm ones, while the ACI / Conformal-PID calibrated intervals breathe with the regime and
  hold the 80% target - the clearest demonstration in the whole atlas of why online conformal calibration
  (our preqts package) matters.

## Expected honest outcome

Best-point-method is noise; report it without narrative. The meaningful comparison is rolling COVERAGE
(raw vs calibrated) and interval width, where the calibrated variants should visibly track the target.
