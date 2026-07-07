"""Stage 2b - analyze: run the analysis toolkit on a case's series and bake a compact analysis artifact.

This is the "understand the series" half of CONTRACT 2 (the forecast trace is the other half). For each case
it runs the applicable diagnostics from ``chronoscopelab.analysis`` (stationarity, autocorrelation,
seasonality, filters, change-points, volatility, distribution/complexity, fractal; the heavy nonlinear panel
only when the series is long enough), producing one JSON-ready dict the web "Understand" workbench renders.
The browser recomputes a live subset of these to match the baked numbers (parity), so the same code path
answers "is this stationary / seasonal / bursty / long-memory?" offline and live.

Guardrails: every panel is wrapped so a degenerate case records an honest ``{"error": ...}`` instead of
crashing the whole bake; the heavy panels (nonlinear surrogate loop, MF-DFA, recurrence) are gated by series
length so precompute stays tractable. Nothing here is decimated beyond what each report already returns.
"""
from __future__ import annotations

from typing import Any, Callable

from ..analysis import (
    autocorrelation,
    causality,
    changepoints,
    distribution,
    fractal,
    filters,
    nonlinear,
    seasonality,
    stationarity,
    volatility,
)

# Series-length gates: heavy panels need enough points to be meaningful (and to stay tractable offline).
MIN_FOR_NONLINEAR = 400
MIN_FOR_MFDFA = 200
STRONG_SEASONAL_FS = 0.64  # FPP3 threshold: above this, deseasonalize before change-point detection


def _safe(name: str, fn: Callable[[], dict]) -> dict:
    """Run one panel, converting any failure into a recorded error (the bake must never die on a bad case)."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - honesty: record the failure in the artifact, do not crash
        return {"error": f"{type(exc).__name__}: {exc}"}


def _changepoints_series(y: list, m: int) -> tuple[list, bool]:
    """For a strongly-seasonal series, deseasonalize before change-point detection.

    PELT with an l2 (mean-shift) cost flags every seasonal peak and trough as a break, so on raw seasonal
    data it reports dozens of spurious change points. When seasonality is strong we subtract the STL seasonal
    component so change-point detection finds GENUINE regime shifts (trend/level breaks), not the seasonal
    oscillation. Returns (series_to_use, was_deseasonalized).
    """
    if m >= 2 and len(y) >= 2 * m:
        try:
            if seasonality.seasonal_strength(y, m) >= STRONG_SEASONAL_FS:
                d = seasonality.stl_decompose(y, m)
                # trend + remainder = the series with the seasonal wave removed
                return (list(d.trend + d.remainder), True)
        except Exception:  # noqa: BLE001 - fall back to the raw series if STL fails
            pass
    return (y, False)


def run(spec: Any) -> dict:
    """Run the analysis panel for one case's series and return the JSON-ready ``analysis`` dict.

    ``spec`` is a SeriesSpec (``.y`` the series, ``.seasonality`` the period, ``.case_id``). The seasonality
    knob is passed as a candidate period so seasonal strength / Guerrero lambda use the case's known period.
    """
    y = list(spec.y)
    m = int(getattr(spec, "seasonality", 0) or 0)
    n = len(y)
    candidates = sorted({p for p in (m, 2 * m) if p >= 2})

    analysis: dict[str, dict] = {
        "n": n,
        "seasonality_period": m,
        "stationarity": _safe("stationarity", lambda: stationarity.stationarity_report(y, period=m or None)),
        "autocorrelation": _safe("autocorrelation", lambda: autocorrelation.autocorrelation_report(y)),
        "seasonality": _safe("seasonality", lambda: seasonality.seasonality_report(y, candidate_periods=candidates)),
        "filters": _safe("filters", lambda: filters.filters_report(y)),
        "changepoints": _safe("changepoints", lambda: _changepoints_report(y, m)),
        "volatility": _safe("volatility", lambda: volatility.volatility_report(y, season_length=m or None)),
        "distribution": _safe("distribution", lambda: distribution.distribution_report(y)),
        "fractal": _safe("fractal", lambda: fractal.fractal_report(y)),
    }

    # Heavy nonlinear panel only for long enough series (the surrogate loop is O(n^2) x surrogates).
    if n >= MIN_FOR_NONLINEAR:
        analysis["nonlinear"] = _safe("nonlinear", lambda: nonlinear.nonlinear_report(y, n_surrogates=9))
    else:
        analysis["nonlinear"] = {"skipped": f"series too short (n={n} < {MIN_FOR_NONLINEAR}) for the chaos panel"}

    # Causality is bivariate: only run it when the case carries a covariate/second series.
    covar = getattr(spec, "covariate", None)
    if covar is not None and len(covar) >= 2:
        analysis["causality"] = _safe("causality", lambda: causality.causality_report(y, list(covar)))
    else:
        analysis["causality"] = {"skipped": "univariate case (no covariate series to relate)"}

    return analysis


def _changepoints_report(y: list, m: int) -> dict:
    """Change-point report on the deseasonalized series when seasonality is strong (records which was used)."""
    series, deseasonalized = _changepoints_series(y, m)
    rep = changepoints.changepoints_report(series)
    rep["deseasonalized"] = deseasonalized
    rep["note"] = ("change points detected on the STL-deseasonalized series (strong seasonality would "
                   "otherwise flag every peak/trough)" if deseasonalized
                   else "change points detected on the raw series")
    return rep
