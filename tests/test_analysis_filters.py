"""Filter toolkit tests: ground-truth checks on trend+cycle composites, EMD reconstruction, scalogram period."""
import numpy as np

from chronoscopelab.analysis import filters as fl


def _trend_plus_cycle(n=240, cycle_period=16, seed=0):
    """A slow quadratic trend plus a fast sinusoidal cycle plus small noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    trend = 0.001 * (t - n / 2) ** 2
    cycle = 3.0 * np.sin(2 * np.pi * t / cycle_period)
    return trend + cycle + rng.normal(0, 0.2, n), trend, cycle


def test_hp_recovers_the_smooth_trend():
    y, trend, _cycle = _trend_plus_cycle()
    res = fl.hodrick_prescott(y, lamb=1600.0)
    assert res.trend is not None and len(res.trend) == len(y)
    # the HP trend should be far closer to the true trend than the raw series is
    err_hp = float(np.mean((res.trend - trend) ** 2))
    err_raw = float(np.mean((y - trend) ** 2))
    assert err_hp < 0.5 * err_raw
    # trend + cycle reconstructs the series exactly (two-way split)
    assert np.allclose(res.trend + res.cycle, y, atol=1e-8)


def test_bk_bandpass_extracts_the_cycle_band():
    y, _trend, _cycle = _trend_plus_cycle(cycle_period=16)
    res = fl.baxter_king(y, low=8, high=32, K=12)
    # BK loses K points at each end
    assert len(res.cycle) == len(y) - 2 * 12
    # the extracted band should oscillate with meaningful amplitude
    assert np.std(res.cycle) > 0.5


def test_cf_keeps_full_length_and_finds_the_cycle():
    y, _trend, cycle = _trend_plus_cycle(cycle_period=16)
    res = fl.christiano_fitzgerald(y, low=8, high=32)
    assert len(res.cycle) == len(y)
    # CF cycle should correlate strongly with the true cycle
    c = np.corrcoef(res.cycle, cycle)[0, 1]
    assert c > 0.8


def test_emd_reconstruction_is_complete():
    y, _t, _c = _trend_plus_cycle()
    res = fl.emd(y, max_imfs=6)
    recon = res.imfs.sum(axis=0) + res.residual
    assert np.allclose(recon, y, atol=1e-8)          # IMFs + residue == the series (complete sifting)
    assert res.imfs.shape[0] >= 2                     # at least a fast IMF and a slower one


def test_emd_first_imf_is_the_fastest():
    y, _t, _c = _trend_plus_cycle()
    res = fl.emd(y, max_imfs=6)
    # zero-crossing count decreases from the first IMF to the last (fastest first)
    def crossings(v):
        return int(np.sum(np.diff(np.signbit(v)) != 0))
    assert crossings(res.imfs[0]) > crossings(res.imfs[-1])


def test_scalogram_finds_the_cycle_period():
    # ground truth without a polynomial trend: the scalogram's energy-dominant scale IS the cycle period.
    # (with a strong trend, long-scale energy legitimately dominates - that caveat is documented.)
    rng = np.random.default_rng(0)
    t = np.arange(256, dtype=float)
    y = 3.0 * np.sin(2 * np.pi * t / 16) + rng.normal(0, 0.2, 256)
    sc = fl.cwt_scalogram(y, num_scales=48)
    assert sc.power.shape == (48, 256)
    energy = sc.power.sum(axis=1)
    dominant = float(sc.periods[int(np.argmax(energy))])
    assert 10.0 < dominant < 26.0                     # near the true 16-sample period


def test_report_is_json_ready_and_complete():
    y, _t, _c = _trend_plus_cycle()
    rep = fl.filters_report(y, hp_lambda=1600.0, band=(8, 32), max_imfs=5)
    assert rep["n"] == 240
    assert len(rep["hp"]["trend"]) == 240
    assert len(rep["cf"]["cycle"]) == 240
    assert rep["emd"]["n_imfs"] >= 2
    assert "scalogram" in rep and rep["scalogram"]["dominant_period"] > 0
    for key in ("hp", "cf", "emd"):
        assert "DOI" in rep[key]["reference"]


def test_nan_safe():
    y, _t, _c = _trend_plus_cycle()
    y[3] = np.nan
    y[77] = np.inf
    rep = fl.filters_report(y)
    assert rep["n"] == 238                            # non-finite dropped, not crashing
