"""Independent small examples protect the replay's additional case analysis."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("replay_cases", Path(__file__).resolve().parents[1] / "scripts/analyze_replay_cases.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def rows():
    return [[i, actual, -1., 0., 1., 0., 1., .2, .2, 0., 0., i + 1, hit, None]
            for i, (actual, hit) in enumerate([(0., 1.), (4., 0.), (0., 1.)])]


def test_manual_width_penalty_and_overlapping_coverage_windows():
    # Interval scores are 2, 32, 2; trailing coverages are 1, 1/2, 2/3.
    result = MODULE.summarize_rows(rows(), 2.)
    np.testing.assert_allclose(result, [(.2 + .3 + .13333) / 3, 6.], rtol=0, atol=1e-12)


def test_scaled_scores_are_invariant_under_positive_affine_source_units():
    transformed = rows()
    for row in transformed:
        for column in (1, 2, 3, 4):
            row[column] = 13 + 10 * row[column]
    np.testing.assert_allclose(MODULE.summarize_rows(transformed, 20.), MODULE.summarize_rows(rows(), 2.), atol=1e-12)


def test_invalid_hit_or_scale_cannot_be_silently_omitted():
    bad = rows()
    bad[1][12] = 1.
    with pytest.raises(ValueError, match="hit column"):
        MODULE.summarize_rows(bad, 2.)
    with pytest.raises(ValueError, match="positive historical scale"):
        MODULE.summarize_rows(rows(), 0.)


def test_joint_case_pairing_cancels_shared_difficulty_exactly():
    # Difficulty varies by whole case, while both controller effects are fixed.
    # Unpaired method resampling would manufacture spurious uncertainty here.
    values = np.array([[[d, d], [d - .1, d + .2], [d - .3, d + .4]] for d in [1., 10., 100.]])
    draw = MODULE.paired_resample(values, 1000, 42)
    np.testing.assert_allclose(draw, np.broadcast_to([[-.1, .2], [-.3, .4]], draw.shape), rtol=0, atol=1e-12)


def test_perfect_constant_base_is_counterexample_to_clipped_coverage_guarantee():
    spec = importlib.util.spec_from_file_location("historical_replay", Path(__file__).resolve().parents[1] / "scripts/manuscript_replay.py")
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    result = replay.evaluate(np.zeros(420), [[0., 0.]] * 400, 20, controller="ACI", keep_rows=True)
    assert result["final_coverage"] == 1.
    a = np.asarray(result["rows"], dtype=float)
    assert a[-1, 8] == 1 - 1e-4
    residual = a[:, 8] - a[:, 7] - .02 * (a[:, 12] - .8)
    reconstructed_error = (a[-1, 8] - a[0, 7] - residual.sum()) / (.02 * len(a))
    assert reconstructed_error == pytest.approx(.2)
