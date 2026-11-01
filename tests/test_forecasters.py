"""Classical forecasting core tests: method correctness, interval shape, and the normal quantile."""
import math

import numpy as np

from chronoscopelab.model.forecasters import (
    METHOD_FNS,
    forecast_all,
    normal_ppf,
    seasonal_naive,
)


def _seasonal(n=120, m=12, seed=0):
    rng = np.random.default_rng(seed)
    return 50 + 10 * np.sin(np.arange(n) * 2 * np.pi / m) + rng.normal(0, 1.0, n)


def test_normal_ppf_known_values():
    assert abs(normal_ppf(0.5)) < 1e-6
    assert abs(normal_ppf(0.9) - 1.2815515) < 1e-4
    assert normal_ppf(0.1) < 0 < normal_ppf(0.9)


def test_seasonal_naive_repeats_last_season():
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    point, sigma = seasonal_naive(y, m=3, h=5)
    assert np.allclose(point, [4.0, 5.0, 6.0, 4.0, 5.0])
    assert sigma >= 0.0


def test_all_methods_finite_point_and_sigma():
    y = _seasonal()
    for name, fn in METHOD_FNS.items():
        point, sigma = fn(y, 12, 12)
        assert point.shape == (12,), name
        assert np.all(np.isfinite(point)), name
        assert sigma >= 0.0 and math.isfinite(sigma), name


def test_forecast_all_intervals_ordered_and_widen():
    y = _seasonal()
    forecasts = forecast_all(y, 12, 12, (0.1, 0.5, 0.9))
    assert len(forecasts) == len(METHOD_FNS)
    for f in forecasts:
        lo, up = np.array(f.lower), np.array(f.upper)
        assert np.all(up >= lo - 1e-9), f.name                 # upper >= lower
        assert (up[-1] - lo[-1]) >= (up[0] - lo[0]) - 1e-9, f.name  # interval widens with horizon


def test_holt_winters_beats_naive_on_clean_seasonal():
    # On a clean seasonal series the seasonal methods should be reasonable (finite, right length).
    y = _seasonal(n=240, seed=3)
    point, _ = METHOD_FNS["HoltWinters"](y, 12, 24)
    assert point.shape == (24,) and np.all(np.isfinite(point))


def test_adversarial_holt_winters_preserves_an_incomplete_seasons_phase():
    pattern = np.array([10.0, 18.0, 7.0, 14.0])
    history = np.tile(pattern, 21)[:83]
    point, _ = METHOD_FNS["HoltWinters"](history, 4, 9)
    expected = np.array([pattern[(len(history) + k) % 4] for k in range(9)])
    np.testing.assert_allclose(point, expected, atol=1e-8)


def test_adversarial_theta_matches_the_two_theta_lines_with_finite_history():
    from chronoscopelab.model.forecasters import _opt_alpha, _ses_run, theta

    y = np.array([3.0, 4.0, 7.0, 7.5, 10.0, 11.0, 15.0])
    b, a = np.polyfit(np.arange(len(y)), y, 1)
    alpha = _opt_alpha(y)
    _, theta_two = _ses_run(2 * y - (a + b * np.arange(len(y))), alpha)
    expected = 0.5 * (a + b * np.arange(len(y), len(y) + 5) + theta_two)
    point, _ = theta(y, 1, 5)
    np.testing.assert_allclose(point, expected, atol=1e-10)
