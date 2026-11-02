"""Admit a complete fresh comparison: exact sources, original targets and independently recomputed scores."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"amazon/chronos-bolt-small", "amazon/chronos-2", "google/timesfm-2.5-200m-pytorch", "NX-AI/TiRex-2"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute(history, actual, lower, point, upper, lag):
    h = len(actual)
    if not h or any(len(v) != h for v in (lower, point, upper)):
        raise ValueError("Incomplete fresh forecast horizon")
    if not all(math.isfinite(x) for a in (history, actual, lower, point, upper) for x in a):
        raise ValueError("Non-finite fresh values")
    if any(not lo <= p <= hi for lo, p, hi in zip(lower, point, upper, strict=True)):
        raise ValueError("Crossed fresh quantiles")
    scale = math.fsum(abs(history[i] - history[i - lag]) for i in range(lag, len(history))) / (len(history) - lag)
    mae = math.fsum(abs(a - p) for a, p in zip(actual, point, strict=True)) / h
    score = math.fsum(hi - lo + 10 * max(lo - a, 0) + 10 * max(a - hi, 0)
                      for a, lo, hi in zip(actual, lower, upper, strict=True)) / h
    target_scale = math.fsum(abs(a) for a in actual)
    pinball = math.fsum(max(q * (a - p), (q - 1) * (a - p))
                        for q, forecast in zip((0.1, 0.5, 0.9), (lower, point, upper), strict=True)
                        for a, p in zip(actual, forecast, strict=True))
    return {"mae": mae, "rmse": math.sqrt(math.fsum((a - p) ** 2 for a, p in zip(actual, point, strict=True)) / h),
            "mase": mae / scale if scale > 1e-12 else None,
            "coverage": sum(lo <= a <= hi for a, lo, hi in zip(actual, lower, upper, strict=True)) / h,
            "mean_width": math.fsum(hi - lo for lo, hi in zip(lower, upper, strict=True)) / h,
            "msis": score / scale if scale > 1e-12 else None,
            "wql": 2 * pinball / (3 * target_scale) if target_scale > 1e-12 else None}


def validate(document, root=ROOT, artifact_root=None):
    artifact_root = root if artifact_root is None else artifact_root
    baseline = read(artifact_root / "data/derived/reevaluation.json")
    if document["protocol"]["name"] != "fresh common final holdout":
        raise ValueError("A trial is not a complete fresh comparison")
    if document["protocol"]["forecast_origins_per_case"] != 1 or document["protocol"]["quantile_levels"] != [0.1, 0.5, 0.9]:
        raise ValueError("Fresh scoring protocol differs")
    if document["source_comparison_sha256"] != digest(artifact_root / "data/derived/reevaluation.json"):
        raise ValueError("Fresh comparison source artifact is stale")
    expected = {p.relative_to(root).as_posix() for p in (root / "data-pipeline/chronoscopelab").rglob("*.py")}
    expected.add("scripts/reevaluate_fresh.py")
    if set(document["code_sha256"]) != expected:
        raise ValueError("Fresh implementation binding inventory is incomplete")
    for key in ("trace_sha256", "input_sha256"):
        if document[key] != baseline[key]:
            raise ValueError("Fresh source inventory differs from the admitted comparison")
    for bindings, base in ((document["code_sha256"], root),
                           ({**document["trace_sha256"], **document["input_sha256"]}, artifact_root)):
        for rel, value in bindings.items():
            path = (base / rel).resolve()
            if not path.is_relative_to(base.resolve()) or digest(path) != value:
                raise ValueError(f"Fresh source binding differs: {rel}")
    revisions = document["runtime"]["checkpoint_revisions"]
    if set(revisions) != MODELS or any(len(v) != 40 or set(v) - set("0123456789abcdef") for v in revisions.values()):
        raise ValueError("Fresh checkpoint revisions are incomplete or invalid")
    cases = {c["case_id"]: c for c in baseline["cases"]}
    ids = [c["case_id"] for c in document["cases"]]
    if set(ids) != set(cases) or len(ids) != len(cases):
        raise ValueError("Fresh case inventory is incomplete or duplicated")
    names = {r["name"] for r in baseline["summary"]}
    by_method = {name: [] for name in names}
    for case in document["cases"]:
        original = cases[case["case_id"]]
        for key in ("history", "history_length", "actual", "horizon", "seasonality"):
            if case[key] != original[key]:
                raise ValueError(f"Fresh fitting information or target differs: {case['case_id']} {key}")
        roster = [m["name"] for m in case["methods"]]
        if set(roster) != names or len(roster) != len(names):
            raise ValueError("Fresh method inventory is incomplete or duplicated")
        for method in case["methods"]:
            if method["source"] != "recomputed from current source":
                raise ValueError("A frozen model path cannot be admitted as a fresh execution")
            seconds = method["fit_inference_seconds"]
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError("Invalid fresh execution duration")
            scores = recompute(case["history"], case["actual"], method["lower"], method["point"], method["upper"], case["seasonality"])
            for key, value in scores.items():
                given = method["metrics"][key]
                if (given is None) != (value is None) or (value is not None and not math.isclose(value, given, rel_tol=1e-9, abs_tol=1e-9)):
                    raise ValueError(f"Fresh metric differs: {case['case_id']} {method['name']} {key}")
            if "training_origins" in method and any(o + case["horizon"] > len(case["history"]) for o in method["training_origins"]):
                raise ValueError("Fresh combination contains an incomplete historical target")
            by_method[method["name"]].append(scores)
    summaries = {row["name"]: row for row in document["summary"]}
    if set(summaries) != names or len(document["summary"]) != len(names):
        raise ValueError("Fresh aggregate inventory is incomplete")
    for name, scores in by_method.items():
        row = summaries[name]
        valid = [s["mase"] for s in scores if s["mase"] is not None]
        if row["cases"] != len(cases) or not math.isclose(row["mean_mase"], math.fsum(valid) / len(valid), rel_tol=1e-9):
            raise ValueError("Fresh aggregate MASE differs")
        if not math.isclose(row["mean_coverage"], math.fsum(s["coverage"] for s in scores) / len(scores), rel_tol=1e-9):
            raise ValueError("Fresh aggregate coverage differs")
    return len(cases), len(names)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/derived/fresh-reevaluation.json"
    counts = validate(read(path))
    print(f"Fresh comparison: {counts[0]} cases, {counts[1]} freshly executed variants; all metrics independently match")
