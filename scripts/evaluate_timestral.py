"""Evaluate pinned official Timestral checkpoints on unchanged admitted holdouts.

This is a new experiment, never an overwrite or enlargement of the historical
22-variant artifact. Model loading and forecasts execute in the named environment.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import platform
import time
from pathlib import Path

import numpy as np

from check_forecast_units import boundary
from check_fresh_reevaluation import recompute

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/research/timestral-v1/analysis-plan.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def forecast_case(forecaster, case: dict, settings: dict) -> dict:
    """Only the available prefix reaches the model; target access starts at scoring."""
    history = np.asarray(case["history"], dtype=np.float32)
    if history.ndim != 1 or not np.isfinite(history).all():
        raise ValueError("A finite contiguous history is required")
    start = time.perf_counter()
    prediction = forecaster.forecast(history, prediction_length=case["horizon"],
                                    symmetric_averaging=settings["symmetric_averaging"],
                                    clip_nonnegative=settings["clip_nonnegative"])
    raw = prediction.quantiles
    if hasattr(raw, "detach"):
        raw = raw.detach().cpu().numpy()
    raw = np.asarray(raw, dtype=float)
    seconds = time.perf_counter() - start
    levels = list(prediction.quantile_levels)
    if raw.shape != (1, 1, case["horizon"], 21) or len(levels) != 21:
        raise ValueError(f"Unexpected official quantile shape: {raw.shape}")
    if len(set(levels)) != 21 or levels != sorted(levels) or not np.isfinite(raw).all() or np.any(np.diff(raw, axis=-1) < 0):
        raise ValueError("Nonfinite or crossing official quantiles")
    ids = [levels.index(p) for p in settings["probabilities"]]
    q = raw[0, 0][:, ids]
    method = {"name": "Timestral", "lower": q[:, 0].tolist(), "point": q[:, 1].tolist(), "upper": q[:, 2].tolist()}
    advisories = boundary.require_forecast_units([*case["history"], *case["actual"]], [method])
    scores = recompute(case["history"], case["actual"], method["lower"], method["point"], method["upper"], case["seasonality"])
    if any(v is None or not np.isfinite(v) for v in scores.values()):
        raise ValueError("Unavailable score in a required model/case cell")
    return {"case_id": case["case_id"], "history_length": len(history), "horizon": case["horizon"],
            "seasonality": case["seasonality"], "history_sha256": hashlib.sha256(history.tobytes()).hexdigest(),
            "quantile_levels": levels, "quantiles": raw[0, 0].tolist(),
            **method, "metrics": scores, "forecast_seconds": seconds, "unit_advisories": advisories}


def summarize(rows: list[dict], baseline: dict, plan: dict) -> dict:
    cases = {c["case_id"]: c for c in baseline["cases"]}
    real = set(plan["reference"]["authentic_case_ids"])
    comparisons, summaries = [], []
    generator = np.random.Generator(np.random.PCG64(plan["forecast"]["seed"]))
    count = len(cases)
    draws = generator.integers(0, count, size=(10000, count))
    for model in rows:
        by_id = {r["case_id"]: r for r in model["cases"]}
        if len(by_id) != count or set(by_id) != set(cases):
            raise ValueError("An incomplete or duplicated model-case roster cannot be summarized")
        groups = {"all15": list(cases), "authentic4": [k for k in cases if k in real],
                  "generated11": [k for k in cases if k not in real]}
        for group, ids in groups.items():
            summaries.append({"model": model["repo"], "group": group, "cases": len(ids),
                              "mean_metrics": {key: float(np.mean([by_id[k]["metrics"][key] for k in ids]))
                                               for key in by_id[ids[0]]["metrics"]}})
        reference_names = [m["name"] for m in baseline["cases"][0]["methods"]]
        for name in reference_names:
            deltas = {metric: np.array([by_id[k]["metrics"][metric] -
                                       next(m for m in cases[k]["methods"] if m["name"] == name)["metrics"][metric]
                                       for k in cases]) for metric in ("mase", "msis", "coverage")}
            for metric, values in deltas.items():
                row = {"model": model["repo"], "control": name, "metric": metric,
                       "mean_difference": float(values.mean()), "negative": int(np.sum(values < 0)),
                       "zero": int(np.sum(values == 0)), "positive": int(np.sum(values > 0)), "cases": count}
                if name == "AutoTheta" and metric in ("mase", "msis"):
                    row["case_reweighting_percentile_95"] = np.quantile(values[draws].mean(axis=1), [.025, .975]).tolist()
                comparisons.append(row)
    return {"summaries": summaries, "paired_comparisons": comparisons,
            "uncertainty_scope": "Unadjusted joint reweighting of fifteen selected cases; not population confidence"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-cache", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.cache, args.model_cache, args.output):
        if path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Use external model, execution-cache and candidate paths")
    import torch
    import timestral
    from huggingface_hub import snapshot_download
    from timestral import TimestralForecaster

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    source = ROOT / plan["reference"]["path"]
    assert digest(source) == plan["reference"]["sha256"], "Reference holdouts changed"
    baseline = json.loads(source.read_text(encoding="utf-8"))
    assert [c["case_id"] for c in baseline["cases"]] == plan["reference"]["cases"]
    torch.set_num_threads(plan["forecast"]["torch_threads"])
    torch.set_num_interop_threads(plan["forecast"]["torch_interop_threads"])
    torch.manual_seed(plan["forecast"]["seed"])
    package = Path(timestral.__file__).parent
    source_hashes = {p.relative_to(package).as_posix(): digest(p) for p in sorted(package.rglob("*.py"))}
    assert source_hashes == plan["source_code"]["module_sha256"], "Installed Timestral source differs from the pinned code"
    runtime = {"python": platform.python_version(), "platform": platform.platform(), "processor": platform.processor(),
               "packages": {p: importlib.metadata.version(p) for p in ("numpy", "torch", "timestral", "safetensors", "huggingface_hub")},
               "torch_threads": torch.get_num_threads(), "device": "cpu", "timestral_module_sha256": source_hashes}
    binding = {"plan_sha256": digest(PLAN), "reference_sha256": digest(source), "code_sha256": digest(Path(__file__)),
               "scoring_sha256": digest(ROOT / "scripts/check_fresh_reevaluation.py"),
               "unit_boundary_sha256": digest(ROOT / "data-pipeline/chronoscopelab/io/units.py"), "runtime": runtime}
    identity = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    rows = []
    for model in plan["models"]:
        print(f"Loading {model['repo']} at {model['revision']}", flush=True)
        checkpoint = Path(snapshot_download(model["repo"], revision=model["revision"], cache_dir=args.model_cache,
                                            allow_patterns=["config.json", "model.safetensors", "LICENSE"], token=False))
        hashes = {name: digest(checkpoint / name) for name in ("config.json", "model.safetensors", "LICENSE")}
        start = time.perf_counter()
        forecaster = TimestralForecaster.from_pretrained(checkpoint, device="cpu")
        load_seconds = time.perf_counter() - start
        result = {**model, "checkpoint_sha256": hashes, "load_seconds_excluding_download": load_seconds, "cases": []}
        for case in baseline["cases"]:
            cache = args.cache / identity / model["repo"].split("/")[-1] / f"{case['case_id']}.json"
            if cache.exists():
                row = json.loads(cache.read_text(encoding="utf-8"))
            else:
                row = forecast_case(forecaster, case, plan["forecast"])
                row["name"] = model["repo"].split("/")[-1]
                write(cache, row)
            result["cases"].append(row)
            print(f"  {case['case_id']}: MASE={row['metrics']['mase']:.6f} MSIS={row['metrics']['msis']:.6f}", flush=True)
        rows.append(result)
        write(args.output.with_suffix(".partial.json"), {"state": "partial trial, not admitted", **binding, "models": rows})
        del forecaster
        gc.collect()
    assert sum(len(row["cases"]) for row in rows) == plan["admission"]["required_model_cases"]
    assert digest(source) == binding["reference_sha256"], "The immutable reference changed during inference"
    result = {"schema": "chronoscope-timestral-common-holdout/v1", "state": "complete candidate; independent validation pending",
              "identity": identity, **binding, "models": rows, **summarize(rows, baseline, plan)}
    write(args.output, result)
    print(json.dumps({"state": result["state"], "model_cases": 60, "output": str(args.output)}), flush=True)


if __name__ == "__main__":
    main()
