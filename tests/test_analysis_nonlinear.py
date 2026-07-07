"""Nonlinear-dynamics tests: chaotic (logistic map) vs regular (sine) vs stochastic (noise) discrimination."""
import numpy as np
import pytest

from chronoscopelab.analysis import nonlinear as nl


def _logistic(n=3000, r=3.99, x0=0.4):
    x = np.empty(n)
    x[0] = x0
    for i in range(1, n):
        x[i] = r * x[i - 1] * (1 - x[i - 1])
    return x


def _sine(n=3000):
    t = np.linspace(0, 120, n)
    return np.sin(t) + 0.5 * np.sin(2.1 * t)


def _noise(n=3000, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def test_embedding_shape():
    v = nl.time_delay_embed(np.arange(100), dim=3, lag=2)
    assert v.shape[1] == 3
    assert v.shape[0] == 100 - 2 * 2


def test_lyapunov_positive_for_chaos_and_lower_for_regular():
    lyap_chaos = nl.chaos_measures(_logistic(), emb_dim=4).lyap_r
    lyap_reg = nl.chaos_measures(_sine(), emb_dim=4).lyap_r
    assert lyap_chaos > lyap_reg                          # the logistic map is more sensitive to init cond.
    assert lyap_chaos > 0.1                               # genuine positive Lyapunov (chaos)


def test_zero_one_test_separates_chaos_from_regular():
    k_chaos = nl.zero_one_test(_logistic())
    k_reg = nl.zero_one_test(_sine())
    assert k_chaos > 0.5                                  # K near 1 for chaos
    assert k_reg < k_chaos                                # regular dynamics give a lower K


def test_rqa_determinism_high_for_regular_low_for_noise():
    det_reg = nl.recurrence_quantification(_sine(), emb_dim=3).determinism
    det_noise = nl.recurrence_quantification(_noise(), emb_dim=3).determinism
    assert det_reg > det_noise                            # a sine is far more deterministic than noise
    assert det_reg > 0.8


def test_iaaft_surrogate_preserves_spectrum_and_distribution():
    x = _logistic()
    s = nl.iaaft_surrogate(x, n_iter=100)
    # same amplitude distribution (sorted values match closely)
    assert np.allclose(np.sort(x), np.sort(s), atol=1e-6)
    # similar power spectrum
    px, ps = np.abs(np.fft.rfft(x)), np.abs(np.fft.rfft(s))
    assert np.corrcoef(px, ps)[0, 1] > 0.95


def test_surrogate_gate_flags_chaos_only_for_the_map():
    rep_chaos = nl.nonlinear_report(_logistic(), emb_dim=4, n_surrogates=9)
    rep_noise = nl.nonlinear_report(_noise(), emb_dim=4, n_surrogates=9)
    # the logistic map should be flagged chaotic; white noise must NOT be
    assert rep_chaos["likely_chaotic"] is True
    assert rep_noise["likely_chaotic"] is False


def test_report_is_json_ready_and_complete():
    rep = nl.nonlinear_report(_logistic(), emb_dim=4, n_surrogates=5)
    assert rep["n"] == 3000
    for key in ("correlation_dimension", "largest_lyapunov", "zero_one_K", "rqa", "surrogate_test"):
        assert key in rep
    assert "DOI" in rep["rqa"]["reference"]
    assert "DOI" in rep["surrogate_test"]["reference"]


def test_embed_too_short_raises():
    with pytest.raises(ValueError):
        nl.time_delay_embed(np.arange(3), dim=5, lag=2)


def test_nan_safe():
    y = _sine()
    y[3] = np.nan
    y[500] = np.inf
    rep = nl.nonlinear_report(y, n_surrogates=3)
    assert rep["n"] == 2998
