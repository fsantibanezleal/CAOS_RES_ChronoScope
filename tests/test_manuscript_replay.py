"""Check reconstruction against the external package, including information order."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from preqts import AdaptiveConformal, ConformalPID, ReplayAdapter

SPEC = importlib.util.spec_from_file_location("manuscript_replay", Path(__file__).resolve().parents[1] / "scripts/manuscript_replay.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


@pytest.mark.parametrize("controller", ["ACI", "PID"])
def test_exported_updates_match_package(controller):
    y = np.array([0., 2., -1., 3., 8., -4., 1., 9., 2.])
    paths = [[.2 * i, .5 + .1 * i] for i in range(len(y) - 3)]

    def batch(context, horizon, past_cov, future_cov, levels):
        point, sigma = paths[len(context) - 3]
        return np.array([[point + replay.normal_ppf(q) * sigma for q in levels]])

    base = ReplayAdapter(batch)
    fc = AdaptiveConformal(base, gamma=.02) if controller == "ACI" else ConformalPID(base, kp=.05, ki=.02, kd=.02)
    fc.start(y[:3])
    result = replay.evaluate(y, paths, 3, controller=controller, keep_rows=True)
    for row in result["rows"]:
        q = fc.predict(1, [.1, .5, .9])
        np.testing.assert_allclose(row[2:5], q[0], rtol=1e-12, atol=1e-12)
        fc.ingest(np.array([row[1]]))
        np.testing.assert_allclose(row[8], fc._states[0].alpha, rtol=1e-12, atol=1e-12)


def test_future_targets_cannot_change_earlier_intervals():
    y = np.arange(20, dtype=float)
    changed = y.copy()
    changed[13:] = 1000.
    paths = [[1., 1.]] * 15
    a = replay.evaluate(y, paths, 5, controller="PID", keep_rows=True)["rows"]
    b = replay.evaluate(changed, paths, 5, controller="PID", keep_rows=True)["rows"]
    assert a[:8] == b[:8]
    assert a[8][2:5] == b[8][2:5]  # first altered target was not read by predict
    assert a[9][2:5] != b[9][2:5]  # alteration can affect the subsequent update


def test_local_coverage_error_is_not_cancelled_by_time_averaging():
    y = np.array([0., 0., 0., 0., 0., 4., 4., 4., 4.])
    r = replay.evaluate(y, [[0., 1.]] * 6, 3)
    assert r["mean_rolling_absolute_error"] > r["rolling_summary_error"] + .01


def test_zero_target_wql_is_unavailable():
    r = replay.evaluate(np.zeros(5), [[0., 1.]] * 3, 2, keep_rows=True)
    assert r["mean_wql"] is None
    assert r["wql_available_steps"] == 0
