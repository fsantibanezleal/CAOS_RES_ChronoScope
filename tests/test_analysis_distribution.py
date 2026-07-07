"""Distribution + complexity tests: normality verdicts, moments, entropy ordering (regular vs random)."""
import numpy as np

from chronoscopelab.analysis import distribution as di


def _normal(n=1000, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def _heavy_tailed(n=1000, seed=0):
    return np.random.default_rng(seed).standard_t(df=3, size=n)   # heavy tails, excess kurtosis > 0


def _skewed(n=1000, seed=0):
    return np.random.default_rng(seed).exponential(1.0, n)        # right-skewed


def _sine(n=500):
    return np.sin(np.arange(n) * 2 * np.pi / 20)                  # perfectly regular -> low entropy


def test_summary_flags_normal_and_rejects_heavy_tailed():
    assert di.summary(_normal()).normal is True
    ht = di.summary(_heavy_tailed())
    assert ht.normal is False
    assert ht.kurtosis_excess > 1.0                              # heavy tails


def test_summary_detects_skew():
    s = di.summary(_skewed())
    assert s.skewness > 1.0                                       # exponential is strongly right-skewed
    assert s.normal is False


def test_kde_and_qq_payloads():
    kde = di.kde_curve(_normal(), num=64)
    assert len(kde["grid"]) == 64 and len(kde["density"]) == 64
    qq = di.qq_points(_normal())
    assert len(qq["theoretical"]) == len(qq["sample"])
    assert qq["r"] > 0.98                                         # normal data lies on the Q-Q line


def test_entropy_orders_regular_below_random():
    reg = di.complexity(_sine())
    rnd = di.complexity(_normal())
    # a clean sine is far more predictable than white noise on every entropy measure
    assert reg.sample_entropy < rnd.sample_entropy
    assert reg.permutation_entropy < rnd.permutation_entropy
    assert reg.spectral_entropy < rnd.spectral_entropy


def test_permutation_and_spectral_entropy_are_normalized():
    c = di.complexity(_normal())
    assert 0.0 <= c.permutation_entropy <= 1.0
    assert 0.0 <= c.spectral_entropy <= 1.0
    assert c.permutation_entropy > 0.9                           # white noise ~ maximal ordinal entropy


def test_bds_flags_iid_noise_and_rejects_structure():
    assert di.complexity(_normal()).iid is True                  # white noise is i.i.d.
    assert di.complexity(_sine()).iid is False                   # a deterministic sine is not i.i.d.


def test_catch22_is_honest_when_unavailable():
    res = di.catch22_features(_normal())
    # either genuine features (if pycatch22 is built) or an explicit recorded-unavailable marker - never faked
    assert "available" in res
    if res["available"]:
        assert len(res["features"]) >= 22
    else:
        assert "reason" in res and "DOI" in res["reference"]


def test_report_is_json_ready_and_complete():
    rep = di.distribution_report(_normal())
    assert rep["n"] == 1000
    assert rep["summary"]["normal"] is True
    assert "grid" in rep["kde"] and "theoretical" in rep["qq"]
    assert 0.0 <= rep["complexity"]["permutation_entropy"] <= 1.0
    assert "catch22" in rep and "DOI" in rep["summary"]["reference"]


def test_nan_safe():
    y = _normal()
    y[3] = np.nan
    y[500] = np.inf
    rep = di.distribution_report(y)
    assert rep["n"] == 998
