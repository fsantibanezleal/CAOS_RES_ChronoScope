# Seasonality

Code: [`chronoscopelab/analysis/seasonality.py`](../../data-pipeline/chronoscopelab/analysis/seasonality.py)
· Tests: [`tests/test_analysis_seasonality.py`](../../tests/test_analysis_seasonality.py)

## What seasonality is, and the four questions to answer

Seasonality is a pattern that repeats at a fixed period $m$ (a day, a week, a year). Before choosing a
seasonal model, four questions must be answered (and this module answers each with a verified method):

![Finding seasonality](assets/seasonality.svg)

1. **Is there a dominant period, and what is it?** - the periodogram.
2. **How strong is it (is it worth modelling)?** - the seasonal strength $F_S$.
3. **Are there several periods (daily + weekly + yearly)?** - MSTL.
4. **What does each phase of the cycle look like?** - the seasonal subseries plot.

## The periodogram: variance per frequency

The periodogram is the squared magnitude of the (discrete) Fourier transform. For a series sampled at
frequency $f_s$ it estimates the power spectral density at frequencies $f_k = k f_s / n$,

$$P(f_k) = \frac{1}{n}\left| \sum_{t=0}^{n-1} y_t\, e^{-i 2\pi f_k t / f_s} \right|^2 .$$

Peaks reveal periodic components; the tallest non-DC (non-zero-frequency) peak gives the dominant period as
$1/f_{\text{peak}}$. Schuster 1898 introduced it; Welch 1967 averaged it over segments to reduce variance at
the cost of resolution. ChronoScope exposes both: `periodogram` (raw, sharp peaks) and `welch` (smoother).

## Seasonal strength $F_S$

From an STL decomposition $y_t = T_t + S_t + R_t$, the seasonal strength is

$$F_S = \max\!\left(0,\; 1 - \frac{\operatorname{Var}(R_t)}{\operatorname{Var}(S_t + R_t)}\right) \in [0, 1].$$

$F_S$ near 1 means most of the de-trended variance is explained by the seasonal component; near 0 means the
"season" is indistinguishable from noise. The FPP3 rule (`nsdiffs`) seasonally differences when $F_S \ge 0.64$.
Wang, Smith & Hyndman 2006 (DOI 10.1007/s10618-005-0039-x); strength form per FPP3 §4.3.

## STL and MSTL: additive trend + seasonal + remainder

**STL** (Seasonal-Trend decomposition using Loess, Cleveland et al. 1990) splits an additive series

$$y_t = T_t + S_t + R_t$$

by iterated Loess smoothing; it allows the seasonal component to evolve over time and is robust to outliers.
**MSTL** (Bandara, Hyndman & Bergmeir 2021, arXiv:2107.13462) extends STL to *multiple* seasonal periods
(e.g. $m_1 = 24$ hourly + $m_2 = 168$ weekly), returning one seasonal column per period that ChronoScope sums
into a single additive seasonal component. Both also yield a **trend strength** $F_T$, the analogue of $F_S$
for the trend.

## The seasonal subseries (month) plot

For each phase $j = 0, \ldots, m-1$, the subseries plot shows every value that landed in that phase plus the
phase mean, so the per-phase level and its variability are both legible at once. It is the standard "month
plot" (Cleveland & Terpenning 1982, DOI 10.1080/01621459.1982.10477766). `seasonal_subseries` returns the
phase means and the per-phase value arrays for the web to render.

## What this is, and is NOT

- It characterises *deterministic, fixed-period* seasonality. Slowly-drifting periods or intermittent
  cycles need the [change-points](#) (regime) and wavelet views, not a single $m$.
- A peak in the periodogram does not by itself justify a seasonal model: a long slow trend leaks power into
  low frequencies and can masquerade as a long period. Always read the periodogram together with $F_S$ (is
  the season strong?) and the subseries plot (does the per-phase profile actually cycle?).
- When $F_S$ is near 0, do **not** force a seasonal model - the variance you would attribute to a season is
  just the noise of the series.

## Implementation notes

- `scipy.signal.periodogram` (raw) and `scipy.signal.welch` (averaged) for the spectrum; `statsmodels`
  `STL` / `MSTL` for the decompositions; the per-phase split is a reshape. NaN/inf points are dropped.
- `seasonality_report(x, candidate_periods=[...])` returns a JSON-ready dict: the periodogram + Welch
  dominant periods and arrays, the per-candidate $F_S$, and (if a dominant period is found) the STL
  decomposition strengths there. This is what the pipeline bakes per case.

## References

- Schuster, A. (1898). On the investigation of hidden periodicities with application to a supposed 26-day period of meteorological phenomena. *Terrestrial Magnetism* 3(1):13-41. DOI [10.1029/TM003i001p00013](https://doi.org/10.1029/TM003i001p00013).
- Welch, P.D. (1967). The use of the fast Fourier transform for the estimation of power spectra. *IEEE Trans. Audio Electroacoust.* 15(2):70-73. DOI [10.1109/TAU.1967.1161901](https://doi.org/10.1109/TAU.1967.1161901).
- Cleveland, R.B., Cleveland, W.S., McRae, J.E. & Terpenning, I. (1990). STL: A Seasonal-Trend Decomposition Procedure Based on Loess. *J. Official Statistics* 6(1):3-73.
- Bandara, K., Hyndman, R.J. & Bergmeir, C. (2021). MSTL: A Seasonal-Trend Decomposition Algorithm for Time Series with Multiple Seasonal Patterns. arXiv:[2107.13462](https://arxiv.org/abs/2107.13462).
- Wang, X., Smith, K.A. & Hyndman, R.J. (2006). Characteristic-based clustering for time series data. *Data Mining and Knowledge Discovery* 13(3):335-364. DOI [10.1007/s10618-005-0039-x](https://doi.org/10.1007/s10618-005-0039-x).
- Cleveland, W.S. & Terpenning, I.J. (1982). Graphical methods for seasonal adjustment. *JASA* 77(377):52-62. DOI [10.1080/01621459.1982.10477766](https://doi.org/10.1080/01621459.1982.10477766).
- Hyndman, R.J. & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.), §4.3, §11.1. <https://otexts.com/fpp3/>.
