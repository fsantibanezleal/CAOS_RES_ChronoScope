"""Foundation-tier tests (checkpoint-gated): Chronos-Bolt, Chronos-2, TimesFM 2.5 zero-shot from the vault.

Skipped when the packages or the vault checkpoints are absent (CI has neither) - the availability guards
themselves are always tested. When present, each foundation model must produce monotone quantiles of the
right shape zero-shot on a seasonal series.
"""
import numpy as np
import pytest

from chronoscopelab.engines.chronos_engine import chronos_forecasters, foundation_available
from chronoscopelab.engines.timesfm_engine import timesfm_available, timesfm_forecasters


def _seasonal(n=300, m=24, seed=0):
    t = np.arange(n)
    return 100 + 20 * np.sin(2 * np.pi * t / m) + np.random.default_rng(seed).normal(0, 2, n)


def test_registries_gated_by_env(monkeypatch):
    monkeypatch.delenv("CHRONOSCOPE_ENABLE_FOUNDATION", raising=False)
    assert chronos_forecasters() == []
    assert timesfm_forecasters() == []


@pytest.mark.skipif(not foundation_available(), reason="chronos deps/checkpoints absent")
def test_chronos_tiers_zero_shot(monkeypatch):
    monkeypatch.setenv("CHRONOSCOPE_ENABLE_FOUNDATION", "1")
    fcs = chronos_forecasters()
    names = {f.name for f in fcs}
    assert "Chronos-Bolt" in names
    y = _seasonal()
    for fc in fcs:
        q = fc.quantiles(y, 24, 24, (0.1, 0.5, 0.9))
        assert q.shape == (24, 3)
        assert np.all(q[:, 0] <= q[:, 1] + 1e-6) and np.all(q[:, 1] <= q[:, 2] + 1e-6)
        assert fc.family == "foundation"


@pytest.mark.skipif(not timesfm_available(), reason="timesfm package/checkpoint absent")
def test_timesfm_zero_shot(monkeypatch):
    monkeypatch.setenv("CHRONOSCOPE_ENABLE_FOUNDATION", "1")
    fcs = timesfm_forecasters()
    assert [f.name for f in fcs] == ["TimesFM-2.5"]
    y = _seasonal()
    q = fcs[0].quantiles(y, 24, 24, (0.1, 0.5, 0.9))
    assert q.shape == (24, 3)
    assert np.all(q[:, 0] <= q[:, 1] + 1e-6) and np.all(q[:, 1] <= q[:, 2] + 1e-6)


@pytest.mark.skipif(not timesfm_available(), reason="timesfm package/checkpoint absent")
def test_timesfm_median_tracks_a_clean_seasonal(monkeypatch):
    monkeypatch.setenv("CHRONOSCOPE_ENABLE_FOUNDATION", "1")
    y = _seasonal(seed=1)
    q = timesfm_forecasters()[0].quantiles(y[:-24], 24, 24, (0.1, 0.5, 0.9))
    mae = float(np.mean(np.abs(y[-24:] - q[:, 1])))
    mae_flat = float(np.mean(np.abs(y[-24:] - np.mean(y[:-24]))))
    assert mae < mae_flat                                 # zero-shot beats a flat-mean baseline
