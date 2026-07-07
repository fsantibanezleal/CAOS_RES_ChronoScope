"""Fractal, multifractal, and long-memory analysis: Hurst, DFA, MF-DFA, fractal dimension, DCCA.

The self-affine / scaling structure of a series: does it have long-range dependence (persistent memory)? Is a
single scaling exponent enough (monofractal) or does it need a spectrum (multifractal)? How rough is it? For
the forecastability story this is decisive: a Hurst exponent far from 0.5 signals exploitable structure, a
wide multifractal spectrum signals scale-dependent burstiness, and both temper naive "it's just noise"
conclusions. Each method delegates to its authoritative library and carries the primary reference.

Methods / references (verified 2026-07-04; dossiers research-hurst-dfa / research-multifractal /
research-fractal-dimension / research-cross-series-modeling-honesty):
  * Hurst via R/S - Hurst 1951, Trans. ASCE 116:770-799. H<0.5 anti-persistent, =0.5 random walk, >0.5
    persistent. ``hurst.compute_Hc`` (Anis-Lloyd corrected) and ``nolds.hurst_rs``.
  * DFA - Peng et al. 1994, Phys. Rev. E 49:1685-1689 (detrended fluctuation analysis). Scaling exponent
    alpha (fGn: H=alpha; fBm: H=alpha-1; alpha~1 = 1/f noise). ``nolds.dfa`` / ``antropy.detrended_fluctuation``.
  * MF-DFA - Kantelhardt et al. 2002, Physica A 316:87-114, DOI 10.1016/S0378-4371(02)01383-3. The
    generalized Hurst h(q), mass exponent tau(q)=q*h(q)-1, and the singularity spectrum f(alpha) via the
    Legendre transform. Spectrum WIDTH = degree of multifractality. ``MFDFA.MFDFA``.
  * Fractal dimension - Higuchi 1988, Physica D 31:277-283, DOI 10.1016/0167-2789(88)90081-4; Katz 1988;
    Petrosian 1995. D in [1, 2] for a series graph: higher = rougher. ``antropy.{higuchi_fd,katz_fd,petrosian_fd}``.
  * Modeling counterpart: ARFIMA fractional differencing d = H - 0.5 (Granger-Joyeux 1980; Hosking 1981) -
    recorded as the long-memory link, not fitted here (no maintained Python ARFIMA mean-estimator; see plan).

HONESTY: DFA always returns a positive alpha even for non-self-similar data, and R/S is biased on short
series (needs n > ~50-100). We report the value AND a caveat flag; forecastability claims are gated by the
[nonlinear-dynamics] surrogate tests, not by a single exponent.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class HurstResult:
    """Long-range dependence: the Hurst exponent by R/S and by DFA, with an interpretation."""

    hurst_rs: float
    dfa_alpha: float
    interpretation: str          # anti-persistent / random-walk-like / persistent
    reliable: bool               # False when n is too short for a stable estimate
    reference: str


def _interpret_hurst(h: float) -> str:
    if h < 0.45:
        return "anti-persistent (mean-reverting; H < 0.5)"
    if h > 0.55:
        return "persistent (long-range positive dependence; H > 0.5)"
    return "random-walk-like (no long-range dependence; H ~ 0.5)"


def hurst(x) -> HurstResult:
    """Hurst exponent by rescaled-range (Anis-Lloyd corrected) and by DFA; flags short-sample unreliability."""
    from hurst import compute_Hc
    import nolds

    a = _clean(x)
    n = len(a)
    # R/S on the series levels (compute_Hc expects a positive-ish level series; use kind='change' for returns)
    try:
        h_rs, _c, _data = compute_Hc(a, kind="random_walk", simplified=True)
    except Exception:  # noqa: BLE001 - fall back to nolds if compute_Hc rejects the input
        h_rs = float(nolds.hurst_rs(a))
    dfa_alpha = float(nolds.dfa(a))
    # DFA alpha maps to H: fGn regime alpha in [0,1] -> H=alpha; fBm regime alpha in [1,2] -> H=alpha-1
    h_from_dfa = dfa_alpha if dfa_alpha <= 1.0 else dfa_alpha - 1.0
    return HurstResult(
        hurst_rs=float(h_rs), dfa_alpha=dfa_alpha,
        interpretation=_interpret_hurst(0.5 * (float(h_rs) + h_from_dfa)),
        reliable=bool(n >= 100),
        reference="Hurst 1951, Trans. ASCE 116:770-799 (R/S); Peng et al. 1994, Phys. Rev. E 49:1685-1689 (DFA)",
    )


@dataclass(frozen=True)
class MultifractalSpectrum:
    """MF-DFA output: generalized Hurst h(q), mass exponent tau(q), and the singularity spectrum f(alpha)."""

    q: np.ndarray
    hq: np.ndarray               # generalized Hurst exponent per q
    tau: np.ndarray              # mass exponent tau(q) = q*h(q) - 1
    alpha: np.ndarray            # singularity strength (Holder exponent)
    f_alpha: np.ndarray          # singularity spectrum
    width: float                 # max(alpha) - min(alpha): the degree of multifractality
    is_multifractal: bool        # width above a small threshold
    reference: str


def mfdfa(x, q=None, order: int = 1) -> MultifractalSpectrum:
    """MF-DFA generalized Hurst h(q) and the Legendre singularity spectrum f(alpha) (Kantelhardt 2002)."""
    from MFDFA import MFDFA as _MFDFA

    a = _clean(x)
    n = len(a)
    if n < 200:
        raise ValueError("MF-DFA needs a longer series (>= ~200 points) for a stable spectrum")
    q = np.asarray(q if q is not None else [-5, -3, -2, -1, 1, 2, 3, 5], dtype=float)
    q = q[q != 0]                                          # q=0 needs the log-averaging variant; skip it
    # geometric scales from ~8 up to n/4 (Kantelhardt's recommended range)
    lag = np.unique(np.geomspace(8, max(16, n // 4), 24).astype(int))
    lag2, dfa = _MFDFA(a, lag=lag, q=q, order=order)
    # h(q) = slope of log F_q(s) vs log s per q
    logs = np.log(lag2)
    hq = np.array([np.polyfit(logs, np.log(dfa[:, i]), 1)[0] for i in range(len(q))])
    tau = q * hq - 1.0
    # singularity spectrum via the Legendre transform: alpha = dtau/dq, f = q*alpha - tau
    alpha = np.gradient(tau, q)
    f_alpha = q * alpha - tau
    width = float(np.max(alpha) - np.min(alpha))
    return MultifractalSpectrum(
        q=q, hq=hq, tau=tau, alpha=alpha, f_alpha=f_alpha, width=width,
        is_multifractal=bool(width > 0.15),
        reference="Kantelhardt et al. 2002, Physica A 316:87-114, DOI 10.1016/S0378-4371(02)01383-3",
    )


@dataclass(frozen=True)
class FractalDimension:
    """Graph fractal dimension by three estimators (D in [1, 2]; higher = rougher)."""

    higuchi: float
    katz: float
    petrosian: float
    reference: str


def fractal_dimension(x, kmax: int = 10) -> FractalDimension:
    """Higuchi, Katz, and Petrosian fractal dimension of the series graph (antropy)."""
    import antropy as ant

    a = _clean(x)
    return FractalDimension(
        higuchi=float(ant.higuchi_fd(a, kmax=kmax)), katz=float(ant.katz_fd(a)),
        petrosian=float(ant.petrosian_fd(a)),
        reference="Higuchi 1988, Physica D 31:277-283, DOI 10.1016/0167-2789(88)90081-4; Katz 1988; Petrosian 1995",
    )


def dcca_coefficient(x, y, scale: int | None = None) -> dict:
    """Detrended cross-correlation coefficient rho_DCCA at one scale (Zebende 2011), in [-1, 1].

    Measures scale-dependent cross-correlation between two nonstationary series after local detrending.
    Uses a direct DCCA implementation (Podobnik & Stanley 2008): integrate both series, slide a window,
    locally detrend, and form the detrended covariance normalized by the two detrended variances.
    """
    a, b = _clean(x), _clean(y)
    m = min(len(a), len(b))
    a, b = a[:m], b[:m]
    if scale is None:
        scale = max(8, m // 8)
    if scale >= m:
        raise ValueError("scale must be smaller than the series length")
    # integrate to profiles
    A = np.cumsum(a - a.mean())
    B = np.cumsum(b - b.mean())
    fa2 = fb2 = fab = 0.0
    count = 0
    t = np.arange(scale + 1, dtype=float)
    for start in range(0, m - scale):
        wa, wb = A[start:start + scale + 1], B[start:start + scale + 1]
        # local linear detrend
        ca = np.polyfit(t, wa, 1)
        cb = np.polyfit(t, wb, 1)
        ra = wa - np.polyval(ca, t)
        rb = wb - np.polyval(cb, t)
        fab += float(np.mean(ra * rb))
        fa2 += float(np.mean(ra * ra))
        fb2 += float(np.mean(rb * rb))
        count += 1
    denom = np.sqrt(fa2 * fb2) if fa2 > 0 and fb2 > 0 else 0.0
    rho = float(fab / denom) if denom > 0 else float("nan")
    return {"scale": int(scale), "rho_dcca": rho, "n_windows": count,
            "reference": "Podobnik & Stanley 2008, PRL 100:084102, DOI 10.1103/PhysRevLett.100.084102; Zebende 2011, Physica A 390:614-618"}


def fractal_report(x) -> dict:
    """Run the fractal panel (Hurst + fractal dimension + MF-DFA where the series is long enough)."""
    a = _clean(x)
    h = hurst(a)
    fd = fractal_dimension(a)
    out = {
        "n": int(len(a)),
        "hurst": {"rs": h.hurst_rs, "dfa_alpha": h.dfa_alpha, "interpretation": h.interpretation,
                  "reliable": h.reliable, "reference": h.reference},
        "fractal_dimension": {"higuchi": fd.higuchi, "katz": fd.katz, "petrosian": fd.petrosian,
                              "reference": fd.reference},
        "arfima_link": {"d": round(h.hurst_rs - 0.5, 4),
                        "note": "long-memory fractional-differencing order d ~ H - 0.5 (Granger-Joyeux 1980)"},
    }
    try:
        mf = mfdfa(a)
        out["multifractal"] = {
            "q": mf.q.tolist(), "hq": mf.hq.tolist(), "alpha": mf.alpha.tolist(),
            "f_alpha": mf.f_alpha.tolist(), "width": mf.width, "is_multifractal": mf.is_multifractal,
            "reference": mf.reference,
        }
    except Exception as exc:  # noqa: BLE001 - series too short or degenerate; record, do not crash
        out["multifractal"] = {"error": f"{type(exc).__name__}: {exc}"}
    return out
