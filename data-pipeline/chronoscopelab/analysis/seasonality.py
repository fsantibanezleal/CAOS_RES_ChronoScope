"""Seasonality analysis: periodogram/Welch dominant period, seasonal strength, MSTL, seasonal subseries.

Seasonality is a pattern repeating at a fixed period m (a day, a week, a year). This module answers the four
questions a forecaster asks before choosing a seasonal model: (1) is there a dominant period at all, and what
is it? (2) how strong is the seasonality (and is it worth modelling)? (3) are there MULTIPLE seasonal periods
(e.g. daily + weekly)? (4) what does the per-phase seasonal profile look like? Each answer is delegated to
its authoritative implementation and wrapped in one stable, NaN-safe API that carries the primary reference.

Methods / references (verified 2026-07-04):
  * Periodogram (Schuster 1898) / Welch (1967) - the squared magnitude of the FFT; the tallest non-DC peak
    gives the dominant period. ``scipy.signal.periodogram`` / ``scipy.signal.welch``.
  * Seasonal strength Fs = max(0, 1 - Var(R)/Var(S+R)) from an STL decomposition - Wang, Smith & Hyndman
    2006, DOI 10.1007/s10618-005-0039-x; strength form per FPP3 sec. 4.3 (the F_S >= 0.64 threshold drives
    ``nsdiffs``). Re-implemented here so seasonality does not import stationarity.
  * MSTL - multiple-seasonal STL. Bandara, Hyndman & Bergmeir 2021, arXiv:2107.13462. ``statsmodels.MSTL``.
  * Seasonal subseries - the per-phase means + the per-phase series; the standard "month plot" (Cleveland &
    Terpenning 1982, JASA 77(377), DOI 10.1080/01621459.1982.10477766).

NOTE: ``scipy.signal.cwt`` is DEPRECATED (1.12) and REMOVED (1.15); wavelet/scalogram seasonality uses
PyWavelets elsewhere. Here we stay on FFT-based spectral estimation, which scipy keeps.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class Spectrum:
    """A spectral density estimate (periodogram or Welch) over positive frequencies, with the dominant peak."""

    name: str
    freqs: np.ndarray
    power: np.ndarray
    dominant_period: float | None
    dominant_power: float
    reference: str


def periodogram(x, fs: float = 1.0) -> Spectrum:
    """Schuster periodogram; the dominant period is 1 / (the tallest non-DC frequency)."""
    from scipy.signal import periodogram as _periodogram

    a = _clean(x)
    f, pxx = _periodogram(a, fs=fs)
    if len(f) > 1:
        idx = 1 + int(np.argmax(pxx[1:]))   # skip the DC (zero-frequency) bin
        dom_freq = float(f[idx])
        dom_power = float(pxx[idx])
        dom_period = (1.0 / dom_freq) if dom_freq > 0 else None
    else:
        dom_period, dom_power = None, 0.0
    return Spectrum(
        name="Periodogram", freqs=f, power=pxx, dominant_period=dom_period, dominant_power=dom_power,
        reference="Schuster 1898, Terrestrial Magnetism 3(1):13-41; scipy.signal.periodogram",
    )


def welch(x, fs: float = 1.0, nperseg: int | None = None) -> Spectrum:
    """Welch's averaged periodogram (lower variance, coarser resolution) and its dominant period."""
    from scipy.signal import welch as _welch

    a = _clean(x)
    nperseg = min(nperseg or 256, len(a))
    f, pxx = _welch(a, fs=fs, nperseg=nperseg)
    if len(f) > 1:
        idx = 1 + int(np.argmax(pxx[1:]))
        dom_freq = float(f[idx])
        dom_power = float(pxx[idx])
        dom_period = (1.0 / dom_freq) if dom_freq > 0 else None
    else:
        dom_period, dom_power = None, 0.0
    return Spectrum(
        name="Welch", freqs=f, power=pxx, dominant_period=dom_period, dominant_power=dom_power,
        reference="Welch 1967, IEEE Trans. Audio Electroacoust. 15(2):70-73, DOI 10.1109/TAU.1967.1161901",
    )


def seasonal_strength(x, period: int) -> float:
    """F_S = max(0, 1 - Var(remainder)/Var(seasonal+remainder)) from a robust STL fit. 0 if too short."""
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


@dataclass(frozen=True)
class Decomp:
    """An additive decomposition into trend + seasonal + remainder, with the trend/seasonal strength scores."""

    trend: np.ndarray
    seasonal: np.ndarray
    remainder: np.ndarray
    strength_trend: float
    strength_seasonal: float
    periods: tuple[int, ...]
    reference: str


def _strengths(trend, seasonal, remainder) -> tuple[float, float]:
    var_r = float(np.var(remainder)) or 1e-12
    var_tr = float(np.var(trend + remainder)) or 1e-12
    var_sr = float(np.var(seasonal + remainder)) or 1e-12
    f_t = max(0.0, 1.0 - var_r / var_tr)
    f_s = max(0.0, 1.0 - var_r / var_sr)
    return f_t, f_s


def stl_decompose(x, period: int) -> Decomp:
    """STL (Cleveland et al. 1990) additive decomposition at a single ``period``."""
    from statsmodels.tsa.seasonal import STL

    a = _clean(x)
    if period < 2 or len(a) < 2 * period:
        raise ValueError(f"STL needs len >= 2*period; got len={len(a)}, period={period}")
    res = STL(a, period=period, robust=True).fit()
    f_t, f_s = _strengths(res.trend, res.seasonal, res.resid)
    return Decomp(
        trend=np.asarray(res.trend, dtype=float), seasonal=np.asarray(res.seasonal, dtype=float),
        remainder=np.asarray(res.resid, dtype=float), strength_trend=f_t, strength_seasonal=f_s,
        periods=(int(period),),
        reference="Cleveland, Cleveland, McRae & Terpenning 1990, J. Official Statistics 6(1):3-73 (STL)",
    )


def mstl_decompose(x, periods: list[int]) -> Decomp:
    """MSTL: multiple-seasonal STL (daily + weekly + ...) additive decomposition."""
    from statsmodels.tsa.seasonal import MSTL

    a = _clean(x)
    periods = [int(p) for p in periods if int(p) >= 2]
    if not periods:
        raise ValueError("MSTL needs at least one period >= 2")
    if len(a) < 2 * max(periods):
        raise ValueError(f"MSTL needs len >= 2*max(periods); got len={len(a)}, max period={max(periods)}")
    res = MSTL(a, periods=periods).fit()
    seasonal_2d = np.asarray(res.seasonal, dtype=float)
    # MSTL returns one seasonal column per period; sum them into a single additive seasonal component.
    seasonal = seasonal_2d.sum(axis=1) if seasonal_2d.ndim == 2 else seasonal_2d
    trend = np.asarray(res.trend, dtype=float)
    remainder = np.asarray(res.resid, dtype=float)
    f_t, f_s = _strengths(trend, seasonal, remainder)
    return Decomp(
        trend=trend, seasonal=seasonal, remainder=remainder, strength_trend=f_t, strength_seasonal=f_s,
        periods=tuple(periods),
        reference="Bandara, Hyndman & Bergmeir 2021, MSTL, arXiv:2107.13462; statsmodels.tsa.seasonal.MSTL",
    )


@dataclass(frozen=True)
class SeasonalSubseries:
    """The per-phase (per-season) means + the per-phase series, for the standard month/subseries plot."""

    period: int
    means: np.ndarray            # length = period: the mean of each phase
    profiles: list[np.ndarray]   # one array per phase, each the values that landed in that phase


def seasonal_subseries(x, period: int) -> SeasonalSubseries:
    """Split the series into cycles of length ``period``; return the per-phase mean and per-phase values."""
    a = _clean(x)
    if period < 2:
        raise ValueError("period must be >= 2")
    n_full = (len(a) // period) * period
    if n_full == 0:
        raise ValueError("series shorter than one period")
    trimmed = a[:n_full]
    cycles = trimmed.reshape(-1, period)             # rows = cycles, cols = phases
    means = cycles.mean(axis=0)
    profiles = [cycles[:, j] for j in range(period)]
    return SeasonalSubseries(period=int(period), means=means, profiles=profiles)


def seasonality_report(x, fs: float = 1.0, candidate_periods: list[int] | None = None) -> dict:
    """Run the full seasonality panel: periodogram + Welch + per-candidate strength + (optional) MSTL."""
    a = _clean(x)
    pg = periodogram(a, fs=fs)
    wl = welch(a, fs=fs)
    candidates = candidate_periods or []
    strengths = {int(p): float(seasonal_strength(a, int(p))) for p in candidates if int(p) >= 2}
    out = {
        "n": int(len(a)),
        "periodogram": {
            "dominant_period": pg.dominant_period, "dominant_power": pg.dominant_power,
            "freqs": pg.freqs.tolist(), "power": pg.power.tolist(), "reference": pg.reference,
        },
        "welch": {
            "dominant_period": wl.dominant_period, "dominant_power": wl.dominant_power,
            "reference": wl.reference,
        },
        "seasonal_strength_by_candidate_period": strengths,
    }
    # If the periodogram found a dominant period, also report STL strength at that period.
    if pg.dominant_period is not None and pg.dominant_period >= 2:
        p_int = int(round(pg.dominant_period))
        if p_int >= 2 and len(a) >= 2 * p_int:
            out["stl_at_dominant"] = _decomp_dict(stl_decompose(a, p_int))
    return out


def _decomp_dict(d: Decomp) -> dict:
    return {
        "strength_trend": d.strength_trend, "strength_seasonal": d.strength_seasonal,
        "periods": list(d.periods), "reference": d.reference,
    }
