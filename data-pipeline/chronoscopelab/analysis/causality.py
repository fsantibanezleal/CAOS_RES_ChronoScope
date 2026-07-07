"""Cross-series relationships: cross-correlation, Granger causality, and cointegration.

The single-series diagnostics answer "what is this series?"; these answer "how do two series relate?" - which
one leads, whether past values of one improve forecasts of the other (Granger), and whether two nonstationary
series share a long-run equilibrium (cointegration) so their spread is stationary and forecastable even when
the levels are not. This is the analysis foundation for the covariate and multivariate cases in the product.

Methods / references (verified 2026-07-04):
  * Cross-correlation function (CCF) - correlation of x_t with y_{t-k} across lags; the lead/lag detector.
    Box-Jenkins tradition. ``statsmodels.tsa.stattools.ccf``.
  * Granger causality - does the past of x improve a forecast of y beyond y's own past? An F-test on nested
    VAR models. Granger 1969, Econometrica 37(3):424-438, DOI 10.2307/1912791. PREDICTIVE, not true cause.
    ``statsmodels.tsa.stattools.grangercausalitytests``.
  * Engle-Granger cointegration - two-step: regress one series on the other, ADF-test the residuals for a
    unit root; a single cointegrating vector. Engle & Granger 1987, Econometrica 55(2):251-276,
    DOI 10.2307/1913236. ``statsmodels.tsa.stattools.coint``.
  * Johansen cointegration - ML/VECM rank test (trace + max-eigenvalue) for MULTIPLE cointegrating relations.
    Johansen 1991, Econometrica 59(6):1551-1580, DOI 10.2307/2938278.
    ``statsmodels.tsa.vector_ar.vecm.coint_johansen``.

HONESTY: Granger "causality" is a statement about PREDICTABILITY, not mechanism - a common driver or a
confound produces Granger causality without a causal link. Cointegration requires both series to be I(1)
(unit-root nonstationary); it is meaningless on already-stationary series. The report checks and records this.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean_pair(x, y) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(x, dtype=float).ravel()
    b = np.asarray(y, dtype=float).ravel()
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    mask = np.isfinite(a) & np.isfinite(b)
    return a[mask], b[mask]


@dataclass(frozen=True)
class CrossCorrelation:
    """CCF of x vs y across signed lags, with the lag of peak absolute correlation (the lead/lag)."""

    lags: np.ndarray
    values: np.ndarray
    peak_lag: int                # >0: x leads y; <0: y leads x
    peak_value: float
    band: float                  # +/-1.96/sqrt(n) significance band
    reference: str


def cross_correlation(x, y, max_lag: int = 40) -> CrossCorrelation:
    """Cross-correlation across signed lags; a positive peak lag means x leads y.

    Defined unambiguously as corr(x_t, y_{t+k}) for k = -max_lag..max_lag. If the peak is at k > 0 then a
    future value of y correlates with the present of x (x leads y); at k < 0, y leads x. Computed directly on
    mean-centred, shifted overlaps so the sign convention is explicit (statsmodels' ccf mixes the convention).
    """
    a, b = _clean_pair(x, y)
    n = len(a)
    max_lag = min(max_lag, n - 1)
    am, bm = a - a.mean(), b - b.mean()
    denom = float(np.sqrt(np.sum(am ** 2) * np.sum(bm ** 2)))
    if denom == 0:
        denom = 1e-12
    lags = np.arange(-max_lag, max_lag + 1)
    values = np.empty(len(lags))
    for i, k in enumerate(lags):
        if k >= 0:
            # corr(x_t, y_{t+k}): overlap x[:n-k] with y[k:]
            cov = float(np.sum(am[: n - k] * bm[k:]))
        else:
            cov = float(np.sum(am[-k:] * bm[: n + k]))
        values[i] = cov / denom
    peak_idx = int(np.argmax(np.abs(values)))
    band = float(1.96 / np.sqrt(n))
    return CrossCorrelation(
        lags=lags, values=values, peak_lag=int(lags[peak_idx]), peak_value=float(values[peak_idx]),
        band=band, reference="Box & Jenkins (CCF); direct shifted-overlap correlation",
    )


@dataclass(frozen=True)
class GrangerResult:
    """Granger-causality F-test across lags: does the past of ``cause`` help predict ``effect``?"""

    direction: str               # "cause -> effect"
    best_lag: int
    pvalues: dict[int, float]
    causes: bool                 # min p-value across lags < alpha
    alpha: float
    reference: str


def granger_causality(cause, effect, max_lag: int = 6, alpha: float = 0.05) -> GrangerResult:
    """Test whether ``cause`` Granger-causes ``effect`` (past of cause improves the forecast of effect)."""
    from statsmodels.tsa.stattools import grangercausalitytests

    a, b = _clean_pair(cause, effect)
    # statsmodels tests whether the SECOND column Granger-causes the FIRST -> stack [effect, cause]
    data = np.column_stack([b, a])
    res = grangercausalitytests(data, maxlag=max_lag)
    pvals = {lag: float(res[lag][0]["ssr_ftest"][1]) for lag in res}
    best_lag = min(pvals, key=pvals.get)
    return GrangerResult(
        direction="cause -> effect", best_lag=int(best_lag), pvalues=pvals,
        causes=bool(pvals[best_lag] < alpha), alpha=alpha,
        reference="Granger 1969, Econometrica 37(3):424-438, DOI 10.2307/1912791",
    )


@dataclass(frozen=True)
class CointegrationResult:
    """Engle-Granger + Johansen cointegration verdicts for a pair of (ideally I(1)) series."""

    eg_stat: float
    eg_pvalue: float
    eg_cointegrated: bool
    johansen_trace_stat: float
    johansen_trace_crit95: float
    johansen_rank_at_least_1: bool
    both_i1: bool                # both series are unit-root nonstationary (precondition)
    alpha: float
    reference: str


def _is_i1(a: np.ndarray, alpha: float) -> bool:
    """A series is I(1) if ADF does NOT reject a unit root on levels but DOES on first differences."""
    from statsmodels.tsa.stattools import adfuller

    try:
        p_level = adfuller(a, autolag="AIC")[1]
        p_diff = adfuller(np.diff(a), autolag="AIC")[1]
        return bool(p_level >= alpha and p_diff < alpha)
    except Exception:  # noqa: BLE001
        return False


def cointegration(x, y, alpha: float = 0.05) -> CointegrationResult:
    """Engle-Granger (residual ADF) + Johansen (trace rank) cointegration, with the I(1) precondition check."""
    from statsmodels.tsa.stattools import coint
    from statsmodels.tsa.vector_ar.vecm import coint_johansen

    a, b = _clean_pair(x, y)
    eg_stat, eg_p, _crit = coint(a, b)
    j = coint_johansen(np.column_stack([a, b]), det_order=0, k_ar_diff=1)
    trace0 = float(j.trace_stat[0])
    crit95_0 = float(j.trace_stat_crit_vals[0][1])        # 95% critical value for rank r=0
    both_i1 = bool(_is_i1(a, alpha) and _is_i1(b, alpha))
    return CointegrationResult(
        eg_stat=float(eg_stat), eg_pvalue=float(eg_p), eg_cointegrated=bool(eg_p < alpha),
        johansen_trace_stat=trace0, johansen_trace_crit95=crit95_0,
        johansen_rank_at_least_1=bool(trace0 > crit95_0), both_i1=both_i1, alpha=alpha,
        reference="Engle & Granger 1987, DOI 10.2307/1913236; Johansen 1991, DOI 10.2307/2938278",
    )


def causality_report(x, y, max_lag: int = 6) -> dict:
    """Run the cross-series panel (CCF + bidirectional Granger + cointegration) and return a JSON-ready report."""
    a, b = _clean_pair(x, y)
    ccf_res = cross_correlation(a, b)
    g_xy = granger_causality(a, b, max_lag=max_lag)       # does x cause y?
    g_yx = granger_causality(b, a, max_lag=max_lag)       # does y cause x?
    coint_res = cointegration(a, b)
    return {
        "n": int(len(a)),
        "ccf": {"peak_lag": ccf_res.peak_lag, "peak_value": ccf_res.peak_value, "band": ccf_res.band,
                "lead": ("x leads y" if ccf_res.peak_lag > 0 else "y leads x" if ccf_res.peak_lag < 0 else "synchronous"),
                "reference": ccf_res.reference},
        "granger": {"x_causes_y": {"causes": g_xy.causes, "best_lag": g_xy.best_lag,
                                   "pvalue": g_xy.pvalues[g_xy.best_lag]},
                    "y_causes_x": {"causes": g_yx.causes, "best_lag": g_yx.best_lag,
                                   "pvalue": g_yx.pvalues[g_yx.best_lag]},
                    "reference": g_xy.reference},
        "cointegration": {"engle_granger_pvalue": coint_res.eg_pvalue,
                          "engle_granger_cointegrated": coint_res.eg_cointegrated,
                          "johansen_rank_at_least_1": coint_res.johansen_rank_at_least_1,
                          "both_series_I1": coint_res.both_i1,
                          "valid": coint_res.both_i1,     # cointegration is only meaningful when both are I(1)
                          "reference": coint_res.reference},
        "note": "Granger = predictability, not mechanism; cointegration requires both series I(1)",
    }
