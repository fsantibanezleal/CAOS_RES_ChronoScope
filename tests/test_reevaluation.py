import numpy as np
import pytest

from chronoscopelab.model.context_memory import fit_context_memory
from chronoscopelab.reevaluation import metrics


def test_adversarial_context_memory_uses_only_completed_training_targets():
    y = 10 + np.sin(np.arange(73) * 0.5) + np.arange(73) * 0.1
    fit = fit_context_memory(y, 6, 9)
    assert fit.origins and max(fit.origins) + 9 <= len(y)
    assert np.all(fit.weights > 0) and abs(fit.weights.sum() - 1) < 1e-12
    assert np.isfinite(fit.quantiles).all()
    assert np.all(np.diff(fit.quantiles, axis=1) >= 0)


def test_adversarial_context_memory_is_equivariant_to_positive_scale_and_location():
    y = np.array([10 + 3 * np.sin(t * 0.5) + t * 0.03 for t in range(68)])
    first = fit_context_memory(y, 6, 7)
    second = fit_context_memory(4 * y + 80, 6, 7)
    np.testing.assert_allclose(first.weights, second.weights, atol=1e-9)
    np.testing.assert_allclose(4 * first.quantiles + 80, second.quantiles, atol=1e-8)


def test_adversarial_invalid_forecast_shapes_and_crossed_intervals_are_rejected():
    with pytest.raises(ValueError):
        metrics([1, 2, 3], [4, 5], [4], [3, 4], [5, 6], 1)
    with pytest.raises(ValueError):
        metrics([1, 2, 3], [4, 5], [4, 5], [5, 4], [6, 6], 1)


def test_holdout_metrics_have_known_values():
    score = metrics([1, 2, 3], [4, 6], [4, 5], [3, 4], [5, 6], 1)
    assert score["mae"] == score["mase"] == 0.5
    assert score["coverage"] == 1.0
    assert score["mean_width"] == 2.0
