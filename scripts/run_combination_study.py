"""Evaluate fixed prefix-validated combinations on complete new external corpora.

Raw sources and resumable per-series audits live outside the repository. A cache
identity binds source bytes, protocol, implementation and dependency versions.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import warnings

for variable in ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(variable, "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

import numpy as np  # noqa: E402
from chronoscopelab.model.context_memory import fit_context_memory  # noqa: E402
from chronoscopelab.model.forecasters import METHODS, gaussian_quantiles  # noqa: E402
from chronoscopelab.model.validated_combination import fit_validated  # noqa: E402
from chronoscopelab.reevaluation import metrics  # noqa: E402
from run_forecastability_study import series_from_tsf  # noqa: E402
from accelerate_expert_loops import enable as accelerate  # noqa: E402

DATASETS = {
    "m4_weekly": {"record": 4656522, "file": "m4_weekly_dataset.tsf", "count": 359, "horizon": 13, "seasonality": 52},
    "m3_monthly": {"record": 4656298, "file": "m3_monthly_dataset.tsf", "count": 1428, "horizon": 18, "seasonality": 12},
}
PROTOCOL = {"context_cap": 512, "max_origins": 3, "scale": "seasonal difference of the supplied prefix",
            "loop_execution": "unchanged recursive expert loops compiled by Numba without fastmath; reference parity tested",
            "primary": "ValidationMix versus RecencyMean mean series MASE, separately per dataset",
            "selection": "completed historical targets only; no outer target selects a configuration"}
SOURCE_FILES = ["scripts/run_combination_study.py", "data-pipeline/chronoscopelab/model/validated_combination.py",
                "scripts/accelerate_expert_loops.py",
                "data-pipeline/chronoscopelab/model/context_memory.py", "data-pipeline/chronoscopelab/model/forecasters.py",
                "data-pipeline/chronoscopelab/reevaluation.py"]
NAMES = [*(name for name, _, _ in METHODS), "AutoETS", "AutoTheta", "ContextMemory", "RecencyMean", "EqualMean", "ContextMemoryCV", "ValidationMix"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def schedule(length, horizon, seasonality):
    minimum = max(2 * seasonality, 2 * horizon + 8, 24)
    return tuple(o for o in (length - j * horizon for j in (3, 2, 1)) if o >= minimum)


def evaluate(job):
    dataset, name, timestamp, y, destination = job
    path = Path(destination) / dataset / (name + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    accelerate()
    spec = DATASETS[dataset]
    h, m = spec["horizon"], spec["seasonality"]
    row = {"id": name, "dataset": dataset, "start_timestamp": timestamp, "source_n": len(y),
           "sequence_sha256": hashlib.sha256(np.asarray(y, dtype="<f8").tobytes()).hexdigest(), "origins": []}
    origins = schedule(len(y), h, m)
    if not np.isfinite(y).all() or not origins:
        row["excluded"] = "nonfinite observations or no eligible origin"
        write(path, row)
        return row
    started = time.perf_counter()
    for origin in origins:
        prefix = np.asarray(y[max(0, origin-PROTOCOL["context_cap"]):origin])
        actual = np.asarray(y[origin:origin+h])
        scale = float(np.mean(abs(prefix[m:] - prefix[:-m])))
        if not np.isfinite(scale) or scale <= 1e-12:
            row["excluded"] = "unavailable seasonal MASE scale at an outer origin"
            write(path, row)
            return row
        result = {"origin": origin, "prefix_start": max(0, origin-len(prefix)), "prefix_length": len(prefix),
                  "prefix_sha256": hashlib.sha256(prefix.astype('<f8').tobytes()).hexdigest(),
                  "scale": scale, "actual": actual.tolist(), "methods": []}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            forecasts = {}
            for name_, _, fn in METHODS:
                forecasts[name_] = (gaussian_quantiles(*fn(prefix, m, h), (.1, .5, .9)), {})
            from statsforecast.models import AutoETS, AutoTheta
            for model_name, model_class in (("AutoETS", AutoETS), ("AutoTheta", AutoTheta)):
                model = model_class(season_length=m)
                model.fit(prefix)
                p = model.predict(h, level=[80])
                forecasts[model_name] = (np.column_stack([p['lo-80'], p['mean'], p['hi-80']]), {})
            for model_name, mode in (("ContextMemory", "context"), ("RecencyMean", "recency"), ("EqualMean", "uniform")):
                fit = fit_context_memory(prefix, m, h, mode=mode)
                forecasts[model_name] = (fit.quantiles, {"weights": fit.weights.tolist(), "memory_origins": list(fit.origins)})
            for model_name, stacking in (("ContextMemoryCV", False), ("ValidationMix", True)):
                fit = fit_validated(prefix, m, h, stacking=stacking)
                forecasts[model_name] = (fit.quantiles, {"weights": fit.weights.tolist(), "selected": fit.selected,
                    "validation": fit.candidates, "validation_splits": fit.validation_splits, "memory_origins": fit.origins})
            for model_name in NAMES:
                q, details = forecasts[model_name]
                assert q.shape == (h, 3) and np.isfinite(q).all() and np.all(np.diff(q, axis=1) >= 0), model_name
                score = metrics(prefix, actual, q[:, 1], q[:, 0], q[:, 2], m)
                result["methods"].append({"name": model_name, "quantiles": q.tolist(), "metrics": score, **details})
            result["warning_categories"] = sorted({type(w.message).__name__ for w in caught})
        row["origins"].append(result)
    row["seconds"] = time.perf_counter()-started
    write(path, row)
    return row


def summary(rows):
    result = {}
    admitted = [r for r in rows if not r.get("excluded")]
    for name in NAMES:
        values = []
        for row in admitted:
            origins = [next(m["metrics"] for m in o["methods"] if m["name"] == name) for o in row["origins"]]
            values.append({k: float(np.mean([o[k] for o in origins])) for k in ("mase", "mae", "coverage", "mean_width", "msis")})
        result[name] = {"series": len(values), **{k: float(np.mean([v[k] for v in values])) for k in values[0]}} if values else {"series": 0}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    source_hashes = {p: digest(ROOT/p) for p in SOURCE_FILES}
    input_hashes = {k: digest(args.source_root/v["file"]) for k, v in DATASETS.items()}
    versions = {k: importlib.metadata.version(k) for k in ("numpy", "scipy", "statsforecast", "numba")}
    binding = {"protocol": PROTOCOL, "datasets": DATASETS, "code_sha256": source_hashes, "input_sha256": input_hashes, "packages": versions}
    identity = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    cache = args.cache / identity
    os.environ["NUMBA_CACHE_DIR"] = str(args.cache / "numba-cache")
    jobs, duplicate_rows, seen = [], [], {}
    for dataset, config in DATASETS.items():
        inventory = list(series_from_tsf(args.source_root/config["file"]))
        assert len(inventory) == config["count"], (dataset, len(inventory))
        for name, timestamp, y in inventory:
            sequence = hashlib.sha256(np.asarray(y, dtype='<f8').tobytes()).hexdigest()
            if sequence in seen:
                duplicate_rows.append({"id": name, "dataset": dataset, "source_n": len(y), "sequence_sha256": sequence,
                                       "excluded": "exact duplicate", "representative": seen[sequence], "origins": []})
            else:
                seen[sequence] = dataset + "/" + name
                jobs.append((dataset, name, timestamp, y, str(cache)))
    rows = list(duplicate_rows)
    print(json.dumps({"identity": identity, "inventory": sum(c['count'] for c in DATASETS.values()),
                      "unique_jobs": len(jobs), "duplicates": len(duplicate_rows)}), flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(evaluate, job): job[:2] for job in jobs}
        for n, future in enumerate(as_completed(futures), 1):
            row = future.result()  # a method failure fails the run; no silent comparator removal
            rows.append(row)
            if n % 20 == 0 or n == len(jobs):
                print(f"{n}/{len(jobs)} series completed; latest {row['dataset']}/{row['id']}", flush=True)
    rows.sort(key=lambda r: (r['dataset'], r['id']))
    output = {"schema": "chronoscope.validated-combinations/v1", "identity": identity, **binding,
              "summaries": {k: summary([r for r in rows if r['dataset'] == k]) for k in DATASETS}, "series": rows}
    write(args.output, output)
    print(json.dumps({"ok": True, "exit": "COMBINATION_STUDY_COMPLETE", "output": str(args.output),
                      "series": len(rows), "summaries": output['summaries']}), flush=True)


if __name__ == "__main__":
    main()
