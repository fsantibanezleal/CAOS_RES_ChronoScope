# Distribution, normality, and complexity

Code: [`chronoscopelab/analysis/distribution.py`](../../data-pipeline/chronoscopelab/analysis/distribution.py)
· Tests: [`tests/test_analysis_distribution.py`](../../tests/test_analysis_distribution.py)

## Two independent questions

This unit answers two questions that constrain forecasting in different ways:

![Distribution vs complexity](assets/distribution-complexity.svg)

1. **What values occur?** - the distribution's shape, tails, and normality. This decides which error model and
   prediction intervals are valid (Gaussian intervals on a heavy-tailed series under-cover).
2. **How predictable is the ordering?** - entropy measures and a nonlinearity test. A series can be perfectly
   Gaussian in its histogram yet either highly structured (low entropy, forecastable) or i.i.d. noise (high
   entropy, near-unforecastable). The histogram cannot tell these apart; the complexity measures can.

## Distribution: moments, KDE, Q-Q, normality

**Moments** summarise shape: the **skewness** (asymmetry) and **excess kurtosis** (tail-heaviness relative to
a normal, which has excess kurtosis 0). A **kernel density estimate** smooths the histogram into a continuous
density $\hat f(x) = \frac{1}{nh}\sum_i K\!\big(\frac{x - x_i}{h}\big)$ (Gaussian kernel $K$; Parzen 1962). A
**normal Q-Q plot** puts the ordered sample quantiles against theoretical normal quantiles - points on the
line mean normality, an S-curve means skew, and fat ends mean heavy tails.

Two normality tests, with different strengths:

- **Jarque-Bera** builds a statistic from skewness $S$ and excess kurtosis $K$,
  $$JB = \frac{n}{6}\left(S^2 + \frac{K^2}{4}\right) \sim \chi^2_2 ,$$
  powerful in large samples (Jarque & Bera 1980, DOI
  [10.1016/0165-1765(80)90024-5](https://doi.org/10.1016/0165-1765(80)90024-5)).
- **Shapiro-Wilk** is the most powerful general normality test for small-to-moderate $n$ (Shapiro & Wilk
  1965, DOI [10.1093/biomet/52.3-4.591](https://doi.org/10.1093/biomet/52.3-4.591)); ChronoScope runs it for
  $3 \le n \le 5000$ and combines both verdicts.

## Complexity: how much structure is in the ordering?

Entropy measures quantify regularity. Low entropy = predictable, high entropy = random:

- **Sample entropy** is the (bias-corrected) negative log conditional probability that sequences close for
  $m$ points stay close for $m{+}1$ (Richman & Moorman 2000, DOI
  [10.1152/ajpheart.2000.278.6.H2039](https://doi.org/10.1152/ajpheart.2000.278.6.H2039)).
- **Permutation entropy** is the Shannon entropy of the ordinal patterns of length $m$ - robust to noise and
  monotone transforms (Bandt & Pompe 2002, DOI
  [10.1103/PhysRevLett.88.174102](https://doi.org/10.1103/PhysRevLett.88.174102)); normalized to $[0,1]$.
- **Spectral entropy** is the Shannon entropy of the normalized power spectral density - a flat spectrum
  (white noise) is maximal, a peaked spectrum (a clean cycle) is low; normalized to $[0,1]$.

The **BDS test** asks whether the series is i.i.d. against the alternative of *hidden nonlinear structure*,
via the correlation integral across embedding dimensions (Broock, Scheinkman, Dechert & LeBaron 1996, DOI
[10.1080/07474939608800353](https://doi.org/10.1080/07474939608800353)). It is the standard residual
diagnostic for "is there anything a linear model missed?".

## What this is, and is NOT

- The distribution constrains the *error model*, not the *point forecast*: a heavy-tailed series can still
  have a perfectly forecastable conditional mean, but its intervals must be widened (or a Student-t error
  used) rather than assumed Gaussian.
- Entropy is a *relative* quantity: compare it across series or against a shuffled surrogate, not against an
  absolute threshold. Low entropy signals exploitable structure; it does not name the model.
- BDS is a nonlinearity screen, not a chaos test - a rejection means "not i.i.d.", which could be linear
  autocorrelation, nonlinearity, or non-stationarity; corroborate with the autocorrelation and
  [nonlinear-dynamics](#) pages.

## Implementation notes

- Distribution via `scipy.stats` (`skew`, `kurtosis`, `jarque_bera`, `shapiro`, `gaussian_kde`, `probplot`);
  entropy via `antropy` (`sample_entropy`, `perm_entropy`, `spectral_entropy`); BDS via
  `statsmodels.tsa.stattools.bds`. Inputs coerced to finite 1-D.
- **catch22** (22 canonical features, Lubba et al. 2019, DOI
  [10.1007/s10618-019-00647-x](https://doi.org/10.1007/s10618-019-00647-x)) is optional: `pycatch22` needs a
  C toolchain to build its extension. When it is not installed the report records that **honestly**
  (`catch22.available = false` with the reason) - it never fabricates the values. Install `pycatch22` in an
  environment with a compiler to enable it.
- `distribution_report(x)` bakes the moments + normality verdicts, a KDE curve, Q-Q points, the entropy
  triple + BDS verdict, and the catch22 block (features or the honest unavailable marker).

## References

- Parzen, E. (1962). On Estimation of a Probability Density Function and Mode. *Ann. Math. Stat.* 33(3):1065-1076. DOI [10.1214/aoms/1177704472](https://doi.org/10.1214/aoms/1177704472).
- Wilk, M.B. & Gnanadesikan, R. (1968). Probability plotting methods for the analysis of data. *Biometrika* 55(1):1-17. DOI [10.1093/biomet/55.1.1](https://doi.org/10.1093/biomet/55.1.1).
- Jarque, C.M. & Bera, A.K. (1980). Efficient tests for normality, homoscedasticity and serial independence of regression residuals. *Economics Letters* 6(3):255-259. DOI [10.1016/0165-1765(80)90024-5](https://doi.org/10.1016/0165-1765(80)90024-5).
- Shapiro, S.S. & Wilk, M.B. (1965). An analysis of variance test for normality (complete samples). *Biometrika* 52(3-4):591-611. DOI [10.1093/biomet/52.3-4.591](https://doi.org/10.1093/biomet/52.3-4.591).
- Richman, J.S. & Moorman, J.R. (2000). Physiological time-series analysis using approximate entropy and sample entropy. *Am. J. Physiol. Heart Circ. Physiol.* 278(6):H2039-H2049. DOI [10.1152/ajpheart.2000.278.6.H2039](https://doi.org/10.1152/ajpheart.2000.278.6.H2039).
- Bandt, C. & Pompe, B. (2002). Permutation Entropy: A Natural Complexity Measure for Time Series. *Phys. Rev. Lett.* 88:174102. DOI [10.1103/PhysRevLett.88.174102](https://doi.org/10.1103/PhysRevLett.88.174102).
- Broock, W.A., Scheinkman, J.A., Dechert, W.D. & LeBaron, B. (1996). A test for independence based on the correlation dimension. *Econometric Reviews* 15(3):197-235. DOI [10.1080/07474939608800353](https://doi.org/10.1080/07474939608800353).
- Lubba, C.H., Sethi, S.S., Knaute, P., Schultz, S.R., Fulcher, B.D. & Jones, N.S. (2019). catch22: CAnonical Time-series CHaracteristics. *Data Min. Knowl. Disc.* 33(6):1821-1852. DOI [10.1007/s10618-019-00647-x](https://doi.org/10.1007/s10618-019-00647-x).
