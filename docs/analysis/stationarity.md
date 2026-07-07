# Stationarity and unit roots

Code: [`chronoscopelab/analysis/stationarity.py`](../../data-pipeline/chronoscopelab/analysis/stationarity.py)
· Tests: [`tests/test_analysis_stationarity.py`](../../tests/test_analysis_stationarity.py)

## What stationarity is, and why forecasting needs it

A series is (weakly) **stationary** when its mean, variance and autocovariance do not change over time: for
all $t$ and lag $k$,

$$\mathbb{E}[y_t] = \mu, \qquad \operatorname{Var}(y_t) = \sigma^2, \qquad \operatorname{Cov}(y_t, y_{t-k}) = \gamma_k .$$

Most of the classical ladder assumes it. An ARMA model is only well-defined on a stationary series; the "I"
in ARIMA is exactly the differencing $\nabla^d y_t = (1-B)^d y_t$ that removes a stochastic trend before an
ARMA is fitted (here $B$ is the backshift operator, $B y_t = y_{t-1}$). Fitting a stationary model to a
**non-stationary** series produces spurious regression: apparent structure and significance that vanish out
of sample. So "is this series stationary, and if not how many differences make it so?" is the first question
this toolkit answers, and it feeds the differencing order $d$ (and seasonal $D$) that AutoARIMA searches over.

A **unit root** is the canonical form of non-stationarity. Write the AR(1)

$$y_t = \phi\, y_{t-1} + \varepsilon_t .$$

If $|\phi| < 1$ the series is stationary (shocks decay); if $\phi = 1$ it is a **random walk**
$y_t = y_{t-1} + \varepsilon_t$, whose variance $\operatorname{Var}(y_t) = t\,\sigma^2$ grows without bound
and whose shocks are permanent. The tests below decide, from a finite sample, which regime we are in.

## The tests (and the one insight that ties them together)

The single most important thing about these tests is that **ADF and KPSS have opposite null hypotheses.**
Reading one as if it were the other is the most common mistake, so the API returns a `null` field and a
`stationary` verdict already translated to the common language.

![Stationarity decision flow](assets/stationarity-decision.svg)

### ADF - Augmented Dickey-Fuller

Regress the differenced series on the lagged level, a deterministic term, and $p$ lagged differences to
soak up serial correlation (the "augmentation"):

$$\Delta y_t = \alpha + \beta t + \gamma\, y_{t-1} + \sum_{i=1}^{p} \delta_i\, \Delta y_{t-i} + \varepsilon_t .$$

The null is $H_0:\gamma = 0$ (a **unit root**, non-stationary) against $H_1:\gamma < 0$ (stationary). The
statistic is the $t$-ratio on $\hat{\gamma}$, but under $H_0$ it does **not** follow a $t$ distribution, so
it is compared to Dickey-Fuller critical values. A small p-value **rejects the unit root**, i.e. is evidence
the series is stationary. Dickey & Fuller 1979, DOI [10.1080/01621459.1979.10482531](https://doi.org/10.1080/01621459.1979.10482531).

### KPSS

KPSS flips the null: $H_0$ is **stationarity** (around a level or a trend), $H_1$ a unit root. It decomposes
the series into a deterministic trend, a random walk, and a stationary error and tests whether the random-walk
variance is zero. With partial sums $S_t = \sum_{i=1}^{t} \hat{e}_i$ of the regression residuals and a
long-run variance estimate $\hat{\sigma}^2_{\text{LR}}$, the LM statistic is

$$\text{KPSS} = \frac{1}{n^2\,\hat{\sigma}^2_{\text{LR}}} \sum_{t=1}^{n} S_t^2 .$$

Here a small p-value **rejects stationarity** (the opposite polarity to ADF). Kwiatkowski, Phillips, Schmidt
& Shin 1992, DOI [10.1016/0304-4076(92)90104-Y](https://doi.org/10.1016/0304-4076(92)90104-Y).

### Phillips-Perron and DF-GLS (higher power, different corrections)

- **Phillips-Perron** keeps the DF regression but corrects for serial correlation and heteroscedasticity
  **non-parametrically** (a HAC adjustment to the statistic) rather than by adding lags. Same unit-root null.
  Phillips & Perron 1988, DOI [10.1093/biomet/75.2.335](https://doi.org/10.1093/biomet/75.2.335). Implemented
  by `arch.unitroot.PhillipsPerron` (statsmodels has no PP).
- **DF-GLS** first removes the deterministic part by **GLS** detrending, which makes the test locally most
  powerful (it detects near-unit-roots that ADF misses). Elliott, Rothenberg & Stock 1996,
  DOI [10.2307/2171846](https://doi.org/10.2307/2171846). Implemented by `arch.unitroot.DFGLS`.

### Zivot-Andrews (a break-aware test)

A trend break can masquerade as a unit root. Zivot-Andrews allows **one endogenous structural break** in the
level and/or trend, choosing the break date that most favours rejecting the unit root, and reports that break
index. Zivot & Andrews 1992, DOI [10.1080/07350015.1992.10509904](https://doi.org/10.1080/07350015.1992.10509904).

## Reading the two nulls together: the four-quadrant verdict

Because ADF and KPSS point opposite ways, their four combinations are informative (`combined_verdict`):

| | KPSS: stationary | KPSS: rejects (non-stationary) |
|---|---|---|
| **ADF: rejects (stationary)** | stationary (both agree) | difference-stationary (needs differencing) |
| **ADF: unit root** | trend-stationary (detrend, don't difference) | non-stationary (both agree) |

The off-diagonal cases are the useful ones: they separate a **difference-stationary** series (remove a
stochastic trend by differencing) from a **trend-stationary** one (remove a deterministic trend by
detrending). This four-quadrant table is standard general econometrics; note it is **not** what FPP3
prescribes for choosing $d$ (below).

## Choosing the differencing order (the FPP3 procedure)

For the actual number of differences, ChronoScope follows Hyndman & Athanasopoulos, *Forecasting: Principles
and Practice* (3rd ed.), §9.1, not the four-quadrant heuristic:

- **`ndiffs`** (non-seasonal $d$): apply KPSS; while it **rejects** stationarity, difference once more and
  re-test, up to `max_d`. This is the KPSS-sequential `unitroot_ndiffs` rule.
- **`nsdiffs`** (seasonal $D$): difference seasonally while the **seasonal strength** exceeds $0.64$. From an
  STL decomposition $y_t = T_t + S_t + R_t$, the strength is

$$F_S = \max\!\left(0,\; 1 - \frac{\operatorname{Var}(R_t)}{\operatorname{Var}(S_t + R_t)}\right),$$

  (Wang, Smith & Hyndman 2006, DOI [10.1007/s10618-005-0039-x](https://doi.org/10.1007/s10618-005-0039-x);
  strength form per FPP3 §4.3). $F_S$ near 1 means strong seasonality; the threshold $0.64$ is the FPP3 rule.

## What this is, and is NOT

- It answers "does the series have a stochastic trend, and how many differences remove it?", feeding $d$/$D$.
- It is **not** a forecastability verdict. A stationary series can still be near-unforecastable (white noise),
  and differencing a series that did not need it (over-differencing) injects an MA unit root and inflates
  variance. Pair these tests with the autocorrelation and forecastability pages before concluding.
- The tests are asymptotic: on short series (n < ~50) they have low power and wide uncertainty; treat a
  single p-value near the threshold as inconclusive, which is why the panel reports five tests, not one.

## Implementation notes

- Delegated to the authoritative implementations: ADF/KPSS/Zivot-Andrews via `statsmodels`, Phillips-Perron
  and DF-GLS via `arch` (statsmodels has neither). Inputs are coerced to finite 1-D arrays (non-finite points
  dropped) so the tests never crash on gaps.
- `stationarity_report(x, period)` runs the whole panel and returns a JSON-ready dict (statistic, p-value,
  critical values, null, verdict, and the reference per test) plus the recommended $d$ and $D$; this is what
  the pipeline bakes per case and the web renders.

## References

- Dickey, D.A. & Fuller, W.A. (1979). *JASA* 74(366):427-431. DOI [10.1080/01621459.1979.10482531](https://doi.org/10.1080/01621459.1979.10482531).
- Kwiatkowski, D., Phillips, P.C.B., Schmidt, P. & Shin, Y. (1992). *J. Econometrics* 54:159-178. DOI [10.1016/0304-4076(92)90104-Y](https://doi.org/10.1016/0304-4076(92)90104-Y).
- Phillips, P.C.B. & Perron, P. (1988). *Biometrika* 75(2):335-346. DOI [10.1093/biomet/75.2.335](https://doi.org/10.1093/biomet/75.2.335).
- Elliott, G., Rothenberg, T.J. & Stock, J.H. (1996). *Econometrica* 64(4):813-836. DOI [10.2307/2171846](https://doi.org/10.2307/2171846).
- Zivot, E. & Andrews, D.W.K. (1992). *J. Business & Economic Statistics* 10(3):251-270. DOI [10.1080/07350015.1992.10509904](https://doi.org/10.1080/07350015.1992.10509904).
- Wang, X., Smith, K.A. & Hyndman, R.J. (2006). *Data Mining and Knowledge Discovery* 13(3):335-364. DOI [10.1007/s10618-005-0039-x](https://doi.org/10.1007/s10618-005-0039-x).
- Hyndman, R.J. & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.), §4.3, §9.1. <https://otexts.com/fpp3/>.
