"""Resampling preserves paired identities and does not overweight long series."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "combination_uncertainty", Path(__file__).resolve().parents[1] / "scripts/summarize_combination_uncertainty.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_constant_paired_effect_has_degenerate_interval():
    result = module.paired_interval([-2., -2., -2.], seed=8, resamples=200)
    assert result["difference"] == -2
    assert result["percentile_95"] == [-2., -2.]
    assert result["negative"] == result["series"] == 3


def test_batching_is_identical_and_does_not_consume_caller_rng():
    np.random.seed(17)
    before = np.random.get_state()
    a = module.paired_interval([-5., -2., 0., 4.], seed=31, resamples=200, batch=7)
    b = module.paired_interval([-5., -2., 0., 4.], seed=31, resamples=200, batch=64)
    assert a == b
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])


def test_adversarial_equal_series_weighting_refuses_duplicate_identities():
    def origin(value):
        return {"methods": [{"name": name, "metrics": dict.fromkeys(module.METRICS, value)}
                            for name in module.METHODS + module.CONTROLS]}

    rows = [{"dataset": "one", "id": "a", "origins": [origin(1), origin(3)]},
            {"dataset": "one", "id": "b", "origins": [origin(8)]}]
    result = module.series_scores(rows)
    assert result[("one", "a")]["ValidationMix"]["mase"] == 2
    assert np.mean([x["ValidationMix"]["mase"] for x in result.values()]) == 5
    with pytest.raises(ValueError, match="once"):
        module.series_scores(rows + rows[:1])


@pytest.mark.parametrize("values", [[], [float("nan")], [[1., 2.]]])
def test_invalid_pairs_are_not_silently_removed(values):
    with pytest.raises(ValueError, match="finite vector"):
        module.paired_interval(values, seed=4, resamples=200)
