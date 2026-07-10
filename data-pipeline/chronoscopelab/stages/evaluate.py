"""Stage 5 - evaluate (the TEST stage): a leakage-safe rolling-origin backtest of every method on the
case history, scored with the `preqts` library (MASE / WQL / coverage). Each backtest window predicts
out-of-sample, so no method sees its own test point. This is where ChronoScope consumes preqts.

Classical methods get many windows (cheap); heavy engines get a bounded window budget (their own
`max_windows`) so an expensive search like AutoARIMA stays practical. A method that fails on a case is
recorded with NaN metrics rather than crashing the run.
"""
from __future__ import annotations

import numpy as np

from preqts import ReplayAdapter, Stream, run_prequential

from ..io.schema import SeriesSpec
from ..methods import all_forecasters
from ..model.forecasters import Forecaster


def _batch_fn(fc: Forecaster, m: int):
    def batch(context, horizon, past_cov, future_cov, levels):
        return fc.quantiles(np.asarray(context, dtype=float), m, horizon, tuple(levels))

    return batch


def run(spec: SeriesSpec, quantile_levels: tuple[float, ...], forecasters: list[Forecaster] | None = None) -> dict:
    fcs = forecasters if forecasters is not None else all_forecasters()
    y = np.asarray(spec.y, dtype=float)
    m, h = spec.seasonality, spec.horizon
    train_end = max(2 * m + h, len(y) - h)  # backtest within the observed history (the final block is the display holdout)
    hist = y[:train_end]
    stream = Stream(hist, seasonality=m, name=spec.case_id)

    # Warmup floor: at least two seasons AND enough context for the deep tier's minimum lookback
    # (2h + a small training margin). Without this, non-seasonal (m=1) cases gave the first backtest
    # window ~10 points, the deep engines raised, and the whole method was NaN on those cases.
    warmup = min(max(2 * m, 2 * h + 20, 10), max(1, len(hist) - h - 1))
    usable = len(hist) - warmup - h

    methods: dict[str, dict] = {}
    for fc in fcs:
        try:
            step = max(1, usable // max(1, fc.max_windows))
            adapter = ReplayAdapter(_batch_fn(fc, m), name=fc.name)
            res = run_prequential(adapter, stream, horizon=h, quantile_levels=quantile_levels,
                                  step=step, warmup=warmup)
            s = res.summary()
            ph = res.per_horizon()
            methods[fc.name] = {
                "mase": _num(s["mase"]),
                "wql": _num(s["wql"]),
                "coverage": _num(s["coverage"]),
                "mae": _num(s["mae"]),
                "rmse": _num(s["rmse"]),
                "smape": _num(s["smape"]),
                "msis": _num(s["msis"]),
                # error growth by lead time: mean |error| / seasonal-naive scale at each lead
                # (a per-lead MASE; preqts 0.3). The workbench Horizon panel renders this curve.
                "per_horizon_scaled": [_num(v) for v in ph["scaled"]],
                "n_windows": res.n_windows,
            }
        except Exception:  # noqa: BLE001 - a heavy engine that cannot backtest this case gets NaN metrics
            methods[fc.name] = {"mase": float("nan"), "wql": float("nan"), "coverage": float("nan"),
                                "mae": float("nan"), "rmse": float("nan"), "smape": float("nan"),
                                "msis": float("nan"), "per_horizon_scaled": [], "n_windows": 0}

    scored = [(n, v["mase"]) for n, v in methods.items() if v["mase"] == v["mase"]]  # drop NaN
    best_method, best_mase = min(scored, key=lambda kv: kv[1]) if scored else ("SeasonalNaive", float("nan"))
    return {
        "methods": methods,
        "best_method": best_method,
        "best_mase": _num(best_mase),
        "nominal_coverage": round(float(max(quantile_levels) - min(quantile_levels)), 4),
    }


def _num(x: float) -> float:
    x = float(x)
    return round(x, 5) if x == x else float("nan")  # keep NaN as NaN (not rounded)
