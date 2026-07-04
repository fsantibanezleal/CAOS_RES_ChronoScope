"""Change-point toolkit tests: ground truth = a series with KNOWN break locations and regimes."""
import numpy as np

from chronoscopelab.analysis import changepoints as cp


def _level_shifts(n=300, breaks=(100, 200), levels=(0.0, 5.0, -3.0), noise=0.5, seed=0):
    """Piecewise-constant mean with known breaks."""
    rng = np.random.default_rng(seed)
    y = np.empty(n)
    bounds = [0, *breaks, n]
    for lvl, (s, e) in zip(levels, zip(bounds[:-1], bounds[1:])):
        y[s:e] = lvl
    return y + rng.normal(0, noise, n)


def _stable(n=300, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def test_pelt_finds_the_two_level_shifts():
    y = _level_shifts()
    res = cp.pelt(y)
    assert len(res.breakpoints) == 2
    assert abs(res.breakpoints[0] - 100) <= 5           # within a few samples of the truth
    assert abs(res.breakpoints[1] - 200) <= 5
    # segment means recover the true levels
    means = [s["mean"] for s in res.segments]
    assert abs(means[0] - 0.0) < 0.3 and abs(means[1] - 5.0) < 0.3 and abs(means[2] + 3.0) < 0.3


def test_pelt_reports_no_breaks_on_a_stable_series():
    res = cp.pelt(_stable())
    assert res.breakpoints == []
    assert len(res.segments) == 1


def test_binseg_with_known_break_count():
    y = _level_shifts()
    res = cp.binseg(y, n_bkps=2)
    assert len(res.breakpoints) == 2
    assert abs(res.breakpoints[0] - 100) <= 5
    assert abs(res.breakpoints[1] - 200) <= 5


def test_cusum_flags_the_unstable_series_and_passes_the_stable_one():
    assert cp.cusum_stability(_level_shifts()).stable is False
    assert cp.cusum_stability(_stable()).stable is True


def test_markov_two_regimes_separate_means():
    # two clearly-separated regimes alternating in blocks
    rng = np.random.default_rng(1)
    blocks = [rng.normal(0.0, 0.5, 60), rng.normal(4.0, 0.5, 60)] * 3
    y = np.concatenate(blocks)
    fit = cp.markov_regimes(y, k_regimes=2)
    lo, hi = sorted(fit.regime_means)
    assert lo < 1.0 and hi > 3.0                        # the two means are recovered
    assert fit.smoothed_probabilities.shape == (len(y), 2)
    # the most-likely path should switch at least a few times (block structure)
    assert int(np.sum(np.diff(fit.most_likely) != 0)) >= 3


def test_report_is_json_ready_and_honest():
    rep = cp.changepoints_report(_level_shifts())
    assert rep["n"] == 300
    assert len(rep["pelt"]["breakpoints"]) == 2
    assert rep["cusum"]["stable"] is False
    assert "markov" in rep                              # either a fit or a recorded error, never a crash
    assert "DOI" in rep["pelt"]["reference"]


def test_nan_safe():
    y = _level_shifts()
    y[7] = np.nan
    y[150] = np.inf
    rep = cp.changepoints_report(y)
    assert rep["n"] == 298
