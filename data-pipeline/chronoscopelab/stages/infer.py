"""Stage 4 - infer: fit every method (classical ladder + available heavy engines) on the case history and
forecast the horizon.

The final ``horizon`` observations are held out as the display truth (shown in the App next to each
forecast); methods fit on ``y[:-horizon]`` only, so the displayed forecast is genuinely out-of-sample. A
heavy engine that cannot fit a given case (too short, singular) is omitted for that case rather than
crashing the pipeline.
"""
from __future__ import annotations

import numpy as np

from ..io.schema import ForecastResult, SeriesSpec
from ..methods import all_forecasters


def split(spec: SeriesSpec) -> tuple[np.ndarray, np.ndarray]:
    """Return (history, holdout_actual) with the last ``horizon`` points held out."""
    y = np.asarray(spec.y, dtype=float)
    cut = len(y) - spec.horizon
    return y[:cut], y[cut:]


def run(spec: SeriesSpec, quantile_levels: tuple[float, ...]) -> ForecastResult:
    history, _actual = split(spec)
    methods = []
    for fc in all_forecasters():
        try:
            methods.append(fc.forecast(history, spec.seasonality, spec.horizon, quantile_levels))
        except Exception:  # noqa: BLE001 - a heavy engine that cannot fit this case is skipped, honestly
            continue
    return ForecastResult(
        case_id=spec.case_id,
        horizon=spec.horizon,
        seasonality=spec.seasonality,
        quantile_levels=tuple(quantile_levels),
        history=tuple(float(v) for v in history),
        methods=tuple(methods),
    )
