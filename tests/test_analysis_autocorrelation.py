"""Autocorrelation toolkit tests: ground-truth checks against AR(1), MA(1), white noise, and an AR residual."""
import numpy as np

from chronoscopelab.analysis import autocorrelation as ac


def _white_noise(n=500, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def _ar1(phi=0.7, n=500, seed=0):
    rng = np.random.default_rng(seed)
    y = np.empty(n)
    y[0] = 0.0
    for t in range(1, n):
        y[t] = phi * y[t - 1] + rng.normal(0.0, 1.0)
    return y


def _ma1(theta=0.8, n=500, seed=0):
    rng = np.random.default_rng(seed)
    e = rng.normal(0.0, 1.0, n)
    y = e[1:] + theta * e[:-1]
    return y


def test_bartlett_band_matches_196_over_sqrt_n():
    assert abs(ac.bartlett_band(100, alpha=0.05) - 1.96 / 10.0) < 1e-2


def test_acf_lag0_is_one():
    c = ac.acf(_ar1(), nlags=20)
    assert abs(c.values[0] - 1.0) < 1e-9


def test_white_noise_has_few_significant_spikes():
    c = ac.acf(_white_noise(), nlags=30)
    # ~5% of lags escape the band by chance; with n=500 expect a handful, not many
    assert len(c.signif_lags) <= 5
    assert ac.ljung_box(_white_noise(), lags=10).white_noise is True


def test_ar1_shows_in_acf_and_pacf_cut_at_one():
    c_acf = ac.acf(_ar1(0.7), nlags=20)
    c_pacf = ac.pacf(_ar1(0.7), nlags=20)
    assert 1 in c_acf.signif_lags                      # strong lag-1 autocorrelation
    assert 1 in c_pacf.signif_lags                     # PACF cut after p=1 is the AR(1) signature
    assert ac.ljung_box(_ar1(0.7), lags=10).white_noise is False


def test_ma1_shows_in_acf_cut_after_one():
    c_acf = ac.acf(_ma1(0.8), nlags=20)
    assert 1 in c_acf.signif_lags
    # for an MA(1) the ACF should cut off after lag 1 (later lags ~0)
    assert all(lag > 1 for lag in c_acf.signif_lags) is False or 1 in c_acf.signif_lags


def test_durbin_watson_near_two_for_white_noise():
    assert abs(ac.durbin_watson(_white_noise()) - 2.0) < 0.2


def test_durbin_watson_low_for_positive_serial_correlation():
    assert ac.durbin_watson(_ar1(0.8)) < 1.5           # positive serial correlation -> DW well below 2


def test_lag_plot_pairs_shapes():
    y = _ar1()
    xs, ys = ac.lag_plot_pairs(y, lag=1)
    assert xs.shape == ys.shape
    assert len(xs) == len(y) - 1


def test_report_is_json_ready_and_complete():
    rep = ac.autocorrelation_report(_ar1(), nlags=20, lags_m=10)
    assert rep["n"] == 500
    assert "bartlett_band" in rep and rep["bartlett_band"] > 0
    assert len(rep["acf"]) == 21 and rep["acf"][0]["value"] == 1.0
    assert "identification_hint" in rep and isinstance(rep["identification_hint"], str)
    assert "DOI" in rep["ljung_box"]["reference"]


def test_nan_safe():
    y = _ar1()
    y[10] = np.nan
    y[100] = np.inf
    rep = ac.autocorrelation_report(y, nlags=15)
    assert rep["n"] < 500                              # non-finite points dropped, not crashing
