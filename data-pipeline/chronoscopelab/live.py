"""LIVE lane entrypoint (Pyodide-safe): forecast in the BROWSER using ONLY the pure-numpy model core (no
heavy offline engine, no preqts). The web worker calls run_forecast_json(case_id=..., seed=...) for a
baked case or with an explicit series for the bring-your-own-data interaction. The output mirrors the
offline trace's methods block so the SPA renders live and replayed forecasts identically."""
from __future__ import annotations

import numpy as np

from . import registry
from .model.forecasters import forecast_all

DEFAULT_LEVELS = (0.1, 0.5, 0.9)


def run_forecast_json(
    case_id: str | None = None,
    series: dict | None = None,
    seed: int = 42,
    quantile_levels: tuple[float, ...] = DEFAULT_LEVELS,
) -> dict:
    """Return {history, horizon, seasonality, methods:[{name,family,point,lower,upper}]} for a case or a
    user-supplied series ({"y": [...], "seasonality": m, "horizon": h})."""
    if series is not None:
        y = np.asarray([float(v) for v in series["y"]], dtype=float)
        m = int(series.get("seasonality", 1))
        h = int(series.get("horizon", max(1, m)))
    elif case_id is not None:
        spec = registry.build_series(registry.get_case(case_id), seed=seed)
        y = np.asarray(spec.y, dtype=float)
        m, h = spec.seasonality, spec.horizon
        y = y[: len(y) - h]  # forecast beyond the held-out block, same as the offline pipeline
    else:
        raise ValueError("run_forecast_json requires either case_id or series")

    methods = forecast_all(y, m, h, quantile_levels)
    return {
        "history": [round(float(v), 4) for v in y],
        "horizon": h,
        "seasonality": m,
        "quantile_levels": list(quantile_levels),
        "methods": [
            {"name": mf.name, "family": mf.family,
             "point": list(mf.point), "lower": list(mf.lower), "upper": list(mf.upper)}
            for mf in methods
        ],
    }
