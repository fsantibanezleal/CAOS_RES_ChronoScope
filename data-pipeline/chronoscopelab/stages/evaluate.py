"""Stage 5 - evaluate (the TEST stage): a leakage-safe rolling-origin backtest of every method on the
case history, scored with the `preqts` library (MASE / WQL / coverage). Each backtest window predicts
out-of-sample, so no method sees its own test point. This is where ChronoScope consumes preqts.
"""
from __future__ import annotations

import numpy as np

from preqts import ReplayAdapter, Stream, run_prequential

from ..io.schema import SeriesSpec
from ..model.forecasters import METHOD_FNS, normal_ppf

_MAX_WINDOWS = 24


def _batch_fn(method_name: str, m: int):
    """A batch forecaster for preqts: fit the method on the context and emit quantile columns."""

    def batch(context, horizon, past_cov, future_cov, levels):
        point, sigma = METHOD_FNS[method_name](np.asarray(context, dtype=float), m, horizon)
        steps = np.arange(1, horizon + 1)
        cols = [point + normal_ppf(lv) * sigma * np.sqrt(steps) for lv in levels]
        out = np.column_stack(cols)
        return np.maximum.accumulate(out, axis=1)  # keep quantiles monotone across levels

    return batch


def run(spec: SeriesSpec, quantile_levels: tuple[float, ...]) -> dict:
    y = np.asarray(spec.y, dtype=float)
    m, h = spec.seasonality, spec.horizon
    train_end = max(2 * m + h, len(y) - h)  # backtest within the observed history (the final block is the display holdout)
    hist = y[:train_end]
    stream = Stream(hist, seasonality=m, name=spec.case_id)

    warmup = min(max(2 * m, 10), max(1, len(hist) - h - 1))
    usable = len(hist) - warmup - h
    step = max(1, usable // _MAX_WINDOWS)

    methods: dict[str, dict] = {}
    for name in METHOD_FNS:
        adapter = ReplayAdapter(_batch_fn(name, m), name=name)
        res = run_prequential(adapter, stream, horizon=h, quantile_levels=quantile_levels,
                              step=step, warmup=warmup)
        s = res.summary()
        methods[name] = {
            "mase": _num(s["mase"]),
            "wql": _num(s["wql"]),
            "coverage": _num(s["coverage"]),
            "n_windows": res.n_windows,
        }

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
