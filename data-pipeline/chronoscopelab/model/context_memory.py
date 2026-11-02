"""ContextMemory: a within-series forecast-combination proposal and its ablations.

Published feature-based averaging and dynamic ensembles motivate the proposal; this
specific recurrence/recency rule is an experiment, with no claim of priority or superiority.
All training targets end before the supplied history ends. The final holdout is never an input.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .forecasters import METHODS, Forecaster, _clean, gaussian_quantiles

CONFIG = {
    "memory_origins": 12,
    "half_life_origins": 6.0,
    "global_shrinkage": 0.25,
    "uniform_floor": 0.05,
    "temperature": 1.0,
    "kernel_bandwidth_floor": 0.25,
}
EXPERT_NAMES = tuple(name for name, _, _ in METHODS)


@dataclass(frozen=True)
class MemoryFit:
    quantiles: np.ndarray
    weights: np.ndarray
    origins: tuple[int, ...]
    context: np.ndarray


def context_features(y: np.ndarray, m: int) -> np.ndarray:
    """Four bounded, location-invariant and positive-scale-invariant summaries."""
    w = min(len(y) // 2, max(8, min(2 * max(m, 1), 48)))
    if w < 2:
        return np.zeros(4)
    recent, previous = y[-w:], y[-2 * w:-w]
    scale = float(np.std(y[-2 * w:]))
    if scale < 1e-12:
        return np.zeros(4)
    half = max(1, w // 2)
    slope = (np.mean(recent[-half:]) - np.mean(recent[:half])) / scale
    shift = (np.mean(recent) - np.mean(previous)) / scale
    vr, vp = float(np.std(np.diff(recent))), float(np.std(np.diff(previous)))
    volatility = np.log((vr + scale * 1e-6) / (vp + scale * 1e-6))
    periodicity = 0.0
    if m >= 2 and len(y) >= 2 * m + 2:
        a, b = y[-2 * m:-m], y[-m:]
        if np.std(a) > 1e-12 and np.std(b) > 1e-12:
            periodicity = float(np.corrcoef(a, b)[0, 1])
    return np.clip([slope, shift, volatility, periodicity], -4, 4)


def _scale(y: np.ndarray, m: int) -> float:
    lag = max(1, min(m, len(y) - 1))
    value = float(np.mean(np.abs(y[lag:] - y[:-lag])))
    return value if value > 1e-12 else max(float(np.std(y)), 1e-12)


@lru_cache(maxsize=64)
def _memory(values: tuple[float, ...], m: int, h: int):
    y = np.asarray(values)
    first, last = max(2 * m, 2 * h + 8, 24), len(y) - h
    if last < first:
        return (), np.empty((0, 4)), np.empty((0, len(METHODS)))
    origins = tuple(int(o) for o in np.unique(np.linspace(first, last, CONFIG["memory_origins"], dtype=int)))
    features, losses = [], []
    for origin in origins:
        history, truth = y[:origin], y[origin:origin + h]
        features.append(context_features(history, m))
        losses.append([
            float(np.mean(np.abs(fn(history, m, h)[0] - truth))) / _scale(history, m)
            for _, _, fn in METHODS
        ])
    return origins, np.asarray(features), np.asarray(losses)


def fit_context_memory(y: np.ndarray, m: int, h: int, levels=(0.1, 0.5, 0.9), mode="context") -> MemoryFit:
    """Fit from completed historical origins, then combine experts at the query origin.

    The recency ablation removes the context kernel; the uniform ablation removes
    both learning components. Configuration is fixed before the released holdout run.
    Weighted quantiles are a quantile combination, not a calibrated mixture distribution.
    """
    y = _clean(np.asarray(y, dtype=float))
    if len(y) < 2 or not np.isfinite(y).all() or h < 1 or m < 1:
        raise ValueError("ContextMemory requires finite history, positive horizon and seasonality")
    if mode not in {"context", "recency", "uniform"}:
        raise ValueError(f"Unknown combination mode: {mode}")
    origins, features, losses = _memory(tuple(float(v) for v in y), m, h)
    query = context_features(y, m)
    weights = np.full(len(METHODS), 1 / len(METHODS))
    if len(origins) and mode != "uniform":
        ages = np.arange(len(origins) - 1, -1, -1)
        recency = np.exp2(-ages / CONFIG["half_life_origins"])
        global_loss = np.average(losses, axis=0, weights=recency)
        score = global_loss
        if mode == "context":
            distance = np.sqrt(np.mean((features - query) ** 2, axis=1))
            bandwidth = max(float(np.median(distance)), CONFIG["kernel_bandwidth_floor"])
            local = recency * np.exp(-0.5 * (distance / bandwidth) ** 2)
            local_loss = np.average(losses, axis=0, weights=local)
            shrink = CONFIG["global_shrinkage"]
            score = (1 - shrink) * local_loss + shrink * global_loss
        logits = -(score - np.min(score)) / CONFIG["temperature"]
        weights = np.exp(np.clip(logits, -700, 0))
        weights /= weights.sum()
        floor = CONFIG["uniform_floor"]
        weights = (1 - floor) * weights + floor / len(METHODS)
    forecasts = []
    for _, _, fn in METHODS:
        point, sigma = fn(y, m, h)
        forecasts.append(gaussian_quantiles(point, sigma, tuple(levels)))
    combined = np.tensordot(weights, np.asarray(forecasts), axes=(0, 0))
    return MemoryFit(combined, weights, origins, query)


class ContextMemoryForecaster(Forecaster):
    name = "ContextMemory"
    family = "adaptive ensemble"
    max_windows = 3

    def quantiles(self, y, m, h, levels):
        return fit_context_memory(y, m, h, levels).quantiles
