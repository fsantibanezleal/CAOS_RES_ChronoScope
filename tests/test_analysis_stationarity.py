"""Stationarity toolkit tests: opposite-null polarity, unit-root vs stationary verdicts, FPP3 differencing.

Uses seeded synthetic series with a KNOWN answer (white noise = stationary; a random walk = unit root that
becomes stationary after one difference; a strong seasonal series = high seasonal strength), so each test
checks the tool against ground truth, not against itself.
"""
import numpy as np

from chronoscopelab.analysis import stationarity as st


def _white_noise(n=300, seed=0):
    return np.random.default_rng(seed).normal(0.0, 1.0, n)


def _random_walk(n=300, seed=0):
    return np.cumsum(np.random.default_rng(seed).normal(0.0, 1.0, n))


def _seasonal(n=288, m=12, seed=0):
    rng = np.random.default_rng(seed)
    return 50 + 10 * np.sin(np.arange(n) * 2 * np.pi / m) + rng.normal(0, 0.5, n)


def test_opposite_nulls_are_labelled():
    y = _white_noise()
    assert "unit root" in st.adf(y).null
    assert st.kpss(y).null == "stationary"


def test_white_noise_is_stationary():
    y = _white_noise()
    assert st.adf(y).stationary is True          # ADF rejects the unit root
    assert st.kpss(y).stationary is True          # KPSS does not reject stationarity
    assert st.ndiffs(y) == 0                       # no differencing needed


def test_random_walk_has_a_unit_root():
    y = _random_walk()
    assert st.adf(y).stationary is False           # ADF cannot reject the unit root
    assert st.kpss(y).stationary is False          # KPSS rejects stationarity
    assert st.ndiffs(y) >= 1                        # needs at least one difference


def test_differencing_recovers_stationarity():
    y = _random_walk()
    dy = np.diff(y)
    assert st.adf(dy).stationary is True            # the first difference is white-noise-like
    assert st.ndiffs(y) == 1                         # FPP3 KPSS-sequential recovers exactly one


def test_phillips_perron_and_dfgls_agree_on_the_random_walk():
    y = _random_walk()
    assert st.phillips_perron(y).stationary is False
    assert st.dfgls(y).stationary is False


def test_combined_verdict_matches_the_quadrant():
    assert st.combined_verdict(st.adf(_white_noise()), st.kpss(_white_noise())).startswith("stationary")
    rw = _random_walk()
    assert st.combined_verdict(st.adf(rw), st.kpss(rw)).startswith("non-stationary")


def test_seasonal_strength_separates_seasonal_from_noise():
    assert st.seasonal_strength(_seasonal(), period=12) > 0.6      # strong deterministic seasonality
    assert st.seasonal_strength(_white_noise(), period=12) < 0.3   # no seasonality
    assert st.seasonal_strength(_white_noise(20), period=12) == 0.0  # too short for two periods


def test_nsdiffs_flags_strong_seasonality():
    assert st.nsdiffs(_seasonal(), period=12) == 1
    assert st.nsdiffs(_white_noise(), period=12) == 0


def test_report_is_json_ready_and_complete():
    rep = st.stationarity_report(_seasonal(), period=12)
    assert rep["n"] == 288
    names = {t["name"] for t in rep["tests"]}
    assert names == {"ADF", "KPSS", "PhillipsPerron", "DFGLS", "ZivotAndrews"}
    assert "combined_verdict" in rep and "recommended_d" in rep
    assert "seasonal_strength" in rep and "recommended_D" in rep
    for t in rep["tests"]:                                # every test carries its primary reference
        assert "DOI" in t["reference"]


def test_nan_safe():
    y = _random_walk()
    y[5] = np.nan
    y[100] = np.inf
    assert st.ndiffs(y) >= 1                              # non-finite points are dropped, not crashing
