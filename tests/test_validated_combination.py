import numpy as np
import pytest

from chronoscopelab.model.context_memory import fit_context_memory
from chronoscopelab.model.validated_combination import convex_weights, fit_validated, temporal_splits


def test_temporal_validation_excludes_incomplete_target_blocks():
    splits = temporal_splits((20, 23, 26, 29, 32), 7)
    assert splits[2]["train"] == ()
    assert splits[3]["train"] == (0,)
    assert splits[4]["train"] == (0, 1)


def test_convex_stacking_finds_perfect_expert_and_obeys_simplex():
    errors = np.array([[0., 10., -4.], [0., 5., 2.], [0., -3., 7.]])
    w = convex_weights(errors, .01)
    assert np.min(w) >= 0 and np.sum(w) == pytest.approx(1.)
    assert w[0] > .99
    assert np.mean((errors @ w) ** 2) < np.mean((errors @ np.full(3, 1/3)) ** 2)


@pytest.mark.parametrize("stacking", [True, False])
def test_deterministic_ordered_predictions_with_causally_complete_memory(stacking):
    y = 20 + .03 * np.arange(120) + 3 * np.sin(np.arange(120) * 2*np.pi/12)
    a = fit_validated(y, 12, 6, stacking=stacking)
    b = fit_validated(y, 12, 6, stacking=stacking)
    np.testing.assert_array_equal(a.quantiles, b.quantiles)
    assert np.all(np.diff(a.quantiles, axis=1) >= 0)
    assert np.min(a.weights) >= .01 - 1e-12
    assert np.sum(a.weights) == pytest.approx(1.)
    for split in a.validation_splits:
        assert all(a.origins[i] + 6 <= split["query"] for i in split["train"])
    assert all(o+6 <= len(y) for o in a.origins)


def test_insufficient_validation_uses_exact_matching_recency_control():
    y = np.arange(24, dtype=float) + 10
    proposed = fit_validated(y, 12, 6)
    control = fit_context_memory(y, 12, 6, mode="recency")
    assert proposed.validation_splits == ()
    assert proposed.selected == ("recency", 1., 1.)
    np.testing.assert_array_equal(proposed.quantiles, control.quantiles)


def test_stacking_rejects_unavailable_training_values():
    with pytest.raises(ValueError, match="finite"):
        convex_weights([[1., np.nan]], .1)
