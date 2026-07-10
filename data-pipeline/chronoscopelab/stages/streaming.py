"""Stage 5b - streaming: the prequential streaming bench (the product's flagship novel piece).

Real forecasting is streaming: observations arrive one by one, the model updates, and its INTERVALS must
stay calibrated as the series drifts. No public harness evaluates stateful forecasters this way with an
explicit covariate-arrival policy - that is the gap `preqts` (our published package, PyPI `preqts>=0.2`)
fills, and this stage bakes the demonstration per case:

For each streaming method (the classical live methods wrapped as replay + the ACI / Conformal-PID
calibrated variants of the best one), it runs a prequential test-then-update pass over the case history
and records the CUMULATIVE trajectories the web's streaming bench renders:

  * rolling MASE (skill as the stream lengthens),
  * rolling empirical coverage vs the nominal target (the calibration story: raw vs ACI vs PID),
  * per-step interval width (the price of coverage),
  * cumulative compute cost (ms) - the constant-cost-per-step story.

References (verified dossiers): prequential evaluation Dawid 1984 (DOI 10.2307/2981683); ACI Gibbs &
Candes 2021 (arXiv:2106.00170); Conformal PID Angelopoulos, Candes & Tibshirani 2023 (arXiv:2307.16895).
"""
from __future__ import annotations

import numpy as np

from preqts import AdaptiveConformal, ConformalPID, ReplayAdapter, Stream, run_prequential

from ..io.schema import SeriesSpec
from ..model.forecasters import classical_forecasters

_LEVELS = (0.1, 0.5, 0.9)
_TARGET = 0.8  # nominal outer coverage of the 10/90 band


def _batch_fn(fc, m: int):
    def batch(context, horizon, past_cov, future_cov, levels):
        return fc.quantiles(np.asarray(context, dtype=float), m, horizon, tuple(levels))

    return batch


def _rolling_mean(x: np.ndarray, w: int = 25) -> list:
    out = []
    for i in range(len(x)):
        seg = x[max(0, i - w + 1):i + 1]
        seg = seg[np.isfinite(seg)]
        out.append(round(float(seg.mean()), 5) if seg.size else None)
    return out


def _trajectories(res) -> dict:
    """Extract the per-cutoff trajectories the web renders from a preqts PrequentialResult."""
    cost_ms = (np.nan_to_num(res.predict_latency) + np.nan_to_num(res.ingest_latency)) * 1e3
    return {
        "cutoffs": [int(c) for c in res.cutoffs],
        "rolling_mase": _rolling_mean(np.asarray(res.mase, dtype=float)),
        "rolling_coverage": _rolling_mean(np.asarray(res.coverage, dtype=float)),
        "rolling_wql": _rolling_mean(np.asarray(res.wql, dtype=float)),
        "cumulative_cost_ms": np.cumsum(cost_ms).round(3).tolist(),
        "n_steps": int(res.n_windows),
    }


def run(spec: SeriesSpec, horizon: int = 1) -> dict:
    """Run the streaming bench on the case history; return the JSON-ready streaming artifact block."""
    y = np.asarray(spec.y, dtype=float)
    m = spec.seasonality
    stream = Stream(y, seasonality=m, name=spec.case_id)
    warmup = min(max(2 * m, 20), max(1, len(y) // 3))

    # the streaming roster: the best cheap classical live method raw, + its calibrated variants
    base_fc = next(f for f in classical_forecasters() if f.name == "Theta")
    naive_fc = next(f for f in classical_forecasters() if f.name == "SeasonalNaive")

    def _theta():
        return ReplayAdapter(_batch_fn(base_fc, m), name="Theta")

    roster = {
        "SeasonalNaive": ReplayAdapter(_batch_fn(naive_fc, m), name="SeasonalNaive"),
        "Theta": _theta(),
        "Theta+ACI": AdaptiveConformal(_theta(), target_coverage=_TARGET, gamma=0.02),
        "Theta+PID": ConformalPID(_theta(), target_coverage=_TARGET, kp=0.05, ki=0.02, kd=0.02),
    }

    methods: dict[str, dict] = {}
    for name, fc in roster.items():
        try:
            res = run_prequential(fc, stream, horizon=horizon, quantile_levels=list(_LEVELS),
                                  warmup=warmup)
            block = _trajectories(res)
            s = res.summary()
            block["final"] = {"mase": round(float(s["mase"]), 5) if s["mase"] == s["mase"] else None,
                              "coverage": round(float(s["coverage"]), 4),
                              "wql": round(float(s["wql"]), 5) if s["wql"] == s["wql"] else None}
            methods[name] = block
        except Exception as exc:  # noqa: BLE001 - record, never crash the bake
            methods[name] = {"error": f"{type(exc).__name__}: {exc}"}

    return {
        "nominal_coverage": _TARGET,
        "horizon": int(horizon),
        "warmup": int(warmup),
        "methods": methods,
        "references": {
            "prequential": "Dawid 1984, JRSS-A 147(2):278-292, DOI 10.2307/2981683",
            "aci": "Gibbs & Candes 2021, NeurIPS, arXiv:2106.00170",
            "conformal_pid": "Angelopoulos, Candes & Tibshirani 2023, NeurIPS, arXiv:2307.16895",
            "package": "preqts (PyPI), the extracted prequential harness",
        },
    }
