"""Classical forecasting core: real, pure-numpy methods (Pyodide-safe live lane).

Each method fits on a history and returns a point path plus a one-step in-sample residual sigma; the
shared ``build_forecast`` turns that into a point + outer prediction interval at the requested quantile
levels (Gaussian widening by sqrt(step), documented as an iid-error approximation). These are genuine
implementations (state-space exponential smoothing, the Theta method as SES-with-drift), not toys, and
they are the same code path the offline pipeline and the browser live lane use.

Methods: seasonal naive, SES, Holt (additive trend), Holt-Winters (additive trend + seasonality),
Theta. Heavier engines (statsforecast/neuralforecast, LightGBM, and the zero-shot foundation models)
are wired in later slices behind the same MethodForecast contract.
"""
from __future__ import annotations

import math
from typing import Callable

import numpy as np

from ..io.schema import MethodForecast

# --- normal quantile (Acklam's rational approximation; abs error < 1.15e-9) --------------------------
_A = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
      1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
_B = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
      6.680131188771972e01, -1.328068155288572e01]
_C = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
      -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
_D = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]


def normal_ppf(p: float) -> float:
    """Inverse standard-normal CDF (probit) via Acklam's approximation."""
    if p <= 0.0:
        return -math.inf
    if p >= 1.0:
        return math.inf
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
               ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
               ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q / \
           (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1)


def _clean(y: np.ndarray) -> np.ndarray:
    """Fill NaN by forward-fill then back-fill so recursive methods stay defined."""
    y = np.asarray(y, dtype=float).copy()
    if np.isnan(y).any():
        idx = np.where(~np.isnan(y))[0]
        if idx.size == 0:
            return np.zeros_like(y)
        y[: idx[0]] = y[idx[0]]
        last = y[idx[0]]
        for i in range(len(y)):
            if np.isnan(y[i]):
                y[i] = last
            else:
                last = y[i]
    return y


# --- individual methods: each returns (point_path (h,), one_step_sigma) -----------------------------
def seasonal_naive(y: np.ndarray, m: int, h: int) -> tuple[np.ndarray, float]:
    y = _clean(y)
    m = m if (m >= 1 and y.shape[0] > m) else 1
    season = y[-m:]
    point = np.tile(season, int(np.ceil(h / m)))[:h]
    resid = y[m:] - y[:-m]
    sigma = float(np.std(resid)) if resid.size else 0.0
    return point, sigma


def _ses_run(y: np.ndarray, alpha: float) -> tuple[np.ndarray, float]:
    """Return in-sample one-step fitted values and the final level for SES."""
    level = y[0]
    fitted = np.empty_like(y)
    fitted[0] = level
    for t in range(1, y.shape[0]):
        fitted[t] = level
        level = alpha * y[t] + (1 - alpha) * level
    return fitted, level


def _opt_alpha(y: np.ndarray) -> float:
    grid = np.linspace(0.05, 0.95, 19)
    best_a, best_sse = grid[0], math.inf
    for a in grid:
        fitted, _ = _ses_run(y, a)
        sse = float(np.sum((y[1:] - fitted[1:]) ** 2))
        if sse < best_sse:
            best_sse, best_a = sse, a
    return float(best_a)


def ses(y: np.ndarray, m: int, h: int) -> tuple[np.ndarray, float]:
    y = _clean(y)
    a = _opt_alpha(y)
    fitted, level = _ses_run(y, a)
    sigma = float(np.std(y[1:] - fitted[1:])) if y.shape[0] > 1 else 0.0
    return np.full(h, level), sigma


def _holt_run(y: np.ndarray, alpha: float, beta: float) -> tuple[np.ndarray, float, float]:
    level, trend = y[0], (y[1] - y[0] if y.shape[0] > 1 else 0.0)
    fitted = np.empty_like(y)
    fitted[0] = level
    for t in range(1, y.shape[0]):
        fitted[t] = level + trend
        prev_level = level
        level = alpha * y[t] + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return fitted, level, trend


def holt(y: np.ndarray, m: int, h: int) -> tuple[np.ndarray, float]:
    y = _clean(y)
    best = (0.3, 0.1)
    best_sse = math.inf
    for a in np.linspace(0.1, 0.9, 9):
        for b in np.linspace(0.05, 0.5, 6):
            fitted, _, _ = _holt_run(y, a, b)
            sse = float(np.sum((y[1:] - fitted[1:]) ** 2))
            if sse < best_sse:
                best_sse, best = sse, (a, b)
    fitted, level, trend = _holt_run(y, *best)
    sigma = float(np.std(y[1:] - fitted[1:])) if y.shape[0] > 1 else 0.0
    point = level + trend * np.arange(1, h + 1)
    return point, sigma


def _hw_run(y: np.ndarray, m: int, alpha: float, beta: float, gamma: float):
    level = float(np.mean(y[:m]))
    trend = float((np.mean(y[m:2 * m]) - np.mean(y[:m])) / m) if y.shape[0] >= 2 * m else 0.0
    season = [float(y[i] - level) for i in range(m)]
    fitted = np.empty_like(y)
    for t in range(y.shape[0]):
        s = season[t % m]
        fitted[t] = level + trend + s
        prev_level = level
        level = alpha * (y[t] - s) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        season[t % m] = gamma * (y[t] - level) + (1 - gamma) * s
    return fitted, level, trend, season


def holt_winters(y: np.ndarray, m: int, h: int) -> tuple[np.ndarray, float]:
    y = _clean(y)
    if m < 2 or y.shape[0] < 2 * m:
        return holt(y, m, h)  # not enough seasons -> fall back to trend model
    best, best_sse = (0.3, 0.1, 0.1), math.inf
    for a in (0.1, 0.3, 0.5, 0.8):
        for b in (0.05, 0.2):
            for g in (0.1, 0.3, 0.6):
                fitted, *_ = _hw_run(y, m, a, b, g)
                sse = float(np.sum((y[m:] - fitted[m:]) ** 2))
                if sse < best_sse:
                    best_sse, best = sse, (a, b, g)
    fitted, level, trend, season = _hw_run(y, m, *best)
    sigma = float(np.std(y[m:] - fitted[m:])) if y.shape[0] > m else 0.0
    point = np.array([level + trend * (k + 1) + season[k % m] for k in range(h)])
    return point, sigma


def theta(y: np.ndarray, m: int, h: int) -> tuple[np.ndarray, float]:
    """Classic Theta method as SES with half the OLS drift (Hyndman and Billah, 2003)."""
    y = _clean(y)
    n = y.shape[0]
    t = np.arange(n, dtype=float)
    b = float(np.polyfit(t, y, 1)[0]) if n >= 2 else 0.0
    a = _opt_alpha(y)
    fitted, level = _ses_run(y, a)
    sigma = float(np.std(y[1:] - fitted[1:])) if n > 1 else 0.0
    point = level + 0.5 * b * np.arange(1, h + 1)
    return point, sigma


METHODS: list[tuple[str, str, Callable[[np.ndarray, int, int], tuple[np.ndarray, float]]]] = [
    ("SeasonalNaive", "classical", seasonal_naive),
    ("SES", "classical", ses),
    ("Holt", "classical", holt),
    ("HoltWinters", "classical", holt_winters),
    ("Theta", "classical", theta),
]

METHOD_FNS = {name: fn for name, _fam, fn in METHODS}


def build_forecast(name: str, family: str, point: np.ndarray, sigma: float,
                   levels: tuple[float, ...]) -> MethodForecast:
    """Turn a point path + one-step sigma into a MethodForecast with an outer interval."""
    steps = np.arange(1, point.shape[0] + 1)
    z_lo = normal_ppf(min(levels))
    z_hi = normal_ppf(max(levels))
    widen = np.sqrt(steps)
    lower = point + z_lo * sigma * widen
    upper = point + z_hi * sigma * widen
    return MethodForecast(
        name=name, family=family,
        point=tuple(round(float(v), 6) for v in point),
        lower=tuple(round(float(v), 6) for v in lower),
        upper=tuple(round(float(v), 6) for v in upper),
    )


def forecast_all(y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> list[MethodForecast]:
    """Fit and forecast every method; returns one MethodForecast each."""
    out = []
    for name, family, fn in METHODS:
        point, sigma = fn(np.asarray(y, dtype=float), m, h)
        out.append(build_forecast(name, family, point, sigma, levels))
    return out


def forecast_point(name: str, y: np.ndarray, m: int, h: int) -> np.ndarray:
    """Just the point path for one method (used by the backtest/evaluate stage)."""
    point, _sigma = METHOD_FNS[name](np.asarray(y, dtype=float), m, h)
    return point
