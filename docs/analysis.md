# Analysis toolkit

The "understand the series" half of ChronoScope. Before (and to explain) any forecast, these diagnostics
characterise a series: its stationarity, autocorrelation, seasonality, trend, drift, distribution, complexity
and fractal structure. Each method is a real, verified implementation (delegated to its authoritative library
and wrapped in one stable, NaN-safe API that carries the primary reference), computed offline in
`chronoscopelab.analysis` and baked per case so the web shows exactly the numbers the pipeline computed.

Every method is built as a vertical unit: the code, its tests, and a deep page here (theory, equations, DOIs,
and a theme-aware SVG) are authored together, in the same commit, while the context is fresh.

## Pages

- [Stationarity and unit roots](analysis/stationarity.md) - ADF, KPSS, Phillips-Perron, DF-GLS,
  Zivot-Andrews, the opposite-null insight, the four-quadrant verdict, and the FPP3 differencing rule.
- [Autocorrelation](analysis/autocorrelation.md) - ACF, PACF (Durbin-Levinson), the Bartlett band,
  Ljung-Box / Box-Pierce, Durbin-Watson, lag plots, and the Box-Jenkins AR/MA/ARMA identification.
- [Seasonality](analysis/seasonality.md) - periodogram / Welch dominant period, seasonal strength Fs,
  STL / MSTL (multi-seasonal) decomposition, and the seasonal subseries (month) plot.
- [Filters and adaptive decompositions](analysis/filters.md) - Hodrick-Prescott, Baxter-King and
  Christiano-Fitzgerald band-pass, EMD/CEEMDAN intrinsic mode functions, and the CWT wavelet scalogram.
- [Change points and regimes](analysis/changepoints.md) - PELT / Binary Segmentation, the OLS-CUSUM
  stability test, and Hamilton Markov-switching regime probabilities.

_(Volatility, distribution, entropy, and the
fractal/multifractal + nonlinear-dynamics pages follow as each unit is built.)_
