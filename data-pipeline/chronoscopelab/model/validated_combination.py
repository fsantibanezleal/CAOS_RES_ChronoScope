"""Forecast combinations selected by validation wholly inside the observed prefix.

No outer target is accepted by this API. Model selection compares completed
historical blocks, and each inner fit excludes blocks not completed at its query.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations

import numpy as np

from .context_memory import CONFIG, _scale, context_features
from .forecasters import METHODS, gaussian_quantiles

CANDIDATES = (
    ("recency", 1., 1.), ("equal", 0., 1.),
    *(("context", shrink, temp) for shrink in (0., .5, 1.) for temp in (.15, .5, 1.)),
    *(("stack", penalty, 1.) for penalty in (.01, .1, 1., 10.)),
)


@dataclass(frozen=True)
class ValidatedFit:
    quantiles: np.ndarray
    weights: np.ndarray
    selected: tuple[str, float, float]
    candidates: tuple[dict, ...]
    origins: tuple[int, ...]
    validation_splits: tuple[dict, ...]


def convex_weights(errors, penalty):
    """Convex squared-error stacking with shrinkage toward uniform allocation."""
    a = np.asarray(errors, dtype=float)
    if a.ndim != 2 or not len(a) or not np.isfinite(a).all() or penalty <= 0:
        raise ValueError("Stacking requires finite error rows and positive regularization")
    k = a.shape[1]
    uniform = np.full(k, 1 / k)
    gram = a.T @ a / len(a)

    def objective(w):
        return float(w @ gram @ w + penalty * np.sum((w - uniform) ** 2))

    # Five experts permit exhaustive active-set solutions (31 nonempty faces).
    # Each face has a positive-definite regularized quadratic; the best feasible
    # face is the constrained optimum, without iterative solver stopping rules.
    best, value = uniform, objective(uniform)
    for size in range(1, k + 1):
        for active in combinations(range(k), size):
            ids = list(active)
            matrix = gram[np.ix_(ids, ids)] + penalty * np.eye(size)
            rhs = np.column_stack((penalty * uniform[ids], np.ones(size)))
            try:
                solution = np.linalg.solve(matrix, rhs)
            except np.linalg.LinAlgError:
                continue
            x, direction = solution[:, 0], solution[:, 1]
            x = x + (1 - x.sum()) * direction / direction.sum()
            if not np.isfinite(x).all() or np.min(x) < -1e-10:
                continue
            weights = np.zeros(k)
            weights[ids] = np.maximum(x, 0.)
            weights /= weights.sum()
            score = objective(weights)
            if score < value:
                best, value = weights, score
    return best


def candidate_weights(candidate, features, losses, errors, query):
    k = len(METHODS)
    kind, shrink, temp = candidate
    if not len(losses) or kind == "equal":
        return np.full(k, 1 / k)
    if kind == "stack":
        weights = convex_weights(errors.reshape(-1, k), shrink)
    else:
        ages = np.arange(len(losses) - 1, -1, -1)
        recency = np.exp2(-ages / CONFIG["half_life_origins"])
        global_loss = np.average(losses, axis=0, weights=recency)
        score = global_loss
        if kind == "context":
            distance = np.sqrt(np.mean((features - query) ** 2, axis=1))
            bandwidth = max(float(np.median(distance)), CONFIG["kernel_bandwidth_floor"])
            local = recency * np.exp(-.5 * (distance / bandwidth) ** 2)
            score = (1 - shrink) * np.average(losses, axis=0, weights=local) + shrink * global_loss
        weights = np.exp(np.clip(-(score - np.min(score)) / temp, -700, 0))
        weights /= weights.sum()
    return .95 * weights + .05 / k


@lru_cache(maxsize=16)
def memory(values, m, h):
    y = np.asarray(values, dtype=float)
    first, last = max(2 * m, 2 * h + 8, 24), len(y) - h
    if first > last:
        return (), np.empty((0, 4)), np.empty((0, len(METHODS))), np.empty((0, h, len(METHODS))), ()
    origins = tuple(int(o) for o in np.unique(np.linspace(first, last, CONFIG["memory_origins"], dtype=int)))
    features, losses, errors, paths = [], [], [], []
    for origin in origins:
        prefix, truth = y[:origin], y[origin:origin+h]
        quantiles = np.array([gaussian_quantiles(*fn(prefix, m, h), (.1, .5, .9)) for _, _, fn in METHODS])
        normalized_error = (quantiles[:, :, 1].T - truth[:, None]) / _scale(prefix, m)
        features.append(context_features(prefix, m))
        losses.append(np.mean(abs(normalized_error), axis=0))
        errors.append(normalized_error)
        paths.append(quantiles)
    return origins, np.asarray(features), np.asarray(losses), np.asarray(errors), tuple(paths)


def temporal_splits(origins, horizon):
    """Training outcomes must be fully observed when an inner forecast is issued."""
    return tuple({"query": query, "train": tuple(i for i, origin in enumerate(origins) if origin+horizon <= query)}
                 for query in origins)


def fit_validated(y, m, h, *, stacking=True):
    y = np.asarray(y, dtype=float)
    if y.ndim != 1 or len(y) < 2 or not np.isfinite(y).all() or m < 1 or h < 1:
        raise ValueError("Finite contiguous history, positive seasonality and horizon are required")
    origins, features, losses, errors, paths = memory(tuple(y), m, h)
    candidates = CANDIDATES if stacking else tuple(c for c in CANDIDATES if c[0] != "stack")
    splits = tuple(s for s in temporal_splits(origins, h) if len(s["train"]) >= 3)
    scores = []
    for candidate in candidates:
        values = []
        for split in splits:
            j = origins.index(split["query"])
            train = list(split["train"])
            w = candidate_weights(candidate, features[train], losses[train], errors[train], features[j])
            values.append(float(np.mean(abs(errors[j] @ w))))
        scores.append({"configuration": candidate, "mean_validation_mae_scaled": float(np.mean(values)) if values else None,
                       "validation_blocks": len(values)})
    if splits:
        winner = min(range(len(candidates)), key=lambda i: (scores[i]["mean_validation_mae_scaled"], i))
    else:
        winner = 0  # explicit original recency-only fallback
    selected = candidates[winner]
    w = candidate_weights(selected, features, losses, errors, context_features(y, m))
    experts = np.array([gaussian_quantiles(*fn(y, m, h), (.1, .5, .9)) for _, _, fn in METHODS])
    combined = np.tensordot(w, experts, axes=(0, 0))
    return ValidatedFit(combined, w, selected, tuple(scores), origins, splits)
