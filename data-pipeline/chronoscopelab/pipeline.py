"""The offline pipeline orchestrator + CLI (ADR-0057). Runs the named stages per case, applies CONTRACT 1,
writes the compact artifact + manifest (CONTRACT 2) and a flat index.json.

    python -m chronoscopelab.pipeline                 # all cases
    python -m chronoscopelab.pipeline SEAS_hourly --seed 7
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from . import registry
from .core.manifest import build_index
from .io.contract import validate_series
from .io.formats import write_json
from .stages import evaluate, export, feature_extraction, infer, train

# data-pipeline/chronoscopelab/pipeline.py -> parents[2] = repo root (works under `pip install -e .` too)
REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED = REPO_ROOT / "data" / "derived"
MANIFESTS = DERIVED / "manifests"
MODELS = REPO_ROOT / "models"

STAGES = ("preprocess", "feature_extraction", "train", "infer", "evaluate", "export")
QUANTILE_LEVELS = (0.1, 0.5, 0.9)


def _train_selector(seed: int) -> dict:
    # Learn the global method ranking from the SYNTHETIC training cases only (leakage-safe: real cases
    # are scored on their own held-out windows, never used to pick the global default).
    specs = [registry.build_series(c, seed=seed) for c in registry.list_cases()
             if c.real_or_synthetic == "synthetic"]
    return train.run(specs, str(MODELS), QUANTILE_LEVELS)


def precompute(case_id: str, seed: int = 42, selector: dict | None = None) -> dict:
    case = registry.get_case(case_id)
    if selector is None:
        selector = _train_selector(seed)
    t0 = time.perf_counter()
    spec = registry.build_series(case, seed=seed)

    # CONTRACT 1 on the produced series (proves the gate + carries flags); BYO data enters the same way.
    ds = [str(i) for i in range(len(spec.y))]
    _rec, _rej, flag = validate_series(spec.case_id, ds, list(spec.y))
    flags = [flag] if flag else []

    feature = feature_extraction.run(spec)
    result = infer.run(spec, QUANTILE_LEVELS)
    _history, actual = infer.split(spec)
    eval_metrics = evaluate.run(spec, QUANTILE_LEVELS)
    run_ms = (time.perf_counter() - t0) * 1000.0

    return export.run(
        case=case, feature=feature, result=result, actual=[float(v) for v in actual],
        eval_metrics=eval_metrics, seed=seed, run_ms=run_ms, flags=flags,
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS),
    )


def run_all(seed: int = 42) -> list[dict]:
    selector = _train_selector(seed)
    entries = []
    for c in registry.list_cases():
        precompute(c.id, seed=seed, selector=selector)
        entries.append({"case_id": c.id, "category": c.category, "manifest_path": f"manifests/{c.id}.json"})
    write_json(MANIFESTS / "index.json", build_index(entries))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(prog="chronoscopelab.pipeline")
    ap.add_argument("case", nargs="?", default="all", help="a case id, or 'all'")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    if args.case == "all":
        entries = run_all(args.seed)
        print(f"precomputed {len(entries)} cases -> {DERIVED}")
        for e in entries:
            print(f"  {e['case_id']:20s} [{e['category']}]")
        print(f"index -> {MANIFESTS / 'index.json'}")
    else:
        m = precompute(args.case, args.seed)
        print(f"precomputed {args.case}: lane={m['lane']} bytes={m['artifact']['bytes']} "
              f"best={m['best_method']} best_mase={m['metrics']['best_mase']} "
              f"-> {DERIVED / m['artifact']['path']}")


if __name__ == "__main__":
    main()
