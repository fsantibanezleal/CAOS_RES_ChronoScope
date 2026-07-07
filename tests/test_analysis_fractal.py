"""Fractal toolkit tests: Hurst on known processes, fractal dimension ordering, MF-DFA width, DCCA sign."""
import numpy as np

from chronoscopelab.analysis import fractal as fr


def _white_noise(n=1000, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def _random_walk(n=1000, seed=0):
    return np.cumsum(np.random.default_rng(seed).normal(0.0, 1.0, n))


def _persistent(n=2000, seed=0):
    """A persistent (positively autocorrelated) series via a heavy AR(1)."""
    rng = np.random.default_rng(seed)
    y = np.empty(n)
    y[0] = 0.0
    for t in range(1, n):
        y[t] = 0.9 * y[t - 1] + rng.normal()
    return y


def test_hurst_orders_noise_below_random_walk():
    h_wn = fr.hurst(_white_noise())
    h_rw = fr.hurst(_random_walk())
    # white noise ~ 0.5 (DFA alpha ~ 0.5); a random walk is strongly persistent (DFA alpha ~ 1.5)
    assert h_wn.dfa_alpha < h_rw.dfa_alpha
    assert h_rw.dfa_alpha > 1.2                          # random-walk DFA alpha near 1.5
    assert h_wn.reliable is True


def test_hurst_short_series_flagged_unreliable():
    assert fr.hurst(_white_noise(50)).reliable is False


def test_fractal_dimension_rougher_for_noise():
    # white noise is maximally rough (D near 2); a smooth random walk is smoother (lower Higuchi D)
    d_noise = fr.fractal_dimension(_white_noise())
    d_walk = fr.fractal_dimension(_random_walk())
    assert d_noise.higuchi > d_walk.higuchi
    assert 1.0 <= d_walk.higuchi <= 2.0 and 1.0 <= d_noise.higuchi <= 2.0


def test_mfdfa_returns_a_spectrum():
    mf = fr.mfdfa(_random_walk(2000))
    assert len(mf.q) == len(mf.hq) == len(mf.alpha) == len(mf.f_alpha)
    assert mf.width >= 0.0
    # monofractal (fBm-like random walk) should have a narrow spectrum
    assert mf.width < 0.6


def test_mfdfa_needs_length():
    import pytest
    with pytest.raises(ValueError):
        fr.mfdfa(_white_noise(100))


def test_dcca_positive_for_coupled_series():
    rng = np.random.default_rng(3)
    common = np.cumsum(rng.normal(size=1000))
    x = common + np.cumsum(rng.normal(0, 0.3, 1000))
    y = common + np.cumsum(rng.normal(0, 0.3, 1000))
    res = fr.dcca_coefficient(x, y, scale=50)
    assert res["rho_dcca"] > 0.5                         # strongly cross-correlated at this scale


def test_dcca_near_zero_for_independent_series():
    rng = np.random.default_rng(4)
    x = np.cumsum(rng.normal(size=1000))
    y = np.cumsum(rng.normal(size=1000))
    res = fr.dcca_coefficient(x, y, scale=50)
    assert abs(res["rho_dcca"]) < 0.5                    # independent -> low detrended cross-correlation


def test_report_is_json_ready_and_complete():
    rep = fr.fractal_report(_random_walk(2000))
    assert rep["n"] == 2000
    assert "interpretation" in rep["hurst"]
    assert rep["fractal_dimension"]["higuchi"] > 0
    assert "d" in rep["arfima_link"]
    assert "multifractal" in rep
    # Hurst 1951 / Peng 1994 predate DOIs; the MF-DFA reference carries one.
    assert "1951" in rep["hurst"]["reference"] and "Peng" in rep["hurst"]["reference"]
    if "reference" in rep["multifractal"]:
        assert "DOI" in rep["multifractal"]["reference"]


def test_nan_safe():
    y = _random_walk(2000)
    y[3] = np.nan
    y[500] = np.inf
    rep = fr.fractal_report(y)
    assert rep["n"] == 1998
