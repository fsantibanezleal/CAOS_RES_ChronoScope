"""Nonlinear dynamics and chaos: phase-space embedding, correlation dimension, Lyapunov, RQA, 0-1, surrogates.

Is the series the output of a low-dimensional deterministic (possibly chaotic) system, or is it stochastic?
This distinction bounds forecastability: a chaotic system is deterministic yet has a finite prediction
horizon (errors grow like e^{lambda t}), while a stochastic one has no such structure to exploit. The tools
here reconstruct the state space (Takens), measure its dimension (Grassberger-Procaccia) and its sensitivity
to initial conditions (largest Lyapunov exponent), visualize recurrences (RQA), and - crucially - guard every
"it's chaotic" claim behind SURROGATE testing, because colored noise can mimic a low correlation dimension.

Methods / references (verified 2026-07-04; dossier research-nonlinear-dynamics-2026-07-04.md):
  * Takens time-delay embedding - Takens 1981, LNM 898:366-381, DOI 10.1007/BFb0091924.
  * Correlation dimension D2 (Grassberger-Procaccia) - 1983, Physica D 9:189-208,
    DOI 10.1016/0167-2789(83)90298-1. ``nolds.corr_dim``.
  * Largest Lyapunov exponent - Rosenstein et al. 1993, Physica D 65:117-134,
    DOI 10.1016/0167-2789(93)90009-P. ``nolds.lyap_r``.
  * Recurrence plots + RQA - Eckmann, Kamphorst & Ruelle 1987, EPL 4(9):973-977,
    DOI 10.1209/0295-5075/4/9/004; Marwan et al. 2007, Phys. Rep. 438:237-329,
    DOI 10.1016/j.physrep.2006.11.001. RQA implemented directly (RR/DET/LAM/L_max).
  * IAAFT surrogates - Schreiber & Schmitz 1996, PRL 77:635-638, DOI 10.1103/PhysRevLett.77.635; the
    surrogate-data method: Theiler et al. 1992, Physica D 58:77-94, DOI 10.1016/0167-2789(92)90102-S.

HONESTY GATE: Osborne & Provenzale 1989 showed colored noise yields a finite, saturating correlation
dimension - so a low D2 alone does NOT prove chaos. The unit requires the surrogate test (a nonlinear
statistic must differ from phase-randomized surrogates) before any determinism/chaos claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


def time_delay_embed(x, dim: int = 3, lag: int = 1) -> np.ndarray:
    """Takens embedding: rows are state vectors [x_t, x_{t+lag}, ..., x_{t+(dim-1)lag}]."""
    a = _clean(x)
    n = len(a) - (dim - 1) * lag
    if n <= 0:
        raise ValueError("series too short for this embedding dim/lag")
    return np.column_stack([a[i * lag: i * lag + n] for i in range(dim)])


@dataclass(frozen=True)
class ChaosMeasures:
    """Correlation dimension + largest Lyapunov exponent, with a (surrogate-gated) chaos verdict."""

    corr_dim: float
    lyap_r: float
    emb_dim: int
    lag: int
    likely_chaotic: bool         # lyap_r > 0 AND the surrogate test rejects linearity (set by caller)
    reference: str


def chaos_measures(x, emb_dim: int = 4, lag: int = 1) -> ChaosMeasures:
    """Grassberger-Procaccia correlation dimension + Rosenstein largest Lyapunov exponent (nolds)."""
    import nolds

    a = _clean(x)
    d2 = float(nolds.corr_dim(a, emb_dim=emb_dim))
    # Rosenstein largest Lyapunov: positive => sensitive dependence (a chaos signature, not proof)
    try:
        lyap = float(nolds.lyap_r(a, emb_dim=emb_dim, lag=lag, min_tsep=max(5, len(a) // 200)))
    except Exception:  # noqa: BLE001
        lyap = float("nan")
    return ChaosMeasures(
        corr_dim=d2, lyap_r=lyap, emb_dim=emb_dim, lag=lag,
        likely_chaotic=False,   # only the surrogate-gated report sets this True
        reference="Grassberger & Procaccia 1983, DOI 10.1016/0167-2789(83)90298-1; Rosenstein et al. 1993, DOI 10.1016/0167-2789(93)90009-P",
    )


@dataclass(frozen=True)
class RQA:
    """Recurrence quantification: recurrence rate, determinism, laminarity, longest diagonal line."""

    recurrence_rate: float       # RR: density of recurrence points
    determinism: float           # DET: fraction of recurrence points on diagonal lines (predictability)
    laminarity: float            # LAM: fraction on vertical lines (intermittency / laminar states)
    l_max: int                   # longest diagonal line (inversely related to the largest Lyapunov)
    threshold: float
    reference: str


def recurrence_quantification(x, emb_dim: int = 3, lag: int = 1, rr_target: float = 0.1,
                              l_min: int = 2, max_n: int = 800) -> RQA:
    """Build the recurrence matrix at a threshold giving ~rr_target density, then quantify it (RQA).

    Following Marwan et al. 2007: recurrence R(i,j) = 1 iff ||v_i - v_j|| < eps, with eps chosen to hit a
    target recurrence rate. DET = fraction of recurrence points forming diagonal lines of length >= l_min
    (determinism); LAM = fraction forming vertical lines (laminarity); L_max = longest diagonal.
    """
    v = time_delay_embed(x, dim=emb_dim, lag=lag)
    n = v.shape[0]
    if n > max_n:                                         # truncate (not subsample) to keep diagonals intact:
        v = v[:max_n]                                     # decimating would break the temporal continuity RQA needs
        n = v.shape[0]
    # pairwise Euclidean distances
    diff = v[:, None, :] - v[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    eps = float(np.quantile(dist, rr_target))             # threshold hitting ~rr_target density
    rec = (dist < eps).astype(np.int8)
    np.fill_diagonal(rec, 0)                              # exclude the trivial main diagonal (LOI)
    rr = float(rec.sum() / (n * (n - 1)))
    # diagonal-line lengths (determinism) and vertical-line lengths (laminarity)
    diag_lengths = _line_lengths_diagonal(rec)
    vert_lengths = _line_lengths_vertical(rec)
    total_points = int(rec.sum())
    det = float(sum(l for l in diag_lengths if l >= l_min) / total_points) if total_points else 0.0
    lam = float(sum(l for l in vert_lengths if l >= l_min) / total_points) if total_points else 0.0
    l_max = int(max(diag_lengths)) if diag_lengths else 0
    return RQA(
        recurrence_rate=rr, determinism=det, laminarity=lam, l_max=l_max, threshold=eps,
        reference="Eckmann, Kamphorst & Ruelle 1987, DOI 10.1209/0295-5075/4/9/004; Marwan et al. 2007, DOI 10.1016/j.physrep.2006.11.001",
    )


def _line_lengths_diagonal(rec: np.ndarray) -> list[int]:
    """Lengths of consecutive-1 runs along all off-main diagonals (both triangles) of the recurrence matrix.

    The matrix is symmetric, so we count both the positive and negative offsets: this matches the denominator
    (the full recurrence-point count ``rec.sum()``) so DET is the true fraction of points on diagonal lines.
    """
    n = rec.shape[0]
    lengths: list[int] = []
    for k in range(1, n):
        lengths.extend(_runs(np.diagonal(rec, offset=k)))     # upper triangle
        lengths.extend(_runs(np.diagonal(rec, offset=-k)))    # lower triangle
    return lengths


def _line_lengths_vertical(rec: np.ndarray) -> list[int]:
    """Lengths of consecutive-1 runs down each column (vertical lines)."""
    lengths: list[int] = []
    for col in rec.T:
        lengths.extend(_runs(col))
    return lengths


def _runs(v: np.ndarray) -> list[int]:
    """Lengths of maximal runs of 1s in a 0/1 vector."""
    out: list[int] = []
    run = 0
    for val in v:
        if val:
            run += 1
        elif run:
            out.append(run)
            run = 0
    if run:
        out.append(run)
    return out


def iaaft_surrogate(x, n_iter: int = 100, seed: int = 0) -> np.ndarray:
    """One IAAFT surrogate: same amplitude distribution AND power spectrum, but linearized dynamics.

    Schreiber & Schmitz 1996. If a nonlinear statistic on the data differs from an ensemble of these
    surrogates, the difference is genuine nonlinear structure, not an artifact of the spectrum/distribution.
    """
    a = _clean(x)
    rng = np.random.default_rng(seed)
    sorted_a = np.sort(a)
    amp = np.abs(np.fft.rfft(a))
    s = rng.permutation(a)
    for _ in range(n_iter):
        # match the power spectrum
        S = np.fft.rfft(s)
        S = amp * np.exp(1j * np.angle(S))
        s = np.fft.irfft(S, n=len(a))
        # match the amplitude distribution (rank-order remap)
        ranks = np.argsort(np.argsort(s))
        s = sorted_a[ranks]
    return s


def zero_one_test(x, n_c: int = 100, seed: int = 0) -> float:
    """Gottwald-Melbourne 0-1 test for chaos: K near 1 => chaotic, near 0 => regular (Gottwald & Melbourne 2004).

    For random phases c, drive p_c(n) = sum x_j cos(j c), q_c(n) = sum x_j sin(j c); the mean-square
    displacement M_c(n) grows linearly (K~1) for chaos and stays bounded (K~0) for regular dynamics. K is the
    median asymptotic growth rate over the random phases.
    """
    a = _clean(x)
    n = len(a)
    rng = np.random.default_rng(seed)
    a = a - a.mean()
    ncut = n // 10
    ks = []
    for _ in range(n_c):
        c = rng.uniform(np.pi / 5, 4 * np.pi / 5)
        j = np.arange(1, n + 1)
        p = np.cumsum(a * np.cos(j * c))
        q = np.cumsum(a * np.sin(j * c))
        M = np.array([np.mean((p[:n - k] - p[k:]) ** 2 + (q[:n - k] - q[k:]) ** 2) for k in range(1, ncut)])
        t = np.arange(1, ncut)
        # correlation of M with linear growth -> K
        if np.std(M) > 0:
            ks.append(float(np.corrcoef(t, M)[0, 1]))
    return float(np.median(ks)) if ks else float("nan")


def nonlinear_report(x, emb_dim: int = 4, lag: int = 1, n_surrogates: int = 19) -> dict:
    """Full nonlinear-dynamics panel WITH the surrogate gate: chaos claims require surrogate rejection."""
    a = _clean(x)
    cm = chaos_measures(a, emb_dim=emb_dim, lag=lag)
    rqa = recurrence_quantification(a, emb_dim=emb_dim, lag=lag)
    k01 = zero_one_test(a)
    # surrogate test: compare the data's correlation dimension to an ensemble of IAAFT surrogates.
    surr_d2 = []
    for i in range(n_surrogates):
        try:
            s = iaaft_surrogate(a, seed=i)
            surr_d2.append(chaos_measures(s, emb_dim=emb_dim, lag=lag).corr_dim)
        except Exception:  # noqa: BLE001
            pass
    nonlinear_detected = None
    if surr_d2:
        mu, sd = float(np.mean(surr_d2)), float(np.std(surr_d2))
        # data D2 significantly LOWER than surrogates => genuine (nonlinear) low-dim structure
        nonlinear_detected = bool(sd > 0 and cm.corr_dim < mu - 2 * sd)
    likely_chaotic = bool((cm.lyap_r > 0.01) and (k01 > 0.5) and (nonlinear_detected is True))
    return {
        "n": int(len(a)),
        "correlation_dimension": cm.corr_dim,
        "largest_lyapunov": cm.lyap_r,
        "zero_one_K": k01,
        "rqa": {"recurrence_rate": rqa.recurrence_rate, "determinism": rqa.determinism,
                "laminarity": rqa.laminarity, "l_max": rqa.l_max, "reference": rqa.reference},
        "surrogate_test": {"n_surrogates": len(surr_d2), "nonlinear_detected": nonlinear_detected,
                           "reference": "Schreiber & Schmitz 1996, DOI 10.1103/PhysRevLett.77.635 (IAAFT); Theiler et al. 1992, DOI 10.1016/0167-2789(92)90102-S"},
        "likely_chaotic": likely_chaotic,
        "verdict_note": "chaos claimed only when Lyapunov>0 AND 0-1 K>0.5 AND surrogate rejects linearity",
        "reference": cm.reference,
    }
