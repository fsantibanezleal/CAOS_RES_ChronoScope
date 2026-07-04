"""Change-point and regime analysis: PELT, Binary Segmentation, CUSUM, Markov-switching regimes.

A structural break (a shift in mean, variance, or dynamics) violates the "one process generated all of it"
assumption every fitted model makes. This module locates WHERE a series changes (offline change-point
detection), tests WHETHER parameters are stable (CUSUM), and models WHICH regime each point belongs to
(Markov switching). Drift, level shifts, and regime changes are exactly the structures that fool both the
classical ladder and a zero-shot foundation model, so the case narratives lean on this panel.

Methods / references (verified 2026-07-04):
  * PELT - exact penalized change-point search in expected linear time via pruning. Killick, Fearnhead &
    Eckley 2012, JASA 107(500):1590-1598, DOI 10.1080/01621459.2012.737745. ``ruptures.Pelt``.
  * Binary Segmentation - greedy sequential single-break search, O(n log n), approximate. ``ruptures.Binseg``.
    Library reference: Truong, Oudre & Vayatis 2020, Signal Processing 167:107299,
    DOI 10.1016/j.sigpro.2019.107299 (the ruptures review, its recommended citation).
  * OLS-CUSUM - parameter-stability test on cumulative OLS residuals against Brownian-bridge bounds.
    Brown, Durbin & Evans 1975 lineage; implemented by
    ``statsmodels.stats.diagnostic.breaks_cusumolsresid``.
  * Markov switching - Hamilton 1989, Econometrica 57(2):357-384 (JSTOR 1912559): latent K-regime Markov
    chain over mean/variance; smoothed regime probabilities per point.
    ``statsmodels.tsa.regime_switching.markov_regression.MarkovRegression``.

NOTE: the Chow test (single KNOWN break date) is deliberately not wrapped - it is NOT first-class in
statsmodels' public API (verified); PELT/Binseg + Zivot-Andrews (stationarity page) cover the unknown-date
problem the product actually has. BOCPD (Adams & MacKay 2007) is an online method; it belongs to the
streaming lane (preqts) and is recorded in the plan, not duplicated here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class ChangePoints:
    """Detected break indices (each the FIRST index of a new segment; excludes 0 and n) + segment stats."""

    name: str
    breakpoints: list[int]
    segments: list[dict]         # per segment: {start, end, mean, std}
    model: str                   # the cost model used ("l2" mean-shift, "normal" mean+var, "rbf" generic)
    penalty: float | None
    reference: str


def _segments(a: np.ndarray, bkps_first_index: list[int]) -> list[dict]:
    bounds = [0, *bkps_first_index, len(a)]
    out = []
    for s, e in zip(bounds[:-1], bounds[1:]):
        seg = a[s:e]
        out.append({"start": int(s), "end": int(e), "mean": float(np.mean(seg)), "std": float(np.std(seg))})
    return out


def pelt(x, model: str = "l2", penalty: float | None = None, min_size: int = 5) -> ChangePoints:
    """PELT with a BIC-style default penalty (2 * sigma^2 * log n for the l2 cost when none is given)."""
    import ruptures as rpt

    a = _clean(x)
    n = len(a)
    if penalty is None:
        sigma2 = float(np.var(np.diff(a))) / 2.0 or 1e-8   # robust noise-variance proxy
        penalty = 2.0 * sigma2 * np.log(max(n, 2))
    algo = rpt.Pelt(model=model, min_size=min_size).fit(a)
    ends = algo.predict(pen=penalty)                        # ruptures returns segment END indices incl. n
    bkps = [int(b) for b in ends if b < n]
    return ChangePoints(
        name="PELT", breakpoints=bkps, segments=_segments(a, bkps), model=model, penalty=float(penalty),
        reference="Killick, Fearnhead & Eckley 2012, JASA 107(500):1590-1598, DOI 10.1080/01621459.2012.737745",
    )


def binseg(x, n_bkps: int, model: str = "l2", min_size: int = 5) -> ChangePoints:
    """Binary segmentation for a KNOWN number of breaks (fast, approximate)."""
    import ruptures as rpt

    a = _clean(x)
    algo = rpt.Binseg(model=model, min_size=min_size).fit(a)
    ends = algo.predict(n_bkps=n_bkps)
    bkps = [int(b) for b in ends if b < len(a)]
    return ChangePoints(
        name="BinSeg", breakpoints=bkps, segments=_segments(a, bkps), model=model, penalty=None,
        reference="Truong, Oudre & Vayatis 2020, Signal Processing 167:107299, DOI 10.1016/j.sigpro.2019.107299",
    )


@dataclass(frozen=True)
class CusumResult:
    """OLS-CUSUM parameter-stability test: sup |cumulative scaled OLS residual| vs Brownian-bridge bounds."""

    stat: float
    pvalue: float
    stable: bool
    alpha: float
    reference: str


def cusum_stability(x, alpha: float = 0.05) -> CusumResult:
    """OLS-CUSUM on the series demeaned by OLS-on-constant: rejects when the mean is unstable over time."""
    from statsmodels.stats.diagnostic import breaks_cusumolsresid

    a = _clean(x)
    resid = a - a.mean()                                   # OLS residuals of y ~ const
    stat, pvalue, _crit = breaks_cusumolsresid(resid)
    return CusumResult(
        stat=float(stat), pvalue=float(pvalue), stable=bool(pvalue >= alpha), alpha=alpha,
        reference="Brown, Durbin & Evans 1975 lineage; statsmodels breaks_cusumolsresid (Ploberger-Kramer OLS-CUSUM)",
    )


@dataclass(frozen=True)
class RegimeFit:
    """A fitted K-regime Markov-switching mean(+variance) model with per-point smoothed probabilities."""

    k_regimes: int
    regime_means: list[float]
    smoothed_probabilities: np.ndarray   # (n, k) - P(regime j | full sample) per point
    most_likely: np.ndarray              # (n,) argmax regime per point
    transition_matrix: list[list[float]]
    reference: str


def markov_regimes(x, k_regimes: int = 2, switching_variance: bool = True) -> RegimeFit:
    """Hamilton Markov-switching regression (mean per regime; optionally variance per regime)."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    a = _clean(x)
    model = MarkovRegression(a, k_regimes=k_regimes, trend="c", switching_variance=switching_variance)
    res = model.fit(disp=False)
    smoothed = np.asarray(res.smoothed_marginal_probabilities)
    if smoothed.ndim == 1:
        smoothed = smoothed.reshape(-1, k_regimes)
    # Pull each regime's mean by its named parameter (the leading params are transition probabilities).
    names = list(res.model.param_names)
    means = [float(res.params[names.index(f"const[{j}]")]) for j in range(k_regimes)]
    tm = np.asarray(res.regime_transition)[..., 0] if hasattr(res, "regime_transition") else np.full((k_regimes, k_regimes), np.nan)
    return RegimeFit(
        k_regimes=k_regimes, regime_means=means, smoothed_probabilities=smoothed,
        most_likely=np.asarray(smoothed.argmax(axis=1)),
        transition_matrix=[[float(v) for v in row] for row in np.asarray(tm).reshape(k_regimes, k_regimes)],
        reference="Hamilton 1989, Econometrica 57(2):357-384, JSTOR 1912559; statsmodels MarkovRegression",
    )


def changepoints_report(x, k_regimes: int = 2) -> dict:
    """Run the change-point panel (PELT + CUSUM + Markov regimes) and return a JSON-ready report."""
    a = _clean(x)
    p = pelt(a)
    c = cusum_stability(a)
    out = {
        "n": int(len(a)),
        "pelt": {"breakpoints": p.breakpoints, "segments": p.segments, "model": p.model,
                 "penalty": p.penalty, "reference": p.reference},
        "cusum": {"stat": c.stat, "pvalue": c.pvalue, "stable": c.stable, "reference": c.reference},
    }
    # Markov regimes can fail to converge on degenerate series; report honestly instead of crashing.
    try:
        r = markov_regimes(a, k_regimes=k_regimes)
        out["markov"] = {
            "k_regimes": r.k_regimes, "regime_means": r.regime_means,
            "most_likely": r.most_likely.tolist(), "transition_matrix": r.transition_matrix,
            "reference": r.reference,
        }
    except Exception as exc:  # noqa: BLE001 - baked artifact must record the failure, not die
        out["markov"] = {"error": f"{type(exc).__name__}: {exc}"}
    return out
