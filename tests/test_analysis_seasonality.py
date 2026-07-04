"""Seasonality toolkit tests: ground-truth checks on a clean sinusoid, white noise, and multi-seasonal data."""
import numpy as np

from chronoscopelab.analysis import seasonality as se


def _sin(n=360, m=12, fs=1.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / fs
    return 50 + 10 * np.sin(2 * np.pi * t / m) + rng.normal(0, 0.3, n)


def _two_seasonal(n=2016, m1=24, m2=168, seed=0):
    """Two-period series: daily (24) + weekly (168) on the same scale."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return 5 + 3 * np.sin(2 * np.pi * t / m1) + 2 * np.sin(2 * np.pi * t / m2) + rng.normal(0, 0.3, n)


def _white_noise(n=360, seed=0):
    return np.random.default_rng(seed).normal(0, 1.0, n)


def test_periodogram_finds_the_dominant_period():
    s = se.periodogram(_sin(m=12), fs=1.0)
    assert s.dominant_period is not None
    assert abs(s.dominant_period - 12.0) < 1.0           # recovers the 12-step period within ~1 sample


def test_welch_agrees_with_periodogram_on_the_period():
    pw = se.welch(_sin(m=12), fs=1.0)
    assert pw.dominant_period is not None
    assert abs(pw.dominant_period - 12.0) < 2.0


def test_seasonal_strength_separates_seasonal_from_noise():
    assert se.seasonal_strength(_sin(m=12), period=12) > 0.8
    assert se.seasonal_strength(_white_noise(), period=12) < 0.3


def test_seasonal_strength_zero_when_too_short():
    assert se.seasonal_strength(_sin(n=15, m=12), period=12) == 0.0


def test_stl_decomposes_into_three_additive_components():
    y = _sin(m=12)
    d = se.stl_decompose(y, period=12)
    recon = d.trend + d.seasonal + d.remainder
    assert np.allclose(recon, y, atol=1e-6)
    assert d.strength_seasonal > 0.8
    assert 0.0 <= d.strength_trend <= 1.0


def test_mstl_handles_two_seasonal_periods():
    y = _two_seasonal(m1=24, m2=168)
    d = se.mstl_decompose(y, periods=[24, 168])
    recon = d.trend + d.seasonal + d.remainder
    assert np.allclose(recon, y, atol=1e-6)
    assert d.strength_seasonal > 0.7
    assert d.periods == (24, 168)


def test_seasonal_subseries_means_match_the_pattern():
    y = _sin(n=240, m=12, seed=1)
    sub = se.seasonal_subseries(y, period=12)
    assert sub.period == 12
    assert len(sub.means) == 12
    # the per-phase means should sweep a sinusoid (max - min ~ 20 for amplitude 10)
    assert (sub.means.max() - sub.means.min()) > 10.0


def test_report_is_json_ready_and_complete():
    rep = se.seasonality_report(_sin(m=12), fs=1.0, candidate_periods=[6, 12])
    assert rep["n"] == 360
    assert rep["periodogram"]["dominant_period"] is not None
    assert 12 in rep["seasonal_strength_by_candidate_period"]
    assert rep["seasonal_strength_by_candidate_period"][12] > 0.8
    assert "DOI" in rep["welch"]["reference"]


def test_nan_safe_periodogram():
    y = _sin(m=12)
    y[5] = np.nan
    y[100] = np.inf
    s = se.periodogram(y, fs=1.0)
    assert s.dominant_period is not None
