"""Autocorrelation analysis: ACF, PACF (Durbin-Levinson), Ljung-Box, Box-Pierce, Durbin-Watson.

The structure of a series' dependence on its own past is read off the ACF/PACF and quantified by the
portmanteau (Ljung-Box / Box-Pierce) and serial-correlation (Durbin-Watson) tests. Each is delegated to its
authoritative implementation in statsmodels, wrapped in one stable, NaN-safe API that returns a typed result
carrying the statistic, the p-value where defined, the Bartlett significance band, and the primary reference.

Tests / references (verified 2026-07-04):
  * ACF  - sample autocorrelation r_k = c_k / c_0, with c_k the autocovariance at lag k. Box, Jenkins,
           Reinsel & Ljung 2015, *Time Series Analysis*, 5th ed., Wiley, ISBN 978-1-118-67502-1.
           ``statsmodels.tsa.stattools.acf``. Under white noise, r_k ~ N(0, 1/n) so the 95% band is
           +/-1.96/sqrt(n) (Bartlett's approximation for independent data; wider under a MA process).
  * PACF - partial autocorrelation: the correlation at lag k after removing the effect of lags 1..k-1,
           computed here by the Durbin-Levinson recursion (``method='ld'``). Identifies the AR order p
           (PACF cuts off after p). Same reference.
  * Ljung-Box - portmanteau test that the first m autocorrelations are jointly zero; the standard
           "are the residuals white noise?" check. Ljung & Box 1978, Biometrika 65(2):297-303,
           DOI 10.1093/biomet/65.2.297. ``statsmodels.stats.diagnostic.acorr_ljungbox``.
  * Box-Pierce - the older portmanteau (Ljung-Box is its small-sample refinement). Box & Pierce 1970,
           JASA 65(332):1509-1526, DOI 10.2307/2284333. Same function, ``boxpierce=True``.
  * Durbin-Watson - tests first-order serial correlation in regression residuals (DW~2 = none, <2 positive
           serial correlation, >2 negative). Durbin & Watson 1950, Biometrika 37(3-4):409-428,
           DOI 10.1093/biomet/37.3-4.409. ``statsmodels.stats.stattools.durbin_watson``.

How to read them together (Box-Jenkins identification): a slowly-decaying ACF with a sharp PACF cut-off after
lag p suggests an AR(p); a sharp ACF cut-off after lag q with a slowly-decaying PACF suggests an MA(q); both
tailing off suggests ARMA. White noise has every r_k inside the Bartlett band and a non-significant Ljung-Box.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Correlogram:
    """ACF or PACF up to ``nlags``, with point values, the Bartlett band, and the read-out.

    ``signif_lags`` lists the lags whose value escapes the +/-1.96/sqrt(n) band (the spikes a reader would
    mark), already translated so callers do not have to re-derive the threshold.
    """

    name: str
    lags: np.ndarray
    values: np.ndarray
    band: float
    reference: str
    signif_lags: list[int] = field(default_factory=list)


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


def bartlett_band(n: int, alpha: float = 0.05) -> float:
    """The +/- z_{1-alpha/2}/sqrt(n) significance bound for the ACF of an independent series.

    For alpha=0.05 this is the familiar +/-1.96/sqrt(n). Bartlett's formula gives a wider, variance-
    dependent band under a moving-average process; the simple form is the standard first-pass threshold.
    """
    if n <= 0:
        return float("inf")
    # Normal quantile via the inverse error function (accurate; matches statsmodels' default band).
    from scipy.special import erfinv

    z = math.sqrt(2.0) * erfinv(1.0 - alpha)
    return float(z / math.sqrt(n))


def acf(x, nlags: int = 40, alpha: float = 0.05) -> Correlogram:
    """Sample autocorrelation function with the Bartlett significance band (statsmodels, FFT-based)."""
    from statsmodels.tsa.stattools import acf as _acf

    a = _clean(x)
    n = len(a)
    nlags = min(nlags, n - 1)
    values = _acf(a, nlags=nlags, fft=True, missing="drop")
    lags = np.arange(len(values))
    band = bartlett_band(n, alpha)
    signif = [int(k) for k in lags[1:] if abs(values[k]) > band]  # exclude the trivial lag-0 = 1
    return Correlogram(
        name="ACF", lags=lags, values=values, band=band, signif_lags=signif,
        reference="Box, Jenkins, Reinsel & Ljung 2015, Time Series Analysis, 5th ed., Wiley, ISBN 978-1-118-67502-1",
    )


def pacf(x, nlags: int = 40, alpha: float = 0.05) -> Correlogram:
    """Partial autocorrelation via the Durbin-Levinson recursion (``method='ld'``) with the Bartlett band."""
    from statsmodels.tsa.stattools import pacf as _pacf

    a = _clean(x)
    n = len(a)
    nlags = min(nlags, n - 1)
    values = _pacf(a, nlags=nlags, method="ld")
    lags = np.arange(len(values))
    band = bartlett_band(n, alpha)
    signif = [int(k) for k in lags[1:] if abs(values[k]) > band]
    return Correlogram(
        name="PACF", lags=lags, values=values, band=band, signif_lags=signif,
        reference="Durbin-Levinson recursion; Box, Jenkins, Reinsel & Ljung 2015, ISBN 978-1-118-67502-1",
    )


@dataclass(frozen=True)
class PortmanteauTest:
    """Ljung-Box or Box-Pierce: a joint test that the first ``lags`` autocorrelations are all zero."""

    name: str
    stat: float
    pvalue: float
    lags: int
    df: int
    white_noise: bool | None
    reference: str


def ljung_box(x, lags: int | list[int] = 10, model_df: int = 0, alpha: float = 0.05) -> PortmanteauTest:
    """Ljung-Box Q. Small p => reject "no autocorrelation up to lag m" => the series is NOT white noise.

    ``model_df`` is the number of ARMA parameters already fitted, subtracted from the degrees of freedom when
    the test is run on residuals (so the residual diagnostic is not biased toward significance).
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox

    a = _clean(x)
    m = max(lags) if isinstance(lags, (list, tuple)) else int(lags)
    res = acorr_ljungbox(a, lags=[m], model_df=model_df, return_df=True)
    stat = float(res["lb_stat"].iloc[0])
    pvalue = float(res["lb_pvalue"].iloc[0])
    return PortmanteauTest(
        name="Ljung-Box", stat=stat, pvalue=pvalue, lags=m, df=max(0, m - model_df),
        white_noise=bool(pvalue >= alpha),
        reference="Ljung & Box 1978, Biometrika 65(2):297-303, DOI 10.1093/biomet/65.2.297",
    )


def box_pierce(x, lags: int = 10, model_df: int = 0, alpha: float = 0.05) -> PortmanteauTest:
    """Box-Pierce: the older portmanteau; Ljung-Box is its small-sample refinement."""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    a = _clean(x)
    res = acorr_ljungbox(a, lags=[int(lags)], boxpierce=True, model_df=model_df, return_df=True)
    stat = float(res["bp_stat"].iloc[0])
    pvalue = float(res["bp_pvalue"].iloc[0])
    return PortmanteauTest(
        name="Box-Pierce", stat=stat, pvalue=pvalue, lags=int(lags), df=max(0, int(lags) - model_df),
        white_noise=bool(pvalue >= alpha),
        reference="Box & Pierce 1970, JASA 65(332):1509-1526, DOI 10.2307/2284333",
    )


def durbin_watson(x) -> float:
    """Durbin-Watson statistic on (residual) series: ~2 = no 1st-order serial correlation, <2 positive, >2 negative."""
    from statsmodels.stats.stattools import durbin_watson as _dw

    a = _clean(x)
    return float(_dw(a))


def lag_plot_pairs(x, lag: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Return the (x_{t-lag}, x_t) pairs a lag plot would render, dropping non-finite points.

    A linear band => AR(1)-style dependence; a circular cloud => white noise; curved => nonlinearity;
    isolated off-diagonal points => outliers (NIST e-Handbook sec. 1.3.3.15).
    """
    a = _clean(x)
    if lag < 1 or lag >= len(a):
        raise ValueError(f"lag must be in 1..{len(a) - 1}, got {lag}")
    return a[:-lag], a[lag:]


def autocorrelation_report(x, nlags: int = 40, lags_m: int = 10) -> dict:
    """Run the full autocorrelation panel and return a JSON-ready report (for the baked artifact + docs)."""
    a = _clean(x)
    n = len(a)
    acf_c = acf(a, nlags=nlags)
    pacf_c = pacf(a, nlags=nlags)
    lb = ljung_box(a, lags=lags_m)
    bp = box_pierce(a, lags=lags_m)
    return {
        "n": int(n),
        "bartlett_band": acf_c.band,
        "acf": [{"lag": int(k), "value": float(v)} for k, v in zip(acf_c.lags, acf_c.values)],
        "acf_signif_lags": acf_c.signif_lags,
        "pacf": [{"lag": int(k), "value": float(v)} for k, v in zip(pacf_c.lags, pacf_c.values)],
        "pacf_signif_lags": pacf_c.signif_lags,
        "ljung_box": {"stat": lb.stat, "pvalue": lb.pvalue, "lags": lb.lags, "white_noise": lb.white_noise,
                      "reference": lb.reference},
        "box_pierce": {"stat": bp.stat, "pvalue": bp.pvalue, "lags": bp.lags, "white_noise": bp.white_noise,
                       "reference": bp.reference},
        "durbin_watson": durbin_watson(a),
        "identification_hint": _identify(acf_c, pacf_c, lb),
    }


def _identify(acf_c: Correlogram, pacf_c: Correlogram, lb: PortmanteauTest) -> str:
    """A conservative Box-Jenkins reading of the correlograms (a hint, not a fitted model)."""
    if lb.white_noise:
        return "no significant autocorrelation (white-noise-like); ARMA identification not warranted"
    # tail-off vs cut-off via the count of signif lags and the decay of |acf| over the last quarter
    a_vals = np.abs(acf_c.values[1:])
    p_vals = np.abs(pacf_c.values[1:])
    if len(a_vals) < 4:
        return "series too short for a reliable ARMA-shape reading"
    a_tail = float(np.mean(a_vals[len(a_vals) // 2:]))  # ACF in its later half
    p_tail = float(np.mean(p_vals[len(p_vals) // 2:]))
    a_band, p_band = acf_c.band, pacf_c.band
    if p_tail < a_band and a_tail > a_band:
        return "ACF tails off, PACF cuts off -> suggests an AR(p) (p ~ last significant PACF lag)"
    if a_tail < a_band and p_tail > p_band:
        return "ACF cuts off, PACF tails off -> suggests an MA(q) (q ~ last significant ACF lag)"
    if a_tail > a_band and p_tail > p_band:
        return "both tail off -> suggests ARMA; fit by AIC over a small (p,q) grid"
    return "autocorrelation present but shape is mixed; inspect the correlograms directly"
