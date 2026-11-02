"""Fresh fits/inference for the entire released roster on verified original final blocks.

Writes only an explicitly named external candidate. Per-method caches are tied to all
implementation, input, package and checkpoint identities; incomplete runs never promote.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

import numpy as np  # noqa: E402

from chronoscopelab.methods import all_forecasters  # noqa: E402
from chronoscopelab.model.context_memory import EXPERT_NAMES, fit_context_memory  # noqa: E402
from chronoscopelab.reevaluation import metrics  # noqa: E402

PACKAGES = ("numpy", "scipy", "pandas", "torch", "statsforecast", "lightgbm", "mlforecast",
            "neuralforecast", "chronos-forecasting", "timesfm", "tirex-2", "transformers", "preqts")
MODEL_IDS = ("amazon/chronos-bolt-small", "amazon/chronos-2", "google/timesfm-2.5-200m-pytorch", "NX-AI/TiRex-2")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def runtime():
    import torch
    from huggingface_hub import HfApi

    torch.set_num_threads(4)
    # Bound compiler workers before a pretrained model first invokes torch.compile.
    os.environ["TORCHINDUCTOR_COMPILE_THREADS"] = "1"
    revisions = {name: HfApi().model_info(name).sha for name in MODEL_IDS}
    model_root = Path(os.environ["CHRONOSCOPE_MODEL_ROOT"])
    weights = {}
    for name, folder in zip(MODEL_IDS[:3], ("chronos-bolt-small", "chronos-2", "timesfm-2.5"), strict=True):
        directory = model_root / folder
        recorded = (directory / ".cache/huggingface/download/config.json.metadata").read_text().splitlines()[0]
        if recorded != revisions[name]:
            raise ValueError(f"Downloaded checkpoint differs from recorded revision: {name}")
        weights[name] = {p.name: sha(p) for p in sorted(directory.iterdir()) if p.suffix in (".json", ".safetensors")}
    os.environ["CHRONOSCOPE_TIREX_REVISION"] = revisions[MODEL_IDS[-1]]
    return {"python": platform.python_version(), "platform": platform.system(), "torch_cpu_threads": 4,
            "packages": {p: importlib.metadata.version(p) for p in PACKAGES},
            "cuda_available": torch.cuda.is_available(), "torch_cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "checkpoint_revisions": revisions, "checkpoint_sha256": weights}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--case", help="Optional single-case trial; never a complete admitted comparison")
    args = parser.parse_args()
    output, cache = args.output.resolve(), args.cache_dir.resolve()
    if output.is_relative_to(ROOT) or cache.is_relative_to(ROOT):
        raise ValueError("Fresh evaluation candidates and caches must be external")
    data = json.loads((ROOT / "data/derived/reevaluation.json").read_text())
    base_hash = sha(ROOT / "data/derived/reevaluation.json")
    rt = runtime()
    paths = [*sorted((ROOT / "data-pipeline/chronoscopelab").rglob("*.py")), Path(__file__).resolve()]
    code = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    identity = {"source_artifact": base_hash, "runtime": rt, "code": code}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    forecasters = {f.name: f for f in all_forecasters()}
    expected = {r["name"] for r in data["summary"]}
    available = set(forecasters) | {"RecencyMean", "EqualMean"}
    if expected != available:
        raise ValueError(f"Incomplete or unexpected engines: missing={expected - available}, extra={available - expected}")
    if args.case:
        data["cases"] = [c for c in data["cases"] if c["case_id"] == args.case]
        if not data["cases"]:
            raise ValueError("Unknown trial case")
    for case in data["cases"]:
        history, actual = np.array(case["history"]), np.array(case["actual"])
        h, m = case["horizon"], case["seasonality"]
        rows = []
        for name in sorted(expected):
            destination = cache / fingerprint / case["case_id"] / f"{name}.json"
            if destination.is_file():
                row = json.loads(destination.read_text())
                metrics(history, actual, row["point"], row["lower"], row["upper"], m)
                rows.append(row)
                continue
            started = time.perf_counter()
            detail = {}
            with warnings.catch_warnings(record=True) as notices:
                warnings.simplefilter("always")
                if name in ("ContextMemory", "RecencyMean", "EqualMean"):
                    mode = {"ContextMemory": "context", "RecencyMean": "recency", "EqualMean": "uniform"}[name]
                    fitted = fit_context_memory(history, m, h, mode=mode)
                    q, family = fitted.quantiles, "adaptive ensemble"
                    detail = {"expert_weights": dict(zip(EXPERT_NAMES, fitted.weights.tolist(), strict=True)),
                              "training_origins": list(fitted.origins)}
                else:
                    fc = forecasters[name]
                    q, family = np.asarray(fc.quantiles(history, m, h, (0.1, 0.5, 0.9))), fc.family
            elapsed = time.perf_counter() - started
            score = metrics(history, actual, q[:, 1], q[:, 0], q[:, 2], m)
            row = {"name": name, "family": family, "source": "recomputed from current source",
                   "point": q[:, 1].tolist(), "lower": q[:, 0].tolist(), "upper": q[:, 2].tolist(),
                   "metrics": score, "fit_inference_seconds": elapsed,
                   "warning_categories": sorted({w.category.__name__ for w in notices}), **detail}
            write(destination, row)
            rows.append(row)
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"{case['case_id']} {name}: MASE={score['mase']:.4f}, seconds={elapsed:.2f}", flush=True)
        case["methods"] = rows
    if code != {p.relative_to(ROOT).as_posix(): sha(p) for p in paths} or base_hash != sha(ROOT / "data/derived/reevaluation.json"):
        raise ValueError("Source or input artifact changed during fresh evaluation; candidate refused")
    data["summary"] = []
    for name in sorted(expected):
        scores = [next(r["metrics"] for r in c["methods"] if r["name"] == name) for c in data["cases"]]
        data["summary"].append({"name": name, "cases": len(scores),
                                "mean_mase": float(np.mean([s["mase"] for s in scores if s["mase"] is not None])),
                                "mean_coverage": float(np.mean([s["coverage"] for s in scores]))})
    data["protocol"]["name"] = "fresh common final holdout" if not args.case else "single-case fresh trial"
    data["protocol"]["heavy_forecasts"] = "All model paths freshly fitted or inferred; exact package and checkpoint identities are included."
    data["protocol"]["limits"] += " Timings include fitting, inference and first-use imports/model loading; they are not warm-inference benchmarks."
    data["code_sha256"], data["runtime"], data["source_comparison_sha256"] = code, rt, base_hash
    write(output, data)
    print(f"Complete candidate: {len(data['cases'])} cases, {len(expected)} methods", flush=True)


if __name__ == "__main__":
    main()
