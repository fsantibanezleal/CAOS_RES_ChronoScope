"""Score the released forecast paths and current light methods on identical final holdouts.

Frozen heavy forecasts are rescored, not represented as new fits. Original traces stay
unchanged and their hashes bind this comparison to the exact historical inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from .model.context_memory import CONFIG, EXPERT_NAMES, fit_context_memory
from .model.forecasters import METHODS, gaussian_quantiles

SCHEMA = "chronoscope.reevaluation/v1"


def metrics(history, actual, point, lower, upper, seasonality):
    history, actual, point, lower, upper = [np.asarray(v, dtype=float) for v in (history, actual, point, lower, upper)]
    if (not len(actual) or any(a.shape != actual.shape for a in (point, lower, upper))
            or not all(np.isfinite(a).all() for a in (history, actual, point, lower, upper))
            or np.any(lower > point) or np.any(point > upper)):
        raise ValueError("Forecast shape, finiteness or quantile ordering is invalid")
    lag = max(1, min(int(seasonality), len(history) - 1))
    scale = float(np.mean(np.abs(history[lag:] - history[:-lag])))
    error = actual - point
    covered = (actual >= lower) & (actual <= upper)
    interval_score = upper - lower + 10 * np.maximum(lower - actual, 0) + 10 * np.maximum(actual - upper, 0)
    qs = np.column_stack((lower, point, upper))
    residual = actual[:, None] - qs
    pinball = np.maximum(np.array([0.1, 0.5, 0.9]) * residual, (np.array([0.1, 0.5, 0.9]) - 1) * residual)
    denominator = float(np.sum(np.abs(actual)))
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "mase": float(np.mean(np.abs(error)) / scale) if scale > 1e-12 else None,
        "coverage": float(np.mean(covered)),
        "mean_width": float(np.mean(upper - lower)),
        "msis": float(np.mean(interval_score) / scale) if scale > 1e-12 else None,
        "wql": float(2 * np.sum(pinball) / (3 * denominator)) if denominator > 1e-12 else None,
    }


def compare_case(trace):
    history, actual = np.asarray(trace["history"]), np.asarray(trace["actual"])
    m, h = int(trace["seasonality"]), int(trace["horizon"])
    if trace.get("redacted") or len(actual) != h:
        raise ValueError("A redacted or incomplete case needs locally admitted raw inputs before reevaluation")
    rows = []
    current_names = {name for name, _, _ in METHODS}
    for old in trace["methods"]:
        if old["name"] in current_names:
            continue
        point, lower, upper = [old[key] for key in ("point", "lower", "upper")]
        rows.append({"name": old["name"], "family": old["family"], "source": "frozen released forecast",
                     "point": point, "lower": lower, "upper": upper,
                     "metrics": metrics(history, actual, point, lower, upper, m)})
    for name, family, fn in METHODS:
        point, sigma = fn(history, m, h)
        quantiles = gaussian_quantiles(point, sigma, (0.1, 0.5, 0.9))
        rows.append({"name": name, "family": family, "source": "recomputed from current source",
                     "point": point.tolist(), "lower": quantiles[:, 0].tolist(), "upper": quantiles[:, 2].tolist(),
                     "metrics": metrics(history, actual, point, quantiles[:, 0], quantiles[:, 2], m)})
    for name, mode in (("ContextMemory", "context"), ("RecencyMean", "recency"), ("EqualMean", "uniform")):
        fit = fit_context_memory(history, m, h, mode=mode)
        lo, point, hi = fit.quantiles.T
        rows.append({"name": name, "family": "adaptive ensemble", "source": "recomputed from current source",
                     "point": point.tolist(), "lower": lo.tolist(), "upper": hi.tolist(),
                     "metrics": metrics(history, actual, point, lo, hi, m),
                     "expert_weights": dict(zip(EXPERT_NAMES, fit.weights.tolist(), strict=True)),
                     "training_origins": list(fit.origins)})
    counts = {row["name"]: row.get("backtest", {}).get("n_windows") for row in trace["methods"]}
    return {"case_id": trace["case_id"], "seasonality": m, "horizon": h,
            "history_length": len(history), "actual": actual.tolist(), "methods": rows,
            "legacy_backtest_window_counts": counts}


def build(root: Path):
    index = json.loads((root / "data/derived/manifests/index.json").read_text(encoding="utf-8"))
    cases, hashes = [], {}
    for row in index["cases"]:
        rel = f"data/derived/{row['case_id']}/trace.json"
        raw = (root / rel).read_bytes()
        hashes[rel] = hashlib.sha256(raw).hexdigest()
        case = compare_case(json.loads(raw))
        case["category"] = row["category"]
        cases.append(case)
    source_paths = ["data-pipeline/chronoscopelab/reevaluation.py",
                    "data-pipeline/chronoscopelab/model/forecasters.py",
                    "data-pipeline/chronoscopelab/model/context_memory.py"]
    sources = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in source_paths}
    names = sorted({m["name"] for c in cases for m in c["methods"]})
    summary = []
    for name in names:
        scores = [next(m["metrics"] for m in c["methods"] if m["name"] == name) for c in cases
                  if any(m["name"] == name for m in c["methods"])]
        summary.append({"name": name, "cases": len(scores), "mean_mase": float(np.mean([s["mase"] for s in scores if s["mase"] is not None])),
                        "mean_coverage": float(np.mean([s["coverage"] for s in scores]))})
    return {"schema": SCHEMA, "protocol": {
        "name": "common final holdout", "forecast_origins_per_case": 1, "quantile_levels": [0.1, 0.5, 0.9],
        "heavy_forecasts": "Rescored from frozen released paths; no new fitting or pretraining-data audit is implied.",
        "light_forecasts": "Recomputed on the exact committed history; the final holdout is never supplied to fit.",
        "limits": "Fifteen selected cases and one origin per case do not establish population superiority or significance.",
        "context_memory": CONFIG}, "source_engine_version": index["engine_version"],
        "trace_sha256": hashes, "code_sha256": sources, "cases": cases, "summary": summary}
