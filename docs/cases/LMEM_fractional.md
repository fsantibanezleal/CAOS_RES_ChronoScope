# LMEM_fractional - long memory (ARFIMA d = 0.35)

**Category:** long memory · **Seasonality:** 1 · **Horizon:** 12 · **Synthetic**

## What generates it

Fractionally-integrated noise: the truncated MA(infinity) expansion of `(1-B)^(-d) eps_t` with d = 0.35
(psi_k built by the recursive Gamma-ratio form; Granger & Joyeux 1980, Hosking 1981). The result is a
stationary series whose autocorrelation decays HYPERBOLICALLY (not exponentially): genuine long-range
dependence with Hurst H = d + 0.5 = 0.85.

## What it teaches

The case that vindicates the fractal panel (see [docs/analysis/fractal.md](../analysis/fractal.md)):

- **DFA alpha ~ 0.85** (verified at generation: 0.825 measured) - persistent long memory, far from the 0.5
  of white noise, and the ARFIMA link d = H - 0.5 recovers the generating parameter.
- The ACF decays slowly across dozens of lags (the autocorrelation panel makes the hyperbolic tail visible
  against an AR(1)'s exponential decay), yet ADF/KPSS still call the series stationary - long memory is NOT
  a unit root, and conflating them (over-differencing) destroys the exploitable structure.
- Methods with genuinely long context (foundation models; NHITS's coarse pooling) can exploit the memory;
  short-memory classical methods (SES/Holt) waste it.

## Expected honest outcome

A modest but REAL edge for long-context methods over short-memory ones, with the fractal + autocorrelation
panels explaining the mechanism. The honest caveat from the fractal page applies: H far from 0.5 signals
exploitable structure, it does not promise a large edge - the point is that the DIAGNOSIS and the LADDER
agree.
