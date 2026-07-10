"""The compact TRACE = the web-replay artifact (decimated history + every method's forecast + backtest).
Part of CONTRACT 2: its shape is mirrored by frontend/src/lib/contract.types.ts, so a drift fails the web
build. Schema id is versioned. NaN metrics become null via the JSON writer (strict JSON for the browser)."""
from __future__ import annotations

from ..io.schema import ForecastResult

# v2 (0.15.000): backtest gains mae/rmse/smape/msis + per_horizon_scaled (preqts 0.3); additive.
TRACE_SCHEMA = "chronoscope.trace/v2"
MAX_HISTORY = 300  # decimate long histories so the committed artifact stays small (replay, not raw data)


def _round(v: float, nd: int = 4) -> float:
    return round(float(v), nd)


def build_trace(result: ForecastResult, actual: list[float], eval_metrics: dict,
                redact_raw: bool = False) -> dict:
    """Build the replay trace. When ``redact_raw`` (a local-only-licensed source), the raw series excerpt and
    the per-step forecast paths are omitted and ONLY aggregate backtest metrics ship - so a dataset whose
    license forbids redistribution still contributes to the public Benchmark without leaking its values."""
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
        entry = {
            "name": mf.name,
            "family": mf.family,
            "backtest": {
                "mase": bt.get("mase"),
                "wql": bt.get("wql"),
                "coverage": bt.get("coverage"),
                "mae": bt.get("mae"),
                "rmse": bt.get("rmse"),
                "smape": bt.get("smape"),
                "msis": bt.get("msis"),
                # per-lead MASE-like curve (preqts 0.3), aggregate over cutoffs; ships even for
                # license-redacted sources (an aggregate like the other backtest metrics, no raw values)
                "per_horizon_scaled": bt.get("per_horizon_scaled", []),
                "n_windows": bt.get("n_windows"),
            },
        }
        if not redact_raw:
            # the per-step forecast paths reveal the source's values; ship them only for public-safe sources
            entry["point"] = [_round(v) for v in mf.point]
            entry["lower"] = [_round(v) for v in mf.lower]
            entry["upper"] = [_round(v) for v in mf.upper]
        methods.append(entry)

    return {
        "schema": TRACE_SCHEMA,
        "case_id": result.case_id,
        "seasonality": result.seasonality,
        "horizon": result.horizon,
        "quantile_levels": list(result.quantile_levels),
        "redacted": redact_raw,                 # true = license forbids shipping the raw series; metrics only
        "history_len": n,                       # forecast x-positions start here: n .. n+horizon-1
        "history_index": [] if redact_raw else idx,
        "history": [] if redact_raw else [_round(hist[i]) for i in idx],
        "actual": [] if redact_raw else [_round(v) for v in actual],  # held-out truth (omitted if redacted)
        "methods": methods,
        "summary": {
            "best_method": eval_metrics.get("best_method"),
            "best_mase": eval_metrics.get("best_mase"),
            "nominal_coverage": eval_metrics.get("nominal_coverage"),
        },
    }
