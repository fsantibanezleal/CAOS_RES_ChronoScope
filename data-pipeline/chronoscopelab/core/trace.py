"""The compact TRACE = the web-replay artifact (decimated history + every method's forecast + backtest).
Part of CONTRACT 2: its shape is mirrored by frontend/src/lib/contract.types.ts, so a drift fails the web
build. Schema id is versioned. NaN metrics become null via the JSON writer (strict JSON for the browser)."""
from __future__ import annotations

from ..io.schema import ForecastResult

TRACE_SCHEMA = "chronoscope.trace/v1"
MAX_HISTORY = 300  # decimate long histories so the committed artifact stays small (replay, not raw data)


def _round(v: float, nd: int = 4) -> float:
    return round(float(v), nd)


def build_trace(result: ForecastResult, actual: list[float], eval_metrics: dict) -> dict:
    hist = list(result.history)
    n = len(hist)
    if n > MAX_HISTORY:
        idx = [round(i * (n - 1) / (MAX_HISTORY - 1)) for i in range(MAX_HISTORY)]
    else:
        idx = list(range(n))
    method_metrics = eval_metrics.get("methods", {})

    methods = []
    for mf in result.methods:
        bt = method_metrics.get(mf.name, {})
        methods.append({
            "name": mf.name,
            "family": mf.family,
            "point": [_round(v) for v in mf.point],
            "lower": [_round(v) for v in mf.lower],
            "upper": [_round(v) for v in mf.upper],
            "backtest": {
                "mase": bt.get("mase"),
                "wql": bt.get("wql"),
                "coverage": bt.get("coverage"),
                "n_windows": bt.get("n_windows"),
            },
        })

    return {
        "schema": TRACE_SCHEMA,
        "case_id": result.case_id,
        "seasonality": result.seasonality,
        "horizon": result.horizon,
        "quantile_levels": list(result.quantile_levels),
        "history_len": n,                       # forecast x-positions start here: n .. n+horizon-1
        "history_index": idx,                   # x positions of the (decimated) history points
        "history": [_round(hist[i]) for i in idx],
        "actual": [_round(v) for v in actual],  # the held-out truth for the horizon
        "methods": methods,
        "summary": {
            "best_method": eval_metrics.get("best_method"),
            "best_mase": eval_metrics.get("best_mase"),
            "nominal_coverage": eval_metrics.get("nominal_coverage"),
        },
    }
