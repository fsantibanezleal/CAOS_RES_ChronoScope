"""Independent small-array controls for the held-out evaluation protocol."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_browser_linear import (  # noqa: E402
    HORIZON, LOOKBACK, calibration_radii, fit_ridge, losses,
    normalize_window, paired_summary, select_weights,
)


def test_adversarial_positive_affine_units_preserve_normalized_window_and_raw_forecast():
    history = np.arange(LOOKBACK, dtype=float) ** 1.1
    target = np.arange(LOOKBACK, LOOKBACK + HORIZON, dtype=float) ** 1.1
    x, y, scale, last = normalize_window(history, target)
    xx, yy, ss, ll = normalize_window(history * 1000 + 273.15, target * 1000 + 273.15)
    np.testing.assert_allclose(xx, x, atol=1e-12)
    np.testing.assert_allclose(yy, y, atol=1e-12)
    point, lower, upper = y * .9, y * .9 - .5, y * .9 + .5
    for values in (point, lower, upper):
        np.testing.assert_allclose(values * ss + ll, (values * scale + last) * 1000 + 273.15)
    for key, value in losses(y[None], point[None], lower[None], upper[None]).items():
        np.testing.assert_allclose(losses(yy[None], point[None], lower[None], upper[None])[key], value)


@pytest.mark.parametrize("kind", ["constant", "nan", "short", "bad_target"])
def test_adversarial_unusable_window_is_refused(kind):
    history, target = np.arange(LOOKBACK, dtype=float), np.arange(HORIZON, dtype=float)
    if kind == "constant":
        history[:] = 5
    elif kind == "nan":
        history[0] = np.nan
    elif kind == "short":
        history = history[:-1]
    else:
        target[-1] = np.inf
    with pytest.raises(ValueError):
        normalize_window(history, target)


def test_adversarial_rank_deficient_fit_and_regularized_closed_form():
    x = np.zeros((2, LOOKBACK))
    x[:, 0] = [1, 2]
    y = np.repeat(np.array([[3.], [6.]]), HORIZON, axis=1)
    unpenalized = fit_ridge(x, y, 0)
    np.testing.assert_allclose(unpenalized[0], 3)
    np.testing.assert_allclose(unpenalized[1:], 0)
    # Mean x^2 = 2.5 and mean xy = 7.5; ridge coefficient is 7.5/(2.5+lambda).
    np.testing.assert_allclose(fit_ridge(x, y, 2.5)[0], 1.5)
    np.testing.assert_allclose(fit_ridge(x, y, 2.5)[1:], 0)


def test_adversarial_selection_uses_validation_and_ordered_ties_only():
    x = np.zeros((2, LOOKBACK))
    x[:, 0] = [1, 2]
    y = np.ones((2, HORIZON))
    _, table = select_weights(x, y, x, np.zeros_like(y))
    assert next(row["penalty"] for row in table if row.get("selected")) == 10
    _, ties = select_weights(x, np.zeros_like(y), x, np.zeros_like(y))
    assert next(row["penalty"] for row in ties if row.get("selected")) == 0


def test_adversarial_calibration_uses_finite_sample_rank_and_each_lead_separately():
    # n=4, alpha=.2 -> ceil(5*.8)=4, not an interpolated 80th percentile.
    residual = np.arange(1, 5)[:, None] * np.arange(1, HORIZON + 1)[None]
    np.testing.assert_array_equal(calibration_radii(-residual), residual[-1])
    with pytest.raises(ValueError, match="Too few"):
        calibration_radii(residual[:1])
    with pytest.raises(ValueError):
        calibration_radii(np.full((4, HORIZON), np.nan))


def test_adversarial_interval_score_has_correct_tail_penalties_and_inclusive_coverage():
    target = np.tile([-2., 0., 2., 1.], 3)[None]
    point = np.zeros_like(target)
    result = losses(target, point, point - 1, point + 1)
    np.testing.assert_allclose(result["normalized_interval_score"], 7)  # (12+2+12+2)/4
    np.testing.assert_allclose(result["coverage"], .5)
    np.testing.assert_allclose(result["normalized_width"], 2)
    np.testing.assert_allclose(result["normalized_mae"], 1.25)
    np.testing.assert_allclose(result["normalized_mse"], 2.25)
    with pytest.raises(ValueError):
        losses(target, point, point + 1, point - 1)


def test_adversarial_paired_resampling_preserves_pairs_and_is_reproducible():
    constant = paired_summary(np.full(20, -2.))
    assert constant["mean_difference"] == -2
    assert constant["percentile_95"] == [-2, -2]
    assert constant["strictly_lower_loss_series"] == 20
    assert paired_summary(np.arange(20.)) == paired_summary(np.arange(20.))
