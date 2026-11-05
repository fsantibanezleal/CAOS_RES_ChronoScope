"""Adversarial controls for prefix-only calibration and fixed admission rules."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from confirm_browser_calibration import admission, group_radii, roughness_bin  # noqa: E402


def prefixes():
    t = np.arange(48)
    return np.array([t, np.sin(2 * np.pi * t / 6), (-1.) ** t])


def test_adversarial_roughness_uses_prefix_shape_and_is_unit_invariant():
    x = prefixes()
    np.testing.assert_array_equal(roughness_bin(x), [0, 1, 2])
    np.testing.assert_array_equal(roughness_bin(x * 1000 + 273.15), [0, 1, 2])
    with pytest.raises(ValueError):
        roughness_bin(np.ones((1, 48)))
    with pytest.raises(ValueError):
        roughness_bin(np.full((1, 48), np.nan))


def test_adversarial_calibration_cannot_pool_or_swap_prefix_groups():
    x = np.repeat(prefixes(), 20, axis=0)
    residual = np.repeat(np.array([1., 2., 4.]), 20)[:, None] * np.ones((1, 12))
    radii, counts = group_radii(x, residual)
    assert counts == [20, 20, 20]
    np.testing.assert_array_equal(radii[:, 0], [1, 2, 4])
    permutation = np.random.default_rng(17).permutation(60)
    np.testing.assert_array_equal(group_radii(x[permutation], residual[permutation])[0], radii)
    with pytest.raises(ValueError, match="fewer than 20"):
        group_radii(x[:-1], residual[:-1])


@pytest.mark.parametrize("defect", ["points", "count", "score", "overall", "bin", "parity"])
def test_adversarial_every_prerecorded_admission_condition_can_refuse(defect):
    scores = {"all": {"stratified": {"normalized_interval_score": 2., "coverage": .8},
                      "gaussian": {"normalized_interval_score": 4.}}}
    scores.update({f"prefix_bin_{g}": {"stratified": {"coverage": .8}} for g in range(3)})
    counts, parity, identical = [30, 30, 30], 1e-6, True
    assert all(admission(scores, counts, parity, identical).values())
    if defect == "points":
        identical = False
    elif defect == "count":
        counts[0] = 19
    elif defect == "score":
        scores["all"]["stratified"]["normalized_interval_score"] = 4.1
    elif defect == "overall":
        scores["all"]["stratified"]["coverage"] = .99
    elif defect == "bin":
        scores["prefix_bin_1"]["stratified"]["coverage"] = .69
    else:
        parity = .0001
    assert not all(admission(scores, counts, parity, identical).values())
