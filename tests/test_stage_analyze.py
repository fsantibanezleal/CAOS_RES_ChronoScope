"""analyze stage tests: the per-case analysis panel bakes the expected shape + honest gating, end to end."""
import numpy as np
import pytest

from chronoscopelab import registry
from chronoscopelab.stages import analyze


def test_analyze_runs_all_panels_on_a_seasonal_case():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    a = analyze.run(spec)
    for panel in ("stationarity", "autocorrelation", "seasonality", "filters", "changepoints",
                  "volatility", "distribution", "fractal", "nonlinear", "causality"):
        assert panel in a
    assert a["n"] == len(spec.y)
    assert a["seasonality_period"] == spec.seasonality


def test_seasonal_case_recovers_its_period():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    a = analyze.run(spec)
    # a strong daily-seasonal hourly case -> dominant period near 24, high seasonal strength
    assert abs(a["seasonality"]["periodogram"]["dominant_period"] - 24.0) < 2.0
    # in-memory the candidate-period keys are ints (JSON coerces them to strings on write)
    assert a["seasonality"]["seasonal_strength_by_candidate_period"][24] > 0.8


def test_changepoints_deseasonalized_when_seasonality_strong():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    a = analyze.run(spec)
    cp = a["changepoints"]
    assert cp["deseasonalized"] is True                   # strong seasonality -> deseasonalize first
    # on a clean deseasonalized seasonal series there is no genuine regime shift
    assert len(cp["pelt"]["breakpoints"]) <= 2


def test_univariate_case_skips_causality():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    a = analyze.run(spec)
    assert "skipped" in a["causality"]                    # no covariate -> honestly skipped, not faked


def test_short_series_skips_nonlinear_panel():
    class _Spec:
        y = tuple(np.sin(np.arange(120) * 2 * np.pi / 12))
        seasonality = 12
        case_id = "SHORT"
    a = analyze.run(_Spec())
    assert "skipped" in a["nonlinear"]                     # n=120 < 400 -> the chaos panel is skipped


def test_every_panel_records_error_not_crash_on_degenerate_input():
    class _Spec:
        y = tuple([5.0] * 60)                              # constant series: many diagnostics are undefined
        seasonality = 0
        case_id = "CONST"
    a = analyze.run(_Spec())                               # must not raise
    # each panel is present and is either a real report or an honest error/skip marker
    for panel in ("stationarity", "autocorrelation", "seasonality", "filters", "distribution", "fractal"):
        assert isinstance(a[panel], dict)


@pytest.mark.parametrize("case_id", ["SEAS_hourly", "TRND_seasonal", "RWLK_noise", "CTRL_white_noise"])
def test_analyze_never_crashes_across_case_regimes(case_id):
    spec = registry.build_series(registry.get_case(case_id), seed=42)
    a = analyze.run(spec)                                  # every regime bakes without raising
    assert a["n"] == len(spec.y)
