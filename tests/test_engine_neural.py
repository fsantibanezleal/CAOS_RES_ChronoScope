"""Deep-engine tests: the real NLinear/DLinear/NHITS architectures train and forecast (GPU-gated).

Skipped when torch is not installed (CI), so the fast test path stays on the classical + statistical ladder.
When torch is present the models train on a small seasonal series and must produce monotone quantiles of the
right shape that beat a trivial baseline - proving the architectures are real, not toys.
"""
import numpy as np
import pytest

torch = pytest.importorskip("torch")  # skip the whole module when the deep dep is absent

from chronoscopelab.engines.neural_engine import (  # noqa: E402 - after the torch skip-guard by design
    NeuralForecaster,
    neural_available,
    neural_forecasters,
)


def _seasonal(n=400, m=24, seed=0):
    t = np.arange(n)
    return 100 + 20 * np.sin(2 * np.pi * t / m) + np.random.default_rng(seed).normal(0, 3, n)


@pytest.mark.parametrize("name", ["NLinear", "DLinear", "NHITS"])
def test_deep_model_produces_monotone_quantiles(name):
    y = _seasonal()
    fc = NeuralForecaster(name, max_steps=150)
    q = fc.quantiles(y[:-24], m=24, h=24, levels=(0.1, 0.5, 0.9))
    assert q.shape == (24, 3)
    assert np.all(q[:, 0] <= q[:, 1] + 1e-6)          # quantiles monotone across levels
    assert np.all(q[:, 1] <= q[:, 2] + 1e-6)


@pytest.mark.parametrize("name", ["NLinear", "NHITS"])
def test_deep_model_forecasts_a_seasonal_series(name):
    y = _seasonal()
    fc = NeuralForecaster(name, max_steps=250)
    q = fc.quantiles(y[:-24], m=24, h=24, levels=(0.1, 0.5, 0.9))
    median = q[:, 1]
    # the model should beat a flat-mean forecast on a clearly-seasonal series
    mae_model = float(np.mean(np.abs(y[-24:] - median)))
    mae_flat = float(np.mean(np.abs(y[-24:] - np.mean(y[:-24]))))
    assert mae_model < mae_flat


def test_determinism_same_seed_same_forecast():
    y = _seasonal()
    a = NeuralForecaster("NLinear", max_steps=100, seed=7).quantiles(y[:-24], 24, 24, (0.1, 0.5, 0.9))
    b = NeuralForecaster("NLinear", max_steps=100, seed=7).quantiles(y[:-24], 24, 24, (0.1, 0.5, 0.9))
    assert np.allclose(a, b, atol=1e-4)               # seeded training is reproducible


def test_too_short_series_raises():
    fc = NeuralForecaster("NLinear")
    with pytest.raises(ValueError):
        fc.quantiles(np.arange(20, dtype=float), m=24, h=24, levels=(0.1, 0.5, 0.9))


def test_registry_gated_by_env(monkeypatch):
    monkeypatch.delenv("CHRONOSCOPE_ENABLE_NEURAL", raising=False)
    assert neural_forecasters() == []                 # off by default (fast test path)
    monkeypatch.setenv("CHRONOSCOPE_ENABLE_NEURAL", "1")
    fcs = neural_forecasters()
    assert {f.name for f in fcs} == {"NLinear", "DLinear", "NHITS"}
    assert neural_available() is True
