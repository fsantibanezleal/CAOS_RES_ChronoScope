"""Changing observable units must not change fitted normalized comparisons."""
import importlib.util
import csv
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from engine.io.contract import _mad_zscores
from engine.reevaluation import metrics
from engine.stages.streaming import _ridge_batch
from engine.core.trace import build_trace
from engine.data import loaders
from engine.engines.neural_engine import NeuralForecaster
from engine.io.schema import Covariate, ForecastResult, MethodForecast, SeriesSpec
from engine.stages import streaming
from engine.stages.feature_extraction import _seasonal_strength


@pytest.mark.parametrize("level", [0.1, 1e-14, 1e12])
@pytest.mark.parametrize("cycles", [2, 5, 10])
def test_adversarial_constant_complete_cycles_ignore_incomplete_tail(level, cycles):
    values = np.r_[np.full(12 * cycles, level), 2 * level]
    assert _seasonal_strength(values, 12) == 0.0


@pytest.mark.parametrize("factor,offset", [(1e-18, 0), (1e12, -4e12), (2, 17)])
def test_adversarial_tiny_units_do_not_erase_scaled_forecast_metrics(factor, offset):
    history = np.array([4, 7, 5, 9, 8], dtype=float)
    actual, point, lower, upper = [np.array(v, dtype=float) for v in ([7, 11], [8, 10], [6, 9], [10, 12])]
    expected = metrics(history, actual, point, lower, upper, 1)
    actual_scores = metrics(*(factor * v + offset for v in (history, actual, point, lower, upper)), 1)
    for name in ("mase", "msis", "coverage"):
        assert actual_scores[name] == pytest.approx(expected[name])


@pytest.mark.parametrize("use_cov", [False, True])
def test_adversarial_ridge_penalty_is_independent_of_response_and_covariate_units(use_cov):
    t = np.arange(120)
    cov = (np.sin(t / 7) + (t % 9 == 0)).reshape(-1, 1)
    y = 10 + 0.03 * t + np.sin(t / 3) + 2 * cov[:, 0]
    future = np.array([[0.2], [1.1], [-0.3]])
    predictor = _ridge_batch(12, use_cov=use_cov)
    expected = predictor(y, 3, cov, future, (0.1, 0.5, 0.9))
    for factor, offset in [(1e-18, 0), (1e12, -4e12), (2, 17)]:
        scaled = predictor(y * factor + offset, 3, cov * 7e-16 + 2e-16,
                           future * 7e-16 + 2e-16, (0.1, 0.5, 0.9))
        np.testing.assert_allclose((scaled - offset) / factor, expected, rtol=1e-12, atol=1e-12)
    np.testing.assert_array_equal(predictor(np.ones(80) * 1e-18, 3, cov, future, (0.1, 0.5, 0.9)),
                                  np.ones((3, 3)) * 1e-18)


def test_adversarial_sparse_outlier_detection_does_not_invent_a_measured_mad():
    values = [1, 1, 1, 1, 3]
    assert _mad_zscores(values) == _mad_zscores([v * 1e-18 for v in values])
    assert _mad_zscores(values) == [0, 0, 0, 0, float("inf")]


@pytest.mark.parametrize("level", [0.1, 1e-14, 1e12])
def test_adversarial_constant_covariate_cannot_acquire_a_future_effect(level):
    y = np.sin(np.arange(120) / 3) + np.arange(120) / 100
    past = np.full((120, 1), level)
    predictor = _ridge_batch(12, use_cov=True)
    unchanged = predictor(y, 3, past, np.full((3, 1), level), (0.1, 0.5, 0.9))
    changed = predictor(y, 3, past, np.full((3, 1), 9 * level), (0.1, 0.5, 0.9))
    blind = _ridge_batch(12, use_cov=False)(y, 3, None, None, (0.1, 0.5, 0.9))
    np.testing.assert_array_equal(changed, unchanged)
    np.testing.assert_allclose(changed, blind, rtol=1e-13, atol=1e-13)


@pytest.mark.parametrize("level", [1, 0.1, 1e-14, 1e12])
def test_adversarial_constant_training_prefix_has_no_arbitrary_normalization_unit(level):
    pytest.importorskip("onnx")
    path = Path(__file__).resolve().parents[1] / "scripts/train_nlinear_onnx.py"
    spec = importlib.util.spec_from_file_location("linear_training", path)
    training = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(training)
    inputs, targets = training._windows(np.full(100, level))
    assert inputs.shape == (0, training.L) and targets.shape == (0, training.H)
    y = np.sin(np.arange(100) / 4)
    expected = training._windows(y)
    scaled = training._windows(y * 1e-18)
    for actual, reference in zip(scaled, expected, strict=True):
        np.testing.assert_allclose(actual, reference, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("level", [0.1, 1e-14, 1e12])
def test_adversarial_exact_constant_forecasts_do_not_require_floating_zero_variance(level):
    y = np.full(60, level)
    assert np.ptp(y) == 0
    levels = (0.1, 0.5, 0.9)
    model = NeuralForecaster("NLinear")
    np.testing.assert_array_equal(model.quantiles(y, 12, 3, levels), np.full((3, 3), level))
    np.testing.assert_array_equal(_ridge_batch(12, use_cov=False)(y, 3, None, None, levels), np.full((3, 3), level))


def test_adversarial_m4_selection_rejects_exact_constants_and_preserves_tiny_seasonality(monkeypatch):
    n = 60
    varying = 1e-18 * (2 + np.sin(np.arange(n) * 2 * np.pi / 12))
    rows = [{"id": "constant", "target": np.full(n, 0.1), "timestamp": list(range(n))},
            {"id": "varying", "target": varying, "timestamp": list(range(n))}]
    monkeypatch.setitem(sys.modules, "datasets", SimpleNamespace(Dataset=SimpleNamespace(from_file=lambda _: rows)))
    monkeypatch.setattr(loaders.glob, "glob", lambda *a, **kw: ["cache.arrow"])
    identity, _, actual = loaders._load_m4_config("test", n, 12)
    assert identity == "varying" and actual == varying.tolist()


def test_adversarial_source_csv_and_trace_preserve_observable_precision(tmp_path):
    values = [1e-18, 1.2345678901234567e-18, -7e-19]
    source = tmp_path / "sample.csv"
    loaders._write_long_csv(source, "tiny", ["a", "b", "c"], values)
    with source.open(newline="") as stream:
        assert [float(row["y"]) for row in csv.DictReader(stream)] == values
    method = MethodForecast("level", "probe", tuple(values), tuple(values), tuple(values))
    result = ForecastResult("tiny", 3, 1, (0.1, 0.5, 0.9), tuple(values), (method,))
    trace = build_trace(result, values, {})
    assert trace["history"] == trace["actual"] == trace["methods"][0]["point"] == values


def test_adversarial_streaming_artifact_preserves_covariate_values(monkeypatch):
    values = tuple(1e-18 * (1 + np.arange(60)))
    spec = SeriesSpec("tiny", tuple(np.sin(np.arange(60)) + 10), 1, 1,
                      covariates=(Covariate("scheduled", values),))
    # Exercise serialization independently of the six separately tested models.
    monkeypatch.setattr(streaming, "run_prequential", lambda *a, **kw: (_ for _ in ()).throw(ValueError("test")))
    assert streaming.run(spec)["covariate"]["values"] == list(values)


@pytest.mark.parametrize("level", [0.1, 1e-14, 1e12])
def test_adversarial_fractional_constant_browser_prefix_is_unavailable(level):
    from evaluate_browser_linear import normalize_window
    from confirm_browser_calibration import roughness_bin
    from engine.stages.feature_extraction import run as features

    with pytest.raises(ValueError, match="scale"):
        normalize_window(np.full(48, level), np.full(12, level))
    with pytest.raises(ValueError, match="variance"):
        roughness_bin(np.full((1, 48), level))
    actual = features(SeriesSpec("constant", tuple(np.full(60, level)), 12, 3))
    assert actual.mean == level
    assert actual.std == actual.trend_slope == actual.seasonal_strength == actual.acf1 == 0
