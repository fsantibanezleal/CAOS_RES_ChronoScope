"""Trend-cycle filters and adaptive decompositions: HP, Baxter-King, Christiano-Fitzgerald, EMD, wavelets.

Where STL/MSTL (see ``seasonality``) split a series by a FIXED period, the tools here separate components by
FREQUENCY BAND (the econometric filters) or fully adaptively (EMD's intrinsic mode functions, the wavelet
scalogram). They answer "what lives at which time scale?", which is how trend, business-cycle, and
high-frequency structure are told apart when no single seasonal period exists.

Methods / references (verified 2026-07-04):
  * Hodrick-Prescott - penalized trend: min sum (y_t - tau_t)^2 + lambda * sum (Delta^2 tau_t)^2. Hodrick &
    Prescott 1997, J. Money, Credit and Banking 29(1):1-16, DOI 10.2307/2953682.
    ``statsmodels.tsa.filters.hp_filter.hpfilter``. Conventional lambda: 1600 quarterly, 129600 monthly,
    6.25 annual.
  * Baxter-King - symmetric finite-MA approximate band-pass isolating cycles of period [low, high];
    loses K observations at each end. Baxter & King 1999, Rev. Econ. & Stat. 81(4):575-593,
    DOI 10.1162/003465399558454. ``statsmodels.tsa.filters.bk_filter.bkfilter``.
  * Christiano-Fitzgerald - asymmetric random-walk band-pass, usable in real time (no end-loss).
    Christiano & Fitzgerald 2003, Int. Economic Review 44(2):435-465, DOI 10.1111/1468-2354.t01-1-00076.
    ``statsmodels.tsa.filters.cf_filter.cffilter``.
  * EMD / EEMD / CEEMDAN - adaptive decomposition into Intrinsic Mode Functions by sifting; EEMD adds
    noise-assisted ensembling against mode mixing; CEEMDAN adds adaptive noise with complete reconstruction.
    Huang et al. 1998, Proc. R. Soc. A 454:903-995, DOI 10.1098/rspa.1998.0193; Wu & Huang 2009,
    Adv. Adaptive Data Analysis 1(1):1-41, DOI 10.1142/S1793536909000047; Torres et al. 2011, ICASSP,
    DOI 10.1109/ICASSP.2011.5947265. Package ``EMD-signal`` (import ``PyEMD``).
  * CWT scalogram - time-scale energy map |CWT(t, s)|^2 via PyWavelets (``pywt.cwt``; NOTE
    ``scipy.signal.cwt`` was deprecated in scipy 1.12 and REMOVED in 1.15). Torrence & Compo 1998,
    Bull. Amer. Meteor. Soc. 79(1):61-78, DOI 10.1175/1520-0477(1998)079<0061:APGTWA>2.0.CO;2.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class FilterResult:
    """A two-way split into a smooth component (trend) and a cyclical component, by a named filter."""

    name: str
    trend: np.ndarray | None     # None for pure band-pass outputs (Baxter-King returns only the cycle)
    cycle: np.ndarray
    reference: str


def hodrick_prescott(x, lamb: float = 1600.0) -> FilterResult:
    """HP filter: penalized smooth trend + cycle. lambda 1600 quarterly / 129600 monthly / 6.25 annual."""
    from statsmodels.tsa.filters.hp_filter import hpfilter

    a = _clean(x)
    cycle, trend = hpfilter(a, lamb=lamb)
    return FilterResult(
        name="HodrickPrescott", trend=np.asarray(trend, dtype=float), cycle=np.asarray(cycle, dtype=float),
        reference="Hodrick & Prescott 1997, JMCB 29(1):1-16, DOI 10.2307/2953682",
    )


def baxter_king(x, low: int = 6, high: int = 32, K: int = 12) -> FilterResult:
    """Baxter-King band-pass for cycles with period in [low, high]; symmetric MA, loses K points per end."""
    from statsmodels.tsa.filters.bk_filter import bkfilter

    a = _clean(x)
    cycle = np.asarray(bkfilter(a, low=low, high=high, K=K), dtype=float).ravel()
    return FilterResult(
        name="BaxterKing", trend=None, cycle=cycle,
        reference="Baxter & King 1999, REStat 81(4):575-593, DOI 10.1162/003465399558454",
    )


def christiano_fitzgerald(x, low: int = 6, high: int = 32) -> FilterResult:
    """Christiano-Fitzgerald asymmetric band-pass; keeps the full sample length (real-time usable)."""
    from statsmodels.tsa.filters.cf_filter import cffilter

    a = _clean(x)
    cycle, trend = cffilter(a, low=low, high=high, drift=True)
    return FilterResult(
        name="ChristianoFitzgerald", trend=np.asarray(trend, dtype=float).ravel(),
        cycle=np.asarray(cycle, dtype=float).ravel(),
        reference="Christiano & Fitzgerald 2003, IER 44(2):435-465, DOI 10.1111/1468-2354.t01-1-00076",
    )


@dataclass(frozen=True)
class EMDResult:
    """Intrinsic Mode Functions (rows of ``imfs``) + the residual trend, from EMD or CEEMDAN sifting."""

    name: str
    imfs: np.ndarray             # (n_imfs, n) - each row one IMF, fastest oscillation first
    residual: np.ndarray         # the final monotone-ish trend left after all IMFs
    reference: str


def emd(x, max_imfs: int = -1, seed: int = 0) -> EMDResult:
    """Plain EMD sifting into IMFs (fastest first) + the residual trend (``get_imfs_and_residue``)."""
    from PyEMD import EMD as _EMD

    a = _clean(x)
    del seed  # plain EMD is deterministic (no noise); the seed applies to EEMD/CEEMDAN only
    engine = _EMD()
    engine.emd(a, max_imf=max_imfs)
    imfs, residue = engine.get_imfs_and_residue()
    return EMDResult(
        name="EMD", imfs=np.asarray(imfs, dtype=float), residual=np.asarray(residue, dtype=float),
        reference="Huang et al. 1998, Proc. R. Soc. A 454:903-995, DOI 10.1098/rspa.1998.0193",
    )


def ceemdan(x, trials: int = 50, seed: int = 0) -> EMDResult:
    """CEEMDAN: noise-assisted EMD with adaptive noise and complete reconstruction (slower, cleaner IMFs)."""
    from PyEMD import CEEMDAN as _CEEMDAN

    a = _clean(x)
    engine = _CEEMDAN(trials=trials)
    engine.noise_seed(seed)
    engine.ceemdan(a)
    imfs, residue = engine.get_imfs_and_residue()
    return EMDResult(
        name="CEEMDAN", imfs=np.asarray(imfs, dtype=float), residual=np.asarray(residue, dtype=float),
        reference="Torres et al. 2011, ICASSP, DOI 10.1109/ICASSP.2011.5947265",
    )


@dataclass(frozen=True)
class Scalogram:
    """|CWT|^2 energy over (scale, time): the standard wavelet time-frequency picture."""

    power: np.ndarray            # (n_scales, n) - |coef|^2
    scales: np.ndarray
    periods: np.ndarray          # the pseudo-period of each scale (in samples, for the given wavelet)
    wavelet: str
    reference: str


def cwt_scalogram(x, wavelet: str = "morl", num_scales: int = 64, max_period_frac: float = 0.5,
                  detrend: bool = True) -> Scalogram:
    """Continuous wavelet transform scalogram via PyWavelets (scipy's cwt is removed since 1.15).

    Scales are geometric from ~2 samples up to ``max_period_frac`` of the series length, converted to
    pseudo-periods so the y-axis reads in samples-per-cycle. Following Torrence & Compo 1998, the series is
    linearly detrended by default: an un-removed trend dumps its energy into the longest scales and swamps
    the cyclic structure the scalogram is meant to reveal (set ``detrend=False`` to see the raw picture).
    """
    import pywt

    a = _clean(x)
    n = len(a)
    if n < 8:
        raise ValueError("series too short for a scalogram")
    if detrend:
        t = np.arange(n, dtype=float)
        slope, intercept = np.polyfit(t, a, 1)
        a = a - (slope * t + intercept)
    max_period = max(4.0, max_period_frac * n)
    fc = pywt.central_frequency(wavelet)
    # period = scale / fc  ->  scale = period * fc
    periods = np.geomspace(2.0, max_period, num_scales)
    scales = periods * fc
    coefs, freqs = pywt.cwt(a, scales, wavelet)
    power = np.abs(coefs) ** 2
    out_periods = 1.0 / freqs
    return Scalogram(
        power=power, scales=np.asarray(scales, dtype=float), periods=np.asarray(out_periods, dtype=float),
        wavelet=wavelet,
        reference="Torrence & Compo 1998, BAMS 79(1):61-78, DOI 10.1175/1520-0477(1998)079<0061:APGTWA>2.0.CO;2",
    )


def filters_report(x, hp_lambda: float = 1600.0, band: tuple[int, int] = (6, 32), max_imfs: int = 6) -> dict:
    """Run the filter panel (HP + CF + EMD + scalogram summary) and return a JSON-ready report.

    Baxter-King is exposed as a function but not baked by default (its K-point end-loss makes panel arrays
    ragged); CF covers the band-pass role in the artifact.
    """
    a = _clean(x)
    hp = hodrick_prescott(a, lamb=hp_lambda)
    cf = christiano_fitzgerald(a, low=band[0], high=band[1])
    e = emd(a, max_imfs=max_imfs)
    sc = cwt_scalogram(a) if len(a) >= 8 else None
    out = {
        "n": int(len(a)),
        "hp": {"lambda": hp_lambda, "trend": hp.trend.tolist(), "cycle": hp.cycle.tolist(),
               "reference": hp.reference},
        "cf": {"band": list(band), "cycle": cf.cycle.tolist(), "reference": cf.reference},
        "emd": {"n_imfs": int(e.imfs.shape[0]), "imfs": e.imfs.tolist(), "residual": e.residual.tolist(),
                "reference": e.reference},
    }
    if sc is not None:
        # bake a compact scalogram summary: per-scale total energy + the dominant period by energy
        energy = sc.power.sum(axis=1)
        out["scalogram"] = {
            "wavelet": sc.wavelet,
            "periods": sc.periods.tolist(),
            "energy_by_period": energy.tolist(),
            "dominant_period": float(sc.periods[int(np.argmax(energy))]),
            "reference": sc.reference,
        }
    return out
