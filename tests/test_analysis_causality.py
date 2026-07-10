"""Causality/cointegration tests: known lead/lag, directional Granger, cointegrated vs independent pairs."""
import numpy as np

from chronoscopelab.analysis import causality as ca


def _leading_pair(n=400, lead=3, seed=0):
    """x leads y by `lead` steps: y_t = x_{t-lead} + small noise."""
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(size=n + lead))
    y = x[:-lead] + rng.normal(0, 0.3, n)
    return x[lead:], y


def _independent_walks(n=400, seed=0):
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(size=n)), np.cumsum(rng.normal(size=n))


def _cointegrated(n=400, seed=0):
    """Two I(1) series sharing a stochastic trend -> a stationary spread (cointegrated)."""
    rng = np.random.default_rng(seed)
    common = np.cumsum(rng.normal(size=n))
    x = common + rng.normal(0, 0.5, n)
    y = 0.8 * common + rng.normal(0, 0.5, n)
    return x, y


def test_ccf_finds_the_lead():
    x, y = _leading_pair(lead=3)
    cc = ca.cross_correlation(x, y, max_lag=20)
    assert cc.peak_lag > 0                                # x leads y (positive lag)
    assert abs(cc.peak_value) > cc.band                  # the peak is significant


def test_granger_is_directional():
    x, y = _leading_pair(lead=2)
    g_fwd = ca.granger_causality(x, y, max_lag=5)         # x -> y should hold
    g_bwd = ca.granger_causality(y, x, max_lag=5)         # y -> x should be weaker
    assert g_fwd.causes is True
    assert g_fwd.pvalues[g_fwd.best_lag] < g_bwd.pvalues[g_bwd.best_lag]


def test_cointegration_detects_shared_trend():
    x, y = _cointegrated()
    res = ca.cointegration(x, y)
    assert res.eg_cointegrated is True
    assert res.johansen_rank_at_least_1 is True
    assert res.both_i1 is True                            # precondition satisfied


def test_independent_walks_not_cointegrated():
    x, y = _independent_walks()
    res = ca.cointegration(x, y)
    # two independent random walks should not be cointegrated (Engle-Granger not significant)
    assert res.eg_cointegrated is False


def test_report_is_json_ready_and_complete():
    x, y = _cointegrated()
    rep = ca.causality_report(x, y, max_lag=5)
    assert rep["n"] == 400
    assert "peak_lag" in rep["ccf"] and rep["ccf"]["lead"] in ("x leads y", "y leads x", "synchronous")
    assert "x_causes_y" in rep["granger"] and "y_causes_x" in rep["granger"]
    assert rep["cointegration"]["valid"] is True         # both I(1) -> cointegration is meaningful
    assert "DOI" in rep["granger"]["reference"]
    assert "DOI" in rep["cointegration"]["reference"]


def test_cointegration_invalid_on_stationary_series():
    rng = np.random.default_rng(1)
    x = rng.normal(size=400)                              # already stationary (not I(1))
    y = rng.normal(size=400)
    rep = ca.causality_report(x, y)
    assert rep["cointegration"]["both_series_I1"] is False
    assert rep["cointegration"]["valid"] is False         # cointegration is not meaningful here


def test_nan_safe():
    x, y = _cointegrated()
    x[3] = np.nan
    y[100] = np.inf
    rep = ca.causality_report(x, y)
    assert rep["n"] < 400                                 # non-finite pairs dropped, not crashing
