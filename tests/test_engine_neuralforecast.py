"""Canonical deep-tier tests (neuralforecast on the py3.12 base): real framework, GPU-gated, quantile columns.

Skipped when neuralforecast/torch are absent (the py3.13 venv, CI) - the direct-torch reference engine in
test_engine_neural.py covers those environments. Here the REAL Nixtla framework trains NHITS/DLinear/NLinear
per case and must produce monotone quantiles that beat a flat baseline on a seasonal series.
"""
import numpy as np
import pytest

nf = pytest.importorskip("neuralforecast")  # canonical tier needs the framework (py3.12 base)
torch = pytest.importorskip("torch")

from chronoscopelab.engines.neuralforecast_engine import (  # noqa: E402 - after the skip-guards by design
    NeuralForecastForecaster,
    _match_quantile_column,
    neuralforecast_available,
    neuralforecast_forecasters,
)


def _seasonal(n=400, m=24, seed=0):
    t = np.arange(n)
    return 100 + 20 * np.sin(2 * np.pi * t / m) + np.random.default_rng(seed).normal(0, 3, n)


def test_column_matcher_handles_all_naming_schemes():
    assert _match_quantile_column(["NHITS-ql0.1", "NHITS-ql0.5", "NHITS-ql0.9"], "NHITS", 0.1) == "NHITS-ql0.1"
    assert _match_quantile_column(["NL-lo-80.0", "NL-median", "NL-hi-80.0"], "NL", 0.1) == "NL-lo-80.0"
    assert _match_quantile_column(["NL-lo-80", "NL-median", "NL-hi-80"], "NL", 0.9) == "NL-hi-80"
    assert _match_quantile_column(["NL-lo-80.0", "NL-median", "NL-hi-80.0"], "NL", 0.5) == "NL-median"
    with pytest.raises(KeyError):
        _match_quantile_column(["NL-median"], "NL", 0.1)


@pytest.mark.parametrize("name", ["NHITS", "NLinear"])
def test_nf_model_produces_monotone_quantiles(name):
    y = _seasonal()
    fc = NeuralForecastForecaster(name, max_steps=120)
    q = fc.quantiles(y[:-24], m=24, h=24, levels=(0.1, 0.5, 0.9))
    assert q.shape == (24, 3)
    assert np.all(q[:, 0] <= q[:, 1] + 1e-6) and np.all(q[:, 1] <= q[:, 2] + 1e-6)


def test_nhits_beats_a_flat_baseline():
    y = _seasonal()
    fc = NeuralForecastForecaster("NHITS", max_steps=250)
    q = fc.quantiles(y[:-24], m=24, h=24, levels=(0.1, 0.5, 0.9))
    mae_model = float(np.mean(np.abs(y[-24:] - q[:, 1])))
    mae_flat = float(np.mean(np.abs(y[-24:] - np.mean(y[:-24]))))
    assert mae_model < mae_flat


def test_registry_gated_by_env(monkeypatch):
    monkeypatch.delenv("CHRONOSCOPE_ENABLE_NEURALFORECAST", raising=False)
    assert neuralforecast_forecasters() == []
    monkeypatch.setenv("CHRONOSCOPE_ENABLE_NEURALFORECAST", "1")
    fcs = neuralforecast_forecasters()
    assert {f.model_name for f in fcs} == {"NHITS", "DLinear", "NLinear"}
    assert all(f.name.endswith("(nf)") for f in fcs)
    assert neuralforecast_available() is True
