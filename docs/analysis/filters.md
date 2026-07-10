# Trend-cycle filters and adaptive decompositions

Code: [`chronoscopelab/analysis/filters.py`](../../data-pipeline/chronoscopelab/analysis/filters.py)
· Tests: [`tests/test_analysis_filters.py`](../../tests/test_analysis_filters.py)

## Why scale-based separation (and when STL is not enough)

STL/MSTL (the [seasonality](seasonality.md) page) split a series by a **fixed period** $m$. Many series have
structure at several time scales with **no** fixed period: a slow trend, an irregular multi-year cycle,
fast transients. The tools here separate components by **frequency band** (the econometric filters) or fully
**adaptively** (EMD, wavelets), answering "what lives at which time scale, and when?".

![Separating a series by time scale](assets/filters-scales.svg)

## Hodrick-Prescott: trend by smoothness penalty

The HP filter chooses the trend $\tau_t$ minimizing

$$\sum_{t=1}^{n} (y_t - \tau_t)^2 \;+\; \lambda \sum_{t=2}^{n-1} \left[(\tau_{t+1} - \tau_t) - (\tau_t - \tau_{t-1})\right]^2 ,$$

a trade-off between fit and smoothness controlled by $\lambda$ (conventions: 1600 quarterly, 129600 monthly,
6.25 annual). The cycle is the remainder $y_t - \tau_t$; trend + cycle reconstruct the series exactly.
Hodrick & Prescott 1997, DOI [10.2307/2953682](https://doi.org/10.2307/2953682). Known caveats: end-point
bias and the possibility of spurious cycles (Hamilton's critique); ChronoScope shows HP next to the
band-pass and EMD views so no single filter is over-trusted.

## Band-pass: Baxter-King and Christiano-Fitzgerald

A band-pass filter keeps only cycles whose period lies in $[p_{low}, p_{high}]$ (classically 6-32 quarters
for business cycles).

- **Baxter-King** approximates the ideal band-pass with a **symmetric** finite moving average of order $K$;
  it is phase-neutral but loses $K$ observations at each end. Baxter & King 1999,
  DOI [10.1162/003465399558454](https://doi.org/10.1162/003465399558454).
- **Christiano-Fitzgerald** uses an **asymmetric**, random-walk-optimal approximation that keeps the full
  sample (usable in real time, at the cost of some phase shift near the ends). Christiano & Fitzgerald 2003,
  DOI [10.1111/1468-2354.t01-1-00076](https://doi.org/10.1111/1468-2354.t01-1-00076).

The report bakes CF (full-length); BK is available as a function (its end-loss makes baked panels ragged).

## EMD: adaptive intrinsic mode functions

Empirical Mode Decomposition sifts the series into **Intrinsic Mode Functions** - oscillations extracted
from the data itself, fastest first - plus a final monotone-ish **residue** (the trend):

$$y_t = \sum_{k=1}^{K} \text{IMF}_k(t) + r_t .$$

No basis or period is assumed; each IMF has a locally-defined instantaneous frequency (via the Hilbert
transform, the "Hilbert-Huang" spectrum). Huang et al. 1998, DOI
[10.1098/rspa.1998.0193](https://doi.org/10.1098/rspa.1998.0193). Plain EMD suffers **mode mixing** (one
IMF carrying disparate scales); **EEMD** (Wu & Huang 2009, DOI
[10.1142/S1793536909000047](https://doi.org/10.1142/S1793536909000047)) ensembles over added white noise,
and **CEEMDAN** (Torres et al. 2011, DOI
[10.1109/ICASSP.2011.5947265](https://doi.org/10.1109/ICASSP.2011.5947265)) adds adaptive noise per stage
with complete reconstruction. The tests assert completeness (IMFs + residue = series) and the
fastest-first ordering by zero-crossing count.

## The wavelet scalogram: energy over scale AND time

The continuous wavelet transform correlates the series with scaled/shifted copies of a mother wavelet
$\psi$:

$$W(t, s) = \frac{1}{\sqrt{s}} \int y(u)\, \psi^*\!\left(\frac{u - t}{s}\right) du ,$$

and the **scalogram** $|W(t, s)|^2$ maps energy over scale (pseudo-period) and time - showing not only which
periods carry energy but **when** (a drifting or intermittent cycle appears as a moving/broken bright band,
which a global periodogram smears). Torrence & Compo 1998, DOI
[10.1175/1520-0477(1998)079<0061:APGTWA>2.0.CO;2](https://doi.org/10.1175/1520-0477(1998)079<0061:APGTWA>2.0.CO;2).

Implementation notes: PyWavelets (`pywt.cwt`, Morlet default) - `scipy.signal.cwt` was deprecated in scipy
1.12 and **removed** in 1.15, so scipy is not an option. The series is linearly detrended by default before
the transform: an un-removed trend dumps its energy into the longest scales and swamps the cyclic structure
(the documented caveat; pass `detrend=False` for the raw picture).

## What this is, and is NOT

- These views **describe** scale structure; they are not forecasting models. HP/BK/CF cycles are
  descriptive constructs (and HP end-points are revised as data arrives - do not treat the last cycle values
  as stable).
- EMD is powerful but data-driven and non-unique: IMF counts and shapes change with noise and sample; treat
  IMFs as exploratory structure, corroborated by the scalogram/periodogram, not as physical components.
- For a clean fixed-period seasonal series, STL/MSTL (seasonality page) is the right tool; these views earn
  their place when the period drifts, breaks, or does not exist.

## Implementation notes

- `statsmodels.tsa.filters.{hp_filter.hpfilter, bk_filter.bkfilter, cf_filter.cffilter}`; `EMD-signal`
  (import `PyEMD`: `EMD`, `CEEMDAN`, `get_imfs_and_residue`); `pywt.cwt`. Inputs coerced to finite 1-D.
- `filters_report(x)` bakes: HP trend/cycle, CF band cycle, the IMFs + residue, and a compact scalogram
  summary (per-scale energy + the energy-dominant period). This is what the pipeline writes per case.

## References

- Hodrick, R.J. & Prescott, E.C. (1997). Postwar U.S. Business Cycles: An Empirical Investigation. *JMCB* 29(1):1-16. DOI [10.2307/2953682](https://doi.org/10.2307/2953682).
- Baxter, M. & King, R.G. (1999). Measuring Business Cycles: Approximate Band-Pass Filters. *REStat* 81(4):575-593. DOI [10.1162/003465399558454](https://doi.org/10.1162/003465399558454).
- Christiano, L.J. & Fitzgerald, T.J. (2003). The Band Pass Filter. *IER* 44(2):435-465. DOI [10.1111/1468-2354.t01-1-00076](https://doi.org/10.1111/1468-2354.t01-1-00076).
- Huang, N.E. et al. (1998). The empirical mode decomposition and the Hilbert spectrum. *Proc. R. Soc. A* 454:903-995. DOI [10.1098/rspa.1998.0193](https://doi.org/10.1098/rspa.1998.0193).
- Wu, Z. & Huang, N.E. (2009). Ensemble Empirical Mode Decomposition. *Adv. Adaptive Data Analysis* 1(1):1-41. DOI [10.1142/S1793536909000047](https://doi.org/10.1142/S1793536909000047).
- Torres, M.E., Colominas, M.A., Schlotthauer, G. & Flandrin, P. (2011). A complete EEMD with adaptive noise. *ICASSP* 2011:4144-4147. DOI [10.1109/ICASSP.2011.5947265](https://doi.org/10.1109/ICASSP.2011.5947265).
- Torrence, C. & Compo, G.P. (1998). A Practical Guide to Wavelet Analysis. *BAMS* 79(1):61-78. DOI [10.1175/1520-0477(1998)079<0061:APGTWA>2.0.CO;2](https://doi.org/10.1175/1520-0477(1998)079%3C0061:APGTWA%3E2.0.CO;2).
