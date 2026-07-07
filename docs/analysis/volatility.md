# Volatility and variance-stabilizing transforms

Code: [`chronoscopelab/analysis/volatility.py`](../../data-pipeline/chronoscopelab/analysis/volatility.py)
· Tests: [`tests/test_analysis_volatility.py`](../../tests/test_analysis_volatility.py)

## Why the second moment matters

Most forecasting assumes homoscedasticity (constant variance). Many real series - financial returns, energy
prices, demand under shocks - instead show **volatility clustering**: calm stretches and turbulent stretches,
"large changes tend to be followed by large changes" (Mandelbrot 1963). Ignoring it produces prediction
intervals that are too narrow in turbulent regimes and too wide in calm ones. This unit answers two
questions:

![Volatility analysis](assets/volatility.svg)

1. **Does the variance cluster?** - Engle's ARCH-LM test, then a fitted GARCH model.
2. **Can a transform stabilize a growing variance?** - the Box-Cox family (MLE or Guerrero lambda).

Scope note: GARCH here characterises **volatility** (the second moment) as an *analysis* diagnostic, not a
point-forecast method - it explains why a point forecast's intervals should breathe with the regime.

## ARCH-LM: is there conditional heteroscedasticity?

Regress the squared (mean-)residuals on their own lags,

$$\hat e_t^2 = \gamma_0 + \sum_{i=1}^{m} \gamma_i\, \hat e_{t-i}^2 + u_t ,$$

and test $H_0: \gamma_1 = \cdots = \gamma_m = 0$ (no ARCH). Under the null $n R^2 \sim \chi^2_m$. A small
p-value means the squared residuals are autocorrelated - variance clusters. Engle 1982, DOI
[10.2307/1912773](https://doi.org/10.2307/1912773). Implemented by `statsmodels.stats.diagnostic.het_arch`.

## GARCH: modelling the conditional variance

When ARCH effects are present, a GARCH(p,q) model gives the variance its own recursion,

$$\sigma_t^2 = \omega + \sum_{i=1}^{q} \alpha_i\, \varepsilon_{t-i}^2 + \sum_{j=1}^{p} \beta_j\, \sigma_{t-j}^2 ,$$

so the conditional volatility $\sigma_t$ rises after large shocks and decays back. The **persistence**
$\sum \alpha_i + \sum \beta_j$ measures how long shocks linger (near 1 = very persistent, IGARCH-like).
Bollerslev 1986, DOI [10.1016/0304-4076(86)90063-1](https://doi.org/10.1016/0304-4076(86)90063-1). Variants:
**EGARCH** captures leverage (negative shocks raise volatility more than positive), **FIGARCH** captures
*long-memory* volatility (fractional integration) - the same long-memory idea the [fractal](#) page treats
for the mean. Implemented by `arch.arch_model` (Kevin Sheppard). ChronoScope fits GARCH **only when ARCH-LM
is significant** - fitting a volatility model to a homoscedastic series is not warranted, and the report
records that it was skipped.

## Box-Cox: variance-stabilizing transforms

If the amplitude of the fluctuations grows with the level (a multiplicative series), a power transform can
make it additive-model-ready. The Box-Cox family is

$$y^{(\lambda)} = \begin{cases} \dfrac{y^\lambda - 1}{\lambda}, & \lambda \ne 0 \\[4pt] \log y, & \lambda = 0 \end{cases}, \qquad y > 0 .$$

Two ways to choose $\lambda$:

- **MLE** (`scipy.stats.boxcox`) maximizes the profile likelihood of the transformed data being normal.
- **Guerrero** (`coreforecast.scalers.boxcox_lambda(method='guerrero', season_length=m)`) minimizes the
  coefficient of variation *across seasonal subseries* - it targets variance stabilization directly and is
  the right choice for seasonal series. Guerrero 1993, DOI
  [10.1002/for.3980120104](https://doi.org/10.1002/for.3980120104).

Box-Cox requires $y > 0$; when the series has non-positive values ChronoScope shifts it by $1 - \min(y)$ and
**records the shift** so the transform is invertible and honest.

## What this is, and is NOT

- ARCH/GARCH describe variance, not the mean. A GARCH fit does not improve the *point* forecast; it informs
  the *intervals* and flags regimes where a constant-variance model would mislead.
- A Box-Cox transform is a modelling convenience, not a truth: forecasts made in transformed space must be
  back-transformed (with a bias correction for the mean), and the chosen $\lambda$ is data-dependent - report
  it, do not hide it.
- Persistence near 1 (IGARCH) signals shocks that effectively never decay; treat long-horizon volatility
  forecasts there with suspicion.

## Implementation notes

- `statsmodels.stats.diagnostic.het_arch`; `arch.arch_model` (GARCH/EGARCH/FIGARCH, `rescale=True` so the
  optimizer sees a well-scaled series); `scipy.stats.boxcox` + `scipy.special.boxcox`;
  `coreforecast.scalers.boxcox_lambda` (Guerrero, an already-installed dependency). Inputs coerced to finite
  1-D; GARCH and Box-Cox failures are recorded in the report, never crash the bake.
- `volatility_report(x, season_length=)` bakes: the ARCH-LM verdict, a rolling mean/std band, the Box-Cox
  lambda (Guerrero if a season is given, else MLE) + shift, and a GARCH fit **iff** ARCH is present.

## References

- Engle, R.F. (1982). Autoregressive Conditional Heteroscedasticity with Estimates of the Variance of United Kingdom Inflation. *Econometrica* 50(4):987-1007. DOI [10.2307/1912773](https://doi.org/10.2307/1912773).
- Bollerslev, T. (1986). Generalized Autoregressive Conditional Heteroskedasticity. *J. Econometrics* 31(3):307-327. DOI [10.1016/0304-4076(86)90063-1](https://doi.org/10.1016/0304-4076(86)90063-1).
- Box, G.E.P. & Cox, D.R. (1964). An Analysis of Transformations. *JRSS-B* 26(2):211-252. JSTOR [2984418](https://www.jstor.org/stable/2984418).
- Guerrero, V.M. (1993). Time-series analysis supported by power transformations. *J. Forecasting* 12(1):37-48. DOI [10.1002/for.3980120104](https://doi.org/10.1002/for.3980120104).
