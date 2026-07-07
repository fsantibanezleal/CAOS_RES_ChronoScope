"""Volatility toolkit tests: ARCH detection, GARCH persistence, Box-Cox variance stabilization, Guerrero."""
import numpy as np

from chronoscopelab.analysis import volatility as vo


def _garch_series(n=1500, omega=0.1, alpha=0.15, beta=0.80, seed=0):
    """Simulate a genuine GARCH(1,1): variance clusters, so ARCH-LM should fire."""
    rng = np.random.default_rng(seed)
    eps = np.empty(n)
    sig2 = np.empty(n)
    sig2[0] = omega / (1 - alpha - beta)
    eps[0] = np.sqrt(sig2[0]) * rng.normal()
    for t in range(1, n):
        sig2[t] = omega + alpha * eps[t - 1] ** 2 + beta * sig2[t - 1]
        eps[t] = np.sqrt(sig2[t]) * rng.normal()
    return eps


def _homoscedastic(n=1500, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def _multiplicative_growth(n=240, m=12, seed=0):
    """A series whose seasonal amplitude grows with the level -> Box-Cox should help."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    level = 10 + 0.1 * t
    return level * (1 + 0.3 * np.sin(2 * np.pi * t / m)) + rng.normal(0, 0.5, n)


def test_arch_lm_detects_clustering_and_clears_homoscedastic():
    assert vo.arch_lm(_garch_series(), nlags=12).has_arch is True
    assert vo.arch_lm(_homoscedastic(), nlags=12).has_arch is False


def test_garch_recovers_high_persistence():
    g = vo.garch(_garch_series(alpha=0.15, beta=0.80), p=1, q=1)
    # true persistence alpha+beta = 0.95; the fit should land in a plausible high-persistence band
    assert 0.80 < g.persistence < 1.02
    assert g.conditional_volatility.shape[0] == len(_garch_series())
    assert np.all(g.conditional_volatility > 0)


def test_boxcox_mle_stabilizes_variance():
    y = _multiplicative_growth()
    bc = vo.box_cox(y, method="mle")
    # after transform, the spread of the second half vs first half should be more similar (variance stabilized)
    raw_ratio = np.std(y[len(y) // 2:]) / np.std(y[: len(y) // 2])
    tr = bc.transformed
    tr_ratio = np.std(tr[len(tr) // 2:]) / np.std(tr[: len(tr) // 2])
    assert abs(tr_ratio - 1.0) <= abs(raw_ratio - 1.0)
    assert -2.0 <= bc.lam <= 2.0


def test_boxcox_guerrero_needs_and_uses_season():
    y = _multiplicative_growth(m=12)
    bc = vo.box_cox(y, method="guerrero", season_length=12)
    assert bc.method == "guerrero"
    assert -1.0 <= bc.lam <= 2.0


def test_boxcox_handles_nonpositive_with_a_recorded_shift():
    y = np.array([-2.0, 0.0, 1.0, 3.0, 5.0, 2.0, 4.0, 6.0])
    bc = vo.box_cox(y, method="log")
    assert bc.shift > 0                                  # shifted to positivity
    assert np.all(np.isfinite(bc.transformed))


def test_report_skips_garch_when_no_arch():
    rep = vo.volatility_report(_homoscedastic())
    assert rep["arch_lm"]["has_arch"] is False
    assert "skipped" in rep["garch"]


def test_report_fits_garch_when_arch_present():
    rep = vo.volatility_report(_garch_series(), arch_lags=12)
    assert rep["arch_lm"]["has_arch"] is True
    assert "params" in rep["garch"] and rep["garch"]["persistence"] > 0.5
    assert "DOI" in rep["arch_lm"]["reference"]


def test_nan_safe():
    y = _garch_series()
    y[3] = np.nan
    y[500] = np.inf
    rep = vo.volatility_report(y)
    assert rep["n"] == len(y) - 2
