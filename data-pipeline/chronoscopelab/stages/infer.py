"""Stage 4 - infer: fit every method on the case history and forecast the horizon.

The final ``horizon`` observations are held out as the display truth (shown in the App next to each
forecast); methods fit on ``y[:-horizon]`` only, so the displayed forecast is genuinely out-of-sample.
"""
from __future__ import annotations

import numpy as np

from ..io.schema import ForecastResult, SeriesSpec
from ..model.forecasters import forecast_all


def split(spec: SeriesSpec) -> tuple[np.ndarray, np.ndarray]:
    """Return (history, holdout_actual) with the last ``horizon`` points held out."""
    y = np.asarray(spec.y, dtype=float)
    cut = len(y) - spec.horizon
    return y[:cut], y[cut:]


def run(spec: SeriesSpec, quantile_levels: tuple[float, ...]) -> ForecastResult:
    history, _actual = split(spec)
    methods = forecast_all(history, spec.seasonality, spec.horizon, quantile_levels)
    return ForecastResult(
        case_id=spec.case_id,
        horizon=spec.horizon,
        seasonality=spec.seasonality,
        quantile_levels=tuple(quantile_levels),
        history=tuple(float(v) for v in history),
        methods=tuple(methods),
    )
