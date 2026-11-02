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
- The **streaming bench** compares rolling coverage under raw, ACI and Conformal-PID intervals. The stored
  artifact does not include interval-width trajectories, so it cannot establish how interval size changes
  between calm and turbulent stretches or identify a uniquely clearest case.

## Expected honest outcome

Best-point-method is noise; report it without narrative. The stored comparison covers rolling MASE,
coverage and WQL. It does not contain an interval-width trajectory.
