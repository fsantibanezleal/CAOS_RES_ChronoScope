# CHAO_mackey - deterministic chaos (Mackey-Glass)

**Category:** deterministic chaos · **Seasonality:** 1 · **Horizon:** 12 · **Synthetic**

## What generates it

The Mackey-Glass delay differential equation `dx/dt = 0.2 x(t-tau) / (1 + x(t-tau)^10) - 0.1 x(t)` with
tau = 17 (the canonical chaotic regime), Euler-integrated at dt = 0.1 with a seed-perturbed initial history,
a long transient discarded, and sampled every 6 time units. The sampling stride matters and was verified by
sweep: OVERSAMPLED chaos fools the 0-1 test into reading "regular" (a documented caveat); at this stride the
series shows K = 0.87 on the 0-1 test with a positive largest Lyapunov exponent (0.039).

## What it teaches

The flagship case for the nonlinear-dynamics panel (see [docs/analysis/nonlinear.md](../analysis/nonlinear.md)):

- **Deterministic but chaotic**: the surrogate gate confirms genuine nonlinearity (the correlation dimension
  sits outside the IAAFT surrogate band), the 0-1 test reads K near 1, and the Lyapunov exponent is positive -
  all three votes of the honesty gate agree, so `likely_chaotic` fires for the right reason.
- **A finite prediction horizon**: short-horizon forecasts are genuinely good (the dynamics are smooth and
  deterministic), but error grows exponentially with lead time at the Lyapunov rate. The per-horizon error
  curve is the star read-out: near-perfect at lead 1-3, degrading toward naive by the end of the horizon.
- Linear methods see "almost noise" (weak ACF); context-rich nonlinear models (NHITS, the foundation tier)
  can exploit the attractor geometry for the first few steps - the clearest separation between linear and
  nonlinear tiers in the atlas.

## Expected honest outcome

A strong ladder split by HORIZON, not by average: everyone should look decent at lead 1 and near-naive at
lead 12. Any method claiming a flat error curve across the horizon on a chaotic series is overfitting and the
case exists to catch exactly that.
