"""Engine-integration tests: the classical ladder is always present; the statistical engines are included
when statsforecast is installed and produce valid monotone quantiles. The suite stays green without the
heavy dependency (graceful degradation)."""
import importlib.util

import numpy as np
import pytest

from chronoscopelab.methods import all_forecasters
from chronoscopelab.model.forecasters import classical_forecasters

HAS_STATSFORECAST = importlib.util.find_spec("statsforecast") is not None
HAS_LIGHTGBM = (
    importlib.util.find_spec("lightgbm") is not None
    and importlib.util.find_spec("mlforecast") is not None
)


def test_classical_ladder_always_present():
    names = {fc.name for fc in classical_forecasters()}
    assert {"SeasonalNaive", "SES", "Holt", "HoltWinters", "Theta"} <= names


def test_all_forecasters_superset_of_classical():
    all_names = {fc.name for fc in all_forecasters()}
    classical_names = {fc.name for fc in classical_forecasters()}
    assert classical_names <= all_names


@pytest.mark.skipif(not HAS_STATSFORECAST, reason="statsforecast not installed")
def test_statistical_engines_forecast_valid_quantiles():
    names = {fc.name for fc in all_forecasters()}
    assert {"AutoETS", "AutoTheta", "AutoARIMA"} <= names

    from chronoscopelab.engines import heavy_forecasters

    rng = np.random.default_rng(0)
    y = 50 + 10 * np.sin(np.arange(120) * 2 * np.pi / 12) + rng.normal(0, 2.0, 120)
    for fc in heavy_forecasters():
        q = fc.quantiles(y, 12, 6, (0.1, 0.5, 0.9))
        assert q.shape == (6, 3), fc.name
        assert np.all(np.isfinite(q)), fc.name
        assert np.all(np.diff(q, axis=1) >= -1e-6), fc.name  # monotone across levels


@pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm/mlforecast not installed")
def test_lightgbm_ml_engine_forecasts():
    names = {fc.name for fc in all_forecasters()}
    assert "LightGBM" in names
    from chronoscopelab.engines.lightgbm_engine import LightGBMForecaster

    rng = np.random.default_rng(1)
    y = 50 + 10 * np.sin(np.arange(180) * 2 * np.pi / 12) + 0.2 * np.arange(180) + rng.normal(0, 2.0, 180)
    q = LightGBMForecaster().quantiles(y, 12, 12, (0.1, 0.5, 0.9))
    assert q.shape == (12, 3)
    assert np.all(np.isfinite(q))
    assert np.all(np.diff(q, axis=1) >= -1e-6)
