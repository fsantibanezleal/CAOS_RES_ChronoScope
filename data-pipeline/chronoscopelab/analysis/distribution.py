"""Distribution, normality, and entropy/complexity: the value-distribution and predictability diagnostics.

Two facets of "what kind of values does this series take, and how predictable is its pattern?": (1) the
DISTRIBUTION of the values (shape, tails, normality) and (2) the COMPLEXITY of the ordering (entropy measures
that quantify regularity vs randomness, and a nonlinearity test). Together they answer whether Gaussian
assumptions hold and how much exploitable structure the sequence carries.

Methods / references (verified 2026-07-04):
  * Summary moments - mean, variance, skewness (asymmetry), kurtosis (tail-heaviness). Standard.
  * KDE - Gaussian kernel density estimate. Parzen 1962, Ann. Math. Stat. 33(3):1065-1076,
    DOI 10.1214/aoms/1177704472. ``scipy.stats.gaussian_kde``.
  * Q-Q plot - sample vs theoretical (normal) quantiles. Wilk & Gnanadesikan 1968, Biometrika 55(1):1-17,
    DOI 10.1093/biomet/55.1.1. ``scipy.stats.probplot``.
  * Jarque-Bera - normality from skew+kurtosis; large-sample. Jarque & Bera 1980, Economics Letters
    6(3):255-259, DOI 10.1016/0165-1765(80)90024-5. ``scipy.stats.jarque_bera``.
  * Shapiro-Wilk - most powerful normality test for small/moderate n. Shapiro & Wilk 1965, Biometrika
    52(3-4):591-611, DOI 10.1093/biomet/52.3-4.591. ``scipy.stats.shapiro``.
  * Sample entropy - bias-corrected regularity (lower = more predictable). Richman & Moorman 2000,
    Am. J. Physiol. 278(6):H2039-H2049, DOI 10.1152/ajpheart.2000.278.6.H2039. ``antropy.sample_entropy``.
  * Permutation entropy - ordinal-pattern entropy, noise-robust. Bandt & Pompe 2002, PRL 88:174102,
    DOI 10.1103/PhysRevLett.88.174102. ``antropy.perm_entropy``.
  * Spectral entropy - Shannon entropy of the normalized PSD (flat spectrum = high). ``antropy.spectral_entropy``.
  * BDS test - i.i.d. vs hidden nonlinear structure via the correlation integral. Broock, Scheinkman,
    Dechert & LeBaron 1996, Econometric Reviews 15(3):197-235, DOI 10.1080/07474939608800353.
    ``statsmodels.tsa.stattools.bds``.
  * catch22 - 22 canonical features (Lubba et al. 2019, DOI 10.1007/s10618-019-00647-x). OPTIONAL: pycatch22
    needs a C toolchain to build; when unavailable the report records that honestly rather than faking it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class DistributionSummary:
    """Moments + normality verdicts + a KDE/Q-Q payload for the distribution panel."""

    n: int
    mean: float
    std: float
    skewness: float
    kurtosis_excess: float       # excess kurtosis (0 = normal); >0 heavy-tailed
    jarque_bera_stat: float
    jarque_bera_pvalue: float
    shapiro_stat: float | None
    shapiro_pvalue: float | None
    normal: bool                 # combined verdict at alpha (both tests non-significant where applicable)
    reference: str


def summary(x, alpha: float = 0.05) -> DistributionSummary:
    """Moments + Jarque-Bera + Shapiro-Wilk (n <= 5000) with a combined normality verdict."""
    from scipy import stats

    a = _clean(x)
    n = len(a)
    skew = float(stats.skew(a))
    kurt = float(stats.kurtosis(a, fisher=True))         # excess kurtosis
    jb_stat, jb_p = stats.jarque_bera(a)
    sh_stat, sh_p = (None, None)
    if 3 <= n <= 5000:                                    # Shapiro is defined/reliable in this range
        sh = stats.shapiro(a)
        sh_stat, sh_p = float(sh[0]), float(sh[1])
    normal = bool(jb_p >= alpha and (sh_p is None or sh_p >= alpha))
    return DistributionSummary(
        n=n, mean=float(np.mean(a)), std=float(np.std(a)), skewness=skew, kurtosis_excess=kurt,
        jarque_bera_stat=float(jb_stat), jarque_bera_pvalue=float(jb_p),
        shapiro_stat=sh_stat, shapiro_pvalue=sh_p, normal=normal,
        reference="Jarque & Bera 1980, DOI 10.1016/0165-1765(80)90024-5; Shapiro & Wilk 1965, DOI 10.1093/biomet/52.3-4.591",
    )


def kde_curve(x, num: int = 100) -> dict:
    """Gaussian KDE evaluated on a grid, for the histogram+density panel (Parzen 1962)."""
    from scipy import stats

    a = _clean(x)
    kde = stats.gaussian_kde(a)
    grid = np.linspace(float(a.min()), float(a.max()), num)
    return {"grid": grid.tolist(), "density": kde(grid).tolist(),
            "reference": "Parzen 1962, Ann. Math. Stat. 33(3):1065-1076, DOI 10.1214/aoms/1177704472"}


def qq_points(x) -> dict:
    """Normal Q-Q points (theoretical vs ordered sample quantiles) + the fitted reference line."""
    from scipy import stats

    a = _clean(x)
    (osm, osr), (slope, intercept, r) = stats.probplot(a, dist="norm")
    return {"theoretical": osm.tolist(), "sample": osr.tolist(),
            "slope": float(slope), "intercept": float(intercept), "r": float(r),
            "reference": "Wilk & Gnanadesikan 1968, Biometrika 55(1):1-17, DOI 10.1093/biomet/55.1.1"}


@dataclass(frozen=True)
class ComplexitySummary:
    """Entropy/complexity measures + the BDS nonlinearity verdict (predictability of the ordering)."""

    sample_entropy: float
    permutation_entropy: float   # normalized to [0, 1]
    spectral_entropy: float      # normalized to [0, 1]
    bds_stat: float | None
    bds_pvalue: float | None
    iid: bool | None             # BDS verdict: True if not rejected (behaves i.i.d.)
    reference: str


def complexity(x, order: int = 3, bds_dim: int = 2, alpha: float = 0.05) -> ComplexitySummary:
    """Sample/permutation/spectral entropy + the BDS i.i.d.-vs-nonlinear test."""
    import antropy as ant
    from statsmodels.tsa.stattools import bds as _bds

    a = _clean(x)
    samp = float(ant.sample_entropy(a))
    perm = float(ant.perm_entropy(a, order=order, normalize=True))
    spec = float(ant.spectral_entropy(a, sf=1.0, method="welch", normalize=True))
    bds_stat = bds_p = None
    iid = None
    if len(a) >= 20:
        try:
            stat, pval = _bds(a, max_dim=bds_dim)
            bds_stat = float(np.ravel(stat)[-1])          # statistic at the largest embedding dim
            bds_p = float(np.ravel(pval)[-1])
            iid = bool(bds_p >= alpha)
        except Exception:  # noqa: BLE001 - BDS can fail on degenerate input; record as unavailable
            pass
    return ComplexitySummary(
        sample_entropy=samp, permutation_entropy=perm, spectral_entropy=spec,
        bds_stat=bds_stat, bds_pvalue=bds_p, iid=iid,
        reference="Richman & Moorman 2000, DOI 10.1152/ajpheart.2000.278.6.H2039; Bandt & Pompe 2002, DOI 10.1103/PhysRevLett.88.174102; BDS: Broock et al. 1996, DOI 10.1080/07474939608800353",
    )


def catch22_features(x) -> dict:
    """The 22 canonical catch22 features (Lubba et al. 2019). OPTIONAL: needs a compiled pycatch22.

    Returns a dict of {feature_name: value} when pycatch22 is installed, else a recorded-unavailable marker.
    We never fabricate these values: if the C extension is not built, the report says so.
    """
    try:
        import pycatch22
    except ImportError:
        return {"available": False,
                "reason": "pycatch22 not installed (requires a C toolchain to build the extension)",
                "reference": "Lubba et al. 2019, Data Min. Knowl. Disc. 33(6):1821-1852, DOI 10.1007/s10618-019-00647-x"}
    a = _clean(x)
    res = pycatch22.catch22_all(a.tolist(), catch24=True)
    return {"available": True,
            "features": dict(zip(res["names"], [float(v) for v in res["values"]])),
            "reference": "Lubba et al. 2019, DOI 10.1007/s10618-019-00647-x"}


def distribution_report(x, order: int = 3) -> dict:
    """Run the distribution + complexity panel and return a JSON-ready report."""
    a = _clean(x)
    s = summary(a)
    c = complexity(a, order=order)
    return {
        "n": int(len(a)),
        "summary": {"mean": s.mean, "std": s.std, "skewness": s.skewness,
                    "kurtosis_excess": s.kurtosis_excess, "jarque_bera_pvalue": s.jarque_bera_pvalue,
                    "shapiro_pvalue": s.shapiro_pvalue, "normal": s.normal, "reference": s.reference},
        "kde": kde_curve(a),
        "qq": qq_points(a),
        "complexity": {"sample_entropy": c.sample_entropy, "permutation_entropy": c.permutation_entropy,
                       "spectral_entropy": c.spectral_entropy, "bds_pvalue": c.bds_pvalue, "iid": c.iid,
                       "reference": c.reference},
        "catch22": catch22_features(a),
    }
