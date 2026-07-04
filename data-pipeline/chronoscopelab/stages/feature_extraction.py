"""Stage 2 - feature_extraction: a series -> a compact fingerprint (deterministic). Describes the case
(trend/seasonal strength, autocorrelation, intermittency) for the docs and the App context panel."""
from __future__ import annotations

import numpy as np

from ..io.schema import FeatureRow, SeriesSpec


def _seasonal_strength(y: np.ndarray, m: int) -> float:
    if m < 2 or y.shape[0] < 2 * m:
        return 0.0
    n = (y.shape[0] // m) * m
    blocks = y[:n].reshape(-1, m)
    seasonal_means = blocks.mean(axis=0)
    seasonal_component = np.tile(seasonal_means, n // m)
    resid = y[:n] - seasonal_component
    var_total = float(np.var(y[:n]))
    return float(max(0.0, 1.0 - np.var(resid) / var_total)) if var_total > 0 else 0.0


def run(spec: SeriesSpec) -> FeatureRow:
    y = np.asarray(spec.y, dtype=float)
    y = y[~np.isnan(y)]
    n = y.shape[0]
    t = np.arange(n, dtype=float)
    slope = float(np.polyfit(t, y, 1)[0]) if n >= 2 else 0.0
    if n >= 2 and np.std(y) > 0:
        acf1 = float(np.corrcoef(y[:-1], y[1:])[0, 1])
    else:
        acf1 = 0.0
    return FeatureRow(
        case_id=spec.case_id,
        n_obs=n,
        seasonality=spec.seasonality,
        mean=float(np.mean(y)) if n else 0.0,
        std=float(np.std(y)) if n else 0.0,
        trend_slope=slope,
        seasonal_strength=_seasonal_strength(y, spec.seasonality),
        acf1=acf1,
        pct_zeros=float(np.mean(y == 0.0)) if n else 0.0,
    )
