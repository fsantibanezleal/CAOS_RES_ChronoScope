"""Stationarity and unit-root analysis: real, verified tests, not toy reimplementations.

The forecasting question "is this series stationary, and if not how many differences make it so?" is
answered here by the standard unit-root / stationarity tests, each delegated to its authoritative
implementation (statsmodels or the ``arch`` package, per the verified library survey), wrapped in one
stable, NaN-safe API that returns a typed result carrying the statistic, the p-value / critical values,
a plain verdict, and the primary reference so the foundation travels with the code.

Tests and where they live (verified 2026-07-04):
  * ADF  - Augmented Dickey-Fuller. H0: unit root (non-stationary). Dickey & Fuller 1979,
           DOI 10.1080/01621459.1979.10482531. ``statsmodels.tsa.stattools.adfuller``.
  * KPSS - H0: (level/trend) stationary -- the OPPOSITE null to ADF. Kwiatkowski, Phillips, Schmidt &
           Shin 1992, DOI 10.1016/0304-4076(92)90104-Y. ``statsmodels.tsa.stattools.kpss``.
  * PP   - Phillips-Perron, nonparametric HAC correction. H0: unit root. Phillips & Perron 1988,
           DOI 10.1093/biomet/75.2.335. ``arch.unitroot.PhillipsPerron`` (statsmodels has no PP).
  * DF-GLS- GLS-detrended, locally most powerful DF. Elliott, Rothenberg & Stock 1996,
           DOI 10.2307/2171846. ``arch.unitroot.DFGLS`` (statsmodels has no DF-GLS).
  * Zivot-Andrews - unit-root test allowing ONE endogenous structural break. Zivot & Andrews 1992,
           DOI 10.1080/07350015.1992.10509904. ``statsmodels.tsa.stattools.zivot_andrews``.

Differencing-order selection follows FPP3 (Hyndman & Athanasopoulos, sec. 9.1): ``ndiffs`` is the
KPSS-sequential rule (difference while KPSS rejects stationarity), and ``nsdiffs`` uses the seasonal
strength measure Fs from an STL decomposition (difference seasonally when Fs >= 0.64). This is the
FPP3-correct procedure; it deliberately does NOT use the ADF+KPSS four-quadrant table (that table is
valid general econometrics and is exposed as an interpretation in ``combined_verdict``, but it is not
what FPP3 prescribes). No pmdarima dependency.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class TestResult:
    """One unit-root / stationarity test outcome.

    ``null`` states the null hypothesis so a p-value is never read backwards (ADF and KPSS have opposite
    nulls). ``stationary`` is the test's verdict at ``alpha`` already translated to the common language
    "is the series stationary?", so callers do not have to remember each test's polarity.
    """

    name: str
    stat: float
    pvalue: float | None
    crit: dict[str, float]
    null: str
    stationary: bool | None
    alpha: float
    reference: str
    extra: dict[str, float] = field(default_factory=dict)


def _clean(x) -> np.ndarray:
    """Coerce to a 1-D float array and drop non-finite points (tests require finite input)."""
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


def adf(x, regression: str = "c", alpha: float = 0.05) -> TestResult:
    """Augmented Dickey-Fuller. Rejecting H0 (small p) => evidence the series IS stationary."""
    from statsmodels.tsa.stattools import adfuller

    a = _clean(x)
    stat, pvalue, _usedlag, _nobs, crit, _icbest = adfuller(a, regression=regression, autolag="AIC")
    return TestResult(
        name="ADF", stat=float(stat), pvalue=float(pvalue),
        crit={k: float(v) for k, v in crit.items()},
        null="unit root (non-stationary)", stationary=bool(pvalue < alpha), alpha=alpha,
        reference="Dickey & Fuller 1979, DOI 10.1080/01621459.1979.10482531",
    )


def kpss(x, regression: str = "c", alpha: float = 0.05) -> TestResult:
    """KPSS. Its null is STATIONARITY, so rejecting H0 (small p) => evidence the series is NON-stationary."""
    from statsmodels.tsa.stattools import kpss as _kpss

    a = _clean(x)
    with warnings.catch_warnings():
        # statsmodels warns when the p-value is clipped at the table edge; that is expected, not an error.
        warnings.simplefilter("ignore")
        stat, pvalue, _lags, crit = _kpss(a, regression=regression, nlags="auto")
    return TestResult(
        name="KPSS", stat=float(stat), pvalue=float(pvalue),
        crit={k: float(v) for k, v in crit.items()},
        null="stationary", stationary=bool(pvalue >= alpha), alpha=alpha,
        reference="Kwiatkowski, Phillips, Schmidt & Shin 1992, DOI 10.1016/0304-4076(92)90104-Y",
    )


def phillips_perron(x, trend: str = "c", alpha: float = 0.05) -> TestResult:
    """Phillips-Perron (arch). Nonparametric HAC correction; H0: unit root. Small p => stationary."""
    from arch.unitroot import PhillipsPerron

    a = _clean(x)
    t = PhillipsPerron(a, trend=trend)
    return TestResult(
        name="PhillipsPerron", stat=float(t.stat), pvalue=float(t.pvalue),
        crit={k: float(v) for k, v in t.critical_values.items()},
        null="unit root (non-stationary)", stationary=bool(t.pvalue < alpha), alpha=alpha,
        reference="Phillips & Perron 1988, DOI 10.1093/biomet/75.2.335",
    )


def dfgls(x, trend: str = "c", alpha: float = 0.05) -> TestResult:
    """DF-GLS (arch). GLS-detrended, locally most powerful DF; H0: unit root. Small p => stationary."""
    from arch.unitroot import DFGLS

    a = _clean(x)
    t = DFGLS(a, trend=trend)
    return TestResult(
        name="DFGLS", stat=float(t.stat), pvalue=float(t.pvalue),
        crit={k: float(v) for k, v in t.critical_values.items()},
        null="unit root (non-stationary)", stationary=bool(t.pvalue < alpha), alpha=alpha,
        reference="Elliott, Rothenberg & Stock 1996, DOI 10.2307/2171846",
    )


def zivot_andrews(x, regression: str = "c", alpha: float = 0.05) -> TestResult:
    """Zivot-Andrews: unit-root test allowing ONE endogenous structural break (reports the break index)."""
    from statsmodels.tsa.stattools import zivot_andrews as _za

    a = _clean(x)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, pvalue, crit, _baselag, bpidx = _za(a, regression=regression)
    return TestResult(
        name="ZivotAndrews", stat=float(stat), pvalue=float(pvalue),
        crit={k: float(v) for k, v in crit.items()},
        null="unit root with no break", stationary=bool(pvalue < alpha), alpha=alpha,
        reference="Zivot & Andrews 1992, DOI 10.1080/07350015.1992.10509904",
        extra={"break_index": float(bpidx)},
    )


def ndiffs(x, alpha: float = 0.05, max_d: int = 2) -> int:
    """Number of first differences to make the series stationary, via the FPP3 KPSS-sequential rule.

    Apply KPSS; while it rejects stationarity (p < alpha) and we are under ``max_d``, difference once
    more and re-test. This is Hyndman & Athanasopoulos FPP3 sec. 9.1 (``unitroot_ndiffs``), not the
    ADF+KPSS four-quadrant heuristic.
    """
    a = _clean(x)
    d = 0
    while d < max_d:
        if len(a) < 8 or np.allclose(a, a[0]):
            break
        try:
            res = kpss(a, regression="c", alpha=alpha)
        except (ValueError, np.linalg.LinAlgError):
            break
        if res.stationary:  # KPSS did not reject stationarity -> stop
            break
        a = np.diff(a)
        d += 1
    return d


def seasonal_strength(x, period: int) -> float:
    """FPP3 seasonal strength Fs = max(0, 1 - Var(remainder)/Var(seasonal+remainder)) from an STL fit.

    Wang, Smith & Hyndman 2006 (DOI 10.1007/s10618-005-0039-x) feature; strength form per FPP3 sec. 4.3.
    Returns 0.0 when the series is too short for two full periods (STL is undefined there).
    """
    from statsmodels.tsa.seasonal import STL

    a = _clean(x)
    if period < 2 or len(a) < 2 * period:
        return 0.0
    res = STL(a, period=period, robust=True).fit()
    var_r = float(np.var(res.resid))
    var_sr = float(np.var(res.seasonal + res.resid))
    if var_sr <= 0:
        return 0.0
    return float(max(0.0, 1.0 - var_r / var_sr))


def nsdiffs(x, period: int, max_D: int = 1, threshold: float = 0.64) -> int:
    """Number of SEASONAL differences via the FPP3 seasonal-strength rule (difference while Fs >= 0.64)."""
    a = _clean(x)
    D = 0
    while D < max_D:
        if len(a) < 2 * period or seasonal_strength(a, period) < threshold:
            break
        a = a[period:] - a[:-period]
        D += 1
    return D


def combined_verdict(adf_res: TestResult, kpss_res: TestResult) -> str:
    """The ADF+KPSS four-quadrant interpretation (general econometrics, not FPP3).

    ADF rejects unit root (stationary) x KPSS rejects stationarity (non-stationary) -> four cases:
      both agree stationary / both agree non-stationary / trend-stationary / difference-stationary.
    """
    adf_stat = adf_res.stationary
    kpss_stat = kpss_res.stationary
    if adf_stat and kpss_stat:
        return "stationary (both tests agree)"
    if not adf_stat and not kpss_stat:
        return "non-stationary (both tests agree)"
    if adf_stat and not kpss_stat:
        return "difference-stationary (ADF stationary, KPSS rejects: likely needs differencing)"
    return "trend-stationary (KPSS stationary, ADF unit root: detrend rather than difference)"


def stationarity_report(x, period: int | None = None, alpha: float = 0.05) -> dict:
    """Run the full stationarity panel and return a JSON-ready report (for the baked artifact + docs).

    Includes ADF, KPSS, Phillips-Perron, DF-GLS, Zivot-Andrews, the four-quadrant combined verdict, and
    the FPP3 differencing recommendation (d via KPSS-sequential; D via seasonal strength when ``period``).
    """
    a = _clean(x)
    adf_res = adf(a, alpha=alpha)
    kpss_res = kpss(a, alpha=alpha)
    tests = [adf_res, kpss_res, phillips_perron(a, alpha=alpha), dfgls(a, alpha=alpha),
             zivot_andrews(a, alpha=alpha)]
    report = {
        "n": int(a.size),
        "tests": [
            {"name": t.name, "stat": t.stat, "pvalue": t.pvalue, "crit": t.crit,
             "null": t.null, "stationary": t.stationary, "reference": t.reference, **t.extra}
            for t in tests
        ],
        "combined_verdict": combined_verdict(adf_res, kpss_res),
        "recommended_d": ndiffs(a, alpha=alpha),
    }
    if period and period >= 2:
        report["seasonal_strength"] = seasonal_strength(a, period)
        report["recommended_D"] = nsdiffs(a, period)
    return report
