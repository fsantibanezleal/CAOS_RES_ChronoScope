"""Independently score the retained Timestral quantiles on the frozen holdouts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/research/timestral-v1"
SOURCE_PATHS = {
    "plan_sha256": "docs/research/timestral-v1/analysis-plan.json",
    "code_sha256": "scripts/evaluate_timestral.py",
    "scoring_sha256": "scripts/check_fresh_reevaluation.py",
    "unit_boundary_sha256": "data-pipeline/chronoscopelab/io/units.py",
}
SCALE_FREE = {"coverage", "mase", "msis", "wql"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"{label}: {actual!r} differs from {expected!r}")


def scores(case: dict, row: dict) -> dict[str, float]:
    history, targets = case["history"], case["actual"]
    lower, point, upper = row["lower"], row["point"], row["upper"]
    lag = case["seasonality"]
    scale = statistics.mean(abs(a - b) for a, b in zip(history[lag:], history[:-lag], strict=True))
    mass = math.fsum(map(abs, targets))
    if min(scale, mass) <= 1e-12:
        raise ValueError("An admitted holdout has an unavailable reference scale")
    errors = [a - p for a, p in zip(targets, point, strict=True)]
    widths = [u - l for l, u in zip(lower, upper, strict=True)]
    misses = [max(l - a, a - u, 0.0) for a, l, u in zip(targets, lower, upper, strict=True)]
    pinball = 0.0
    for q, path in zip((0.1, 0.5, 0.9), (lower, point, upper), strict=True):
        pinball += math.fsum((q if a >= p else q - 1.0) * (a - p) for a, p in zip(targets, path, strict=True))
    mae = statistics.mean(map(abs, errors))
    return {
        "mae": mae,
        "rmse": math.sqrt(statistics.mean(e * e for e in errors)),
        "mase": mae / scale,
        "coverage": statistics.mean(m == 0.0 for m in misses),
        "mean_width": statistics.mean(widths),
        "msis": (statistics.mean(widths) + 10.0 * statistics.mean(misses)) / scale,
        "wql": 2.0 * pinball / (3.0 * mass),
    }


def validate(document: dict, *, reweight: bool = False) -> int:
    plan = load(FOLDER / "analysis-plan.json")
    reference_path = ROOT / plan["reference"]["path"]
    cases = load(reference_path)["cases"]
    source_paths = {**SOURCE_PATHS, "reference_sha256": plan["reference"]["path"]}
    binding = {key: digest(ROOT / path) for key, path in source_paths.items()}
    if binding["reference_sha256"] != plan["reference"]["sha256"]:
        raise ValueError("The holdout reference differs from the pre-inference plan")
    if any(document[key] != value for key, value in binding.items()):
        raise ValueError("Stale Timestral execution bindings")
    runtime = document["runtime"]
    binding["runtime"] = runtime
    identity = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    if identity != document["identity"] or runtime["timestral_module_sha256"] != plan["source_code"]["module_sha256"]:
        raise ValueError("Runtime or source identity differs")
    if runtime["device"] != "cpu" or runtime["torch_threads"] != plan["forecast"]["torch_threads"]:
        raise ValueError("The recorded inference device or thread count differs from the plan")
    if [c["case_id"] for c in cases] != plan["reference"]["cases"]:
        raise ValueError("The holdout identity or case order differs")
    if document["schema"] != "chronoscope-timestral-common-holdout/v1":
        raise ValueError("Unknown Timestral evidence family")
    n = len(cases)
    authentic = set(plan["reference"]["authentic_case_ids"])
    groups = {"all15": list(range(n)), "authentic4": [], "generated11": []}
    for i, case in enumerate(cases):
        groups["authentic4" if case["case_id"] in authentic else "generated11"].append(i)
    summaries = {(r["model"], r["group"]): r for r in document["summaries"]}
    pairs = {(r["model"], r["control"], r["metric"]): r for r in document["paired_comparisons"]}
    reference_names = [m["name"] for m in cases[0]["methods"]]
    if len(summaries) != len(document["summaries"]) or len(pairs) != len(document["paired_comparisons"]):
        raise ValueError("Duplicated Timestral summary or paired comparison")
    if len(summaries) != len(plan["models"]) * len(groups) or len(pairs) != len(plan["models"]) * len(reference_names) * 3:
        raise ValueError("The Timestral summary and comparator rosters must be complete")
    if reweight:
        import numpy as np

        rng = np.random.Generator(np.random.PCG64(plan["forecast"]["seed"]))
        draw_indices = rng.integers(0, n, size=(10000, n))
    count = 0
    for model, expected in zip(document["models"], plan["models"], strict=True):
        if any(model[key] != expected[key] for key in ("repo", "revision")):
            raise ValueError("Model or checkpoint revision differs from the plan")
        hashes = model["checkpoint_sha256"]
        if set(hashes) != {"config.json", "model.safetensors", "LICENSE"} or not all(
            re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values()
        ):
            raise ValueError("Checkpoint hash inventory is incomplete")
        independent = []
        for case, row in zip(cases, model["cases"], strict=True):
            name = model["repo"].split("/")[-1]
            if row["name"] != name or any(row[key] != case[key] for key in ("case_id", "horizon", "seasonality")):
                raise ValueError("A model-case result acquired a different identity")
            history = case["history"]
            history_hash = hashlib.sha256(struct.pack(f"<{len(history)}f", *history)).hexdigest()
            if row["history_length"] != len(history) or row["history_sha256"] != history_hash:
                raise ValueError("The model did not bind the complete contiguous float32 history")
            q = row["quantile_levels"]
            if len(q) != 21 or q != sorted(set(q)) or not all(0 < x < 1 for x in q):
                raise ValueError("Invalid quantile probability grid")
            quantiles = row["quantiles"]
            if len(quantiles) != case["horizon"] or any(
                len(v) != 21 or v != sorted(v) or not all(map(math.isfinite, v)) for v in quantiles
            ):
                raise ValueError("Incomplete, crossed or nonfinite quantile paths")
            for level, field in zip(plan["forecast"]["probabilities"], ("lower", "point", "upper"), strict=True):
                if [v[q.index(level)] for v in quantiles] != row[field]:
                    raise ValueError("A scored quantile differs from the retained output")
            expected_scores = scores(case, row)
            if set(row["metrics"]) != set(expected_scores):
                raise ValueError("Missing or extra case metrics")
            for metric, value in expected_scores.items():
                close(row["metrics"][metric], value, f"{name}/{case['case_id']}/{metric}")
            independent.append(expected_scores)
            count += 1
        for group, indices in groups.items():
            summary = summaries[model["repo"], group]
            if summary["cases"] != len(indices) or set(summary["mean_metrics"]) != SCALE_FREE:
                raise ValueError("A summary has invalid case counts or mixes physical units")
            for metric in SCALE_FREE:
                close(summary["mean_metrics"][metric], statistics.mean(independent[i][metric] for i in indices), metric)
        for control in reference_names:
            for metric in ("mase", "msis", "coverage"):
                pair = pairs[model["repo"], control, metric]
                # Direction counts use the exact recorded case values after verifying them above.
                differences = [r["metrics"][metric] - next(m for m in c["methods"] if m["name"] == control)["metrics"][metric]
                               for r, c in zip(model["cases"], cases, strict=True)]
                close(pair["mean_difference"], statistics.mean(differences), f"{control}/{metric}")
                counts = [sum(d < 0 for d in differences), sum(d == 0 for d in differences), sum(d > 0 for d in differences)]
                if [pair[k] for k in ("negative", "zero", "positive")] != counts or pair["cases"] != n:
                    raise ValueError("Paired direction counts differ")
                if reweight and control == "AutoTheta" and metric != "coverage":
                    draws = np.asarray(differences)[draw_indices].mean(axis=1)
                    bounds = np.quantile(draws, [0.025, 0.975])
                    for actual, expected_bound in zip(pair["case_reweighting_percentile_95"], bounds, strict=True):
                        close(actual, float(expected_bound), "paired case-reweighting bound")
    if count != plan["admission"]["required_model_cases"]:
        raise ValueError("Incomplete model-case matrix")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", nargs="?", type=Path, default=FOLDER / "results.json")
    parser.add_argument("--reweight", action="store_true", help="recompute the seeded percentile intervals with NumPy")
    args = parser.parse_args()
    count = validate(load(args.result), reweight=args.reweight)
    print(f"Timestral: {count} model-case rows rescored; complete matched comparator matrix")


if __name__ == "__main__":
    main()
