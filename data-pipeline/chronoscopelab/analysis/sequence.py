"""Retrospective sequence diagnostics on original, contiguous observations.

Matrix Profile/FLUSS: Yeh et al. 2016, DOI 10.1109/ICDM.2016.0179;
Gharghabi et al. 2017, DOI 10.1109/ICDM.2017.21 (STUMPY implementation).
Multiscale entropy: Costa et al. 2002, DOI 10.1103/PhysRevLett.89.068102.
Lempel-Ziv: Lempel & Ziv 1976, DOI 10.1109/TIT.1976.1055501.
Time reversal: the third-order lag statistic documented by tsfresh.
"""
from __future__ import annotations

import math

import numpy as np


def finite_sequence(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1 or len(a) < 3 or not np.isfinite(a).all():
        raise ValueError("A contiguous finite one-dimensional sequence of at least three observations is required")
    return a


def matrix_profile(x, window: int = 32, regimes: int = 3) -> dict:
    """Exact z-normalized self join; candidates are descriptive, never causal alarms."""
    import stumpy

    a = finite_sequence(x)
    if not isinstance(window, int) or window < 3 or len(a) < 2 * window + 1:
        raise ValueError("Matrix Profile requires an integer window >=3 and n >= 2*window+1")
    if not isinstance(regimes, int) or regimes < 2:
        raise ValueError("FLUSS requires at least two candidate regimes")
    if np.std(a) == 0:
        return {"available": False, "reason": "constant sequence has no discriminating shape profile",
                "n": len(a), "window": window}
    mp = stumpy.stump(a, m=window)
    distances = np.asarray(mp.P_, dtype=float)
    neighbors = np.asarray(mp.I_, dtype=int)
    motifs = []
    for i in np.argsort(distances, kind="stable"):
        j = int(neighbors[i])
        if np.isfinite(distances[i]) and j >= 0 and abs(int(i)-j) >= window:
            motifs.append({"start": int(i), "match": j, "distance": float(distances[i])})
            break
    discords = []
    for i in np.argsort(-distances, kind="stable"):
        if np.isfinite(distances[i]) and all(abs(int(i)-d['start']) >= window for d in discords):
            discords.append({"start": int(i), "distance": float(distances[i])})
            if len(discords) == 3:
                break
    cac, boundaries = stumpy.fluss(neighbors, L=window, n_regimes=regimes, excl_factor=1)
    return {"available": True, "n": len(a), "window": window,
            "exclusion_zone": int(math.ceil(window / stumpy.config.STUMPY_EXCL_ZONE_DENOM)),
            "profile": [float(v) if np.isfinite(v) else None for v in distances],
            "nearest_neighbor": neighbors.tolist(), "motifs": motifs, "discords": discords,
            "corrected_arc_curve": np.asarray(cac, dtype=float).tolist(),
            "regime_boundaries": sorted(int(b) for b in boundaries if 0 < int(b) < len(distances)),
            "regimes_requested": regimes, "normalization": "per-window population-standard-deviation z scores",
            "note": "Retrospective shape candidates, not anomaly probabilities or proven regime changes."}


def multiscale_entropy(x, scales=tuple(range(1, 11)), order: int = 2, tolerance_ratio: float = .15) -> dict:
    """Costa coarse-graining, with original-series tolerance and no self matches.

    Both m and m+1 templates use the same n-m start positions. Matching uses <= r
    Chebyshev distance; finite-sample no-match estimates remain unavailable.
    """
    from scipy.spatial import cKDTree

    a = finite_sequence(x)
    if order < 1 or not isinstance(order, int) or not 0 < tolerance_ratio < 1:
        raise ValueError("Invalid entropy order or tolerance ratio")
    scales = tuple(scales)
    if not scales or any(not isinstance(s, int) or s < 1 for s in scales) or len(set(scales)) != len(scales):
        raise ValueError("Scales must be distinct positive integers")
    tolerance = float(tolerance_ratio * np.std(a))
    rows = []
    for scale in scales:
        coarse = a[:len(a)//scale*scale].reshape(-1, scale).mean(axis=1)
        row = {"scale": scale, "n": len(coarse), "tolerance": tolerance, "entropy": None,
               "matching_m": 0, "matching_m_plus_one": 0}
        if len(coarse) < max(20, order + 3):
            row["reason"] = "fewer than twenty coarse-grained observations"
        else:
            templates = np.lib.stride_tricks.sliding_window_view(coarse, order + 1)
            counts = []
            for dimension in (order, order + 1):
                tree = cKDTree(templates[:, :dimension])
                counts.append(int((tree.count_neighbors(tree, tolerance, p=np.inf) - len(templates)) // 2))
            b, matches = counts
            row.update(matching_m=b, matching_m_plus_one=matches)
            if matches and b:
                row["entropy"] = float(-np.log(matches / b))
            else:
                row["reason"] = "no matching templates; finite sample entropy is unavailable"
        rows.append(row)
    return {"order": order, "tolerance_ratio": tolerance_ratio, "tolerance_basis": "original population standard deviation",
            "scales": rows}


def time_reversal(x, lag: int = 1) -> dict:
    """E[x[t+2l]^2*x[t+l] - x[t+l]*x[t]^2], raw and standardized."""
    a = finite_sequence(x)
    if not isinstance(lag, int) or lag < 1 or len(a) <= 2 * lag:
        raise ValueError("Time-reversal lag requires n > 2*lag")

    def statistic(values):
        return float(np.mean(values[lag:-lag] * (values[2*lag:]**2 - values[:-2*lag]**2)))

    sd = np.std(a)
    return {"lag": lag, "raw": statistic(a), "standardized": statistic((a-np.mean(a))/sd) if sd else 0.0,
            "note": "A descriptive third-order statistic; no significance or irreversibility verdict is inferred."}


def sequence_report(x, seasonality: int = 1, window: int | None = None) -> dict:
    """One JSON-ready contract for offline case diagnostics and the browser consumer."""
    import antropy

    a = finite_sequence(x)
    chosen = window if window is not None else min(max(8, 2*seasonality), 64, len(a)//3)
    profile = matrix_profile(a, window=chosen) if chosen >= 3 and len(a) >= 2*chosen+1 else {
        "available": False, "reason": "sequence too short for the profile", "n": len(a), "window": chosen}
    symbols = (a > np.median(a)).astype(int)
    return {"n": len(a), "observation_indices": list(range(len(a))), "values": a.tolist(),
            "matrix_profile": profile, "multiscale_entropy": multiscale_entropy(a),
            "lempel_ziv": {"raw": int(antropy.lziv_complexity(symbols, normalize=False)),
                           "normalized": float(antropy.lziv_complexity(symbols, normalize=True)),
                           "threshold": float(np.median(a)), "alphabet": "0 if x<=median, 1 otherwise",
                           "normalization": "c(n)*log2(n)/n; finite samples can exceed one"},
            "time_reversal": [time_reversal(a, lag) for lag in (1, 2, 7) if len(a) > 2*lag],
            "interpretation": "Retrospective full-sequence diagnostics; not input to a forecast at an earlier origin."}
