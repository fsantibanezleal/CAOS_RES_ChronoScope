"""Stage a compact browser index, per-series paths and complete compressed audit."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))
from chronoscopelab.model.context_memory import fit_context_memory  # noqa: E402
from chronoscopelab.model.forecasters import METHODS, gaussian_quantiles  # noqa: E402
from chronoscopelab.model.validated_combination import fit_validated  # noqa: E402
from chronoscopelab.reevaluation import metrics  # noqa: E402
from accelerate_expert_loops import enable  # noqa: E402
from check_combination_study import validate  # noqa: E402


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )


def selected_cases():
    comparison = json.loads((ROOT / "data/derived/reevaluation.json").read_text(encoding="utf-8"))
    rows = []
    for case in comparison["cases"]:
        y, actual = np.array(case["history"]), np.array(case["actual"])
        m, h = case["seasonality"], case["horizon"]
        forecasts = []
        for name, _, fn in METHODS:
            q = gaussian_quantiles(*fn(y, m, h), (0.1, 0.5, 0.9))
            forecasts.append(
                {
                    "name": name,
                    "quantiles": q.tolist(),
                    "metrics": metrics(y, actual, q[:, 1], q[:, 0], q[:, 2], m),
                }
            )
        for name, mode in [
            ("ContextMemory", "context"),
            ("RecencyMean", "recency"),
            ("EqualMean", "uniform"),
            ("ContextMemoryCV", None),
            ("ValidationMix", None),
        ]:
            fit = (
                fit_context_memory(y, m, h, mode=mode)
                if mode
                else fit_validated(y, m, h, stacking=name == "ValidationMix")
            )
            q = fit.quantiles
            model = {
                "name": name,
                "quantiles": q.tolist(),
                "metrics": metrics(y, actual, q[:, 1], q[:, 0], q[:, 2], m),
                "weights": fit.weights.tolist(),
                "memory_origins": list(fit.origins),
            }
            if mode is None:
                model.update(
                    selected=fit.selected, validation=fit.candidates, validation_splits=fit.validation_splits
                )
            forecasts.append(model)
        rows.append(
            {
                "id": case["case_id"],
                "dataset": "selected_cases",
                "source_n": len(y) + h,
                "sequence_sha256": sha(np.r_[y, actual].astype("<f8").tobytes()),
                "origins": [
                    {
                        "origin": len(y),
                        "prefix_start": 0,
                        "prefix_length": len(y),
                        "prefix_sha256": sha(y.astype("<f8").tobytes()),
                        "scale": float(np.mean(abs(y[m:] - y[:-m]))),
                        "actual": actual.tolist(),
                        "methods": forecasts,
                    }
                ],
                "seasonality": m,
                "horizon": h,
            }
        )
    return rows


def cohort(rows):
    admitted = [r for r in rows if not r.get("excluded")]
    names = [m["name"] for m in admitted[0]["origins"][0]["methods"]]
    summary = []
    for name in names:
        values = []
        for row in admitted:
            scores = [next(m["metrics"] for m in o["methods"] if m["name"] == name) for o in row["origins"]]
            values.append(
                {
                    k: float(np.mean([s[k] for s in scores]))
                    for k in ["mase", "mae", "coverage", "mean_width", "msis"]
                }
            )
        summary.append(
            {
                "name": name,
                "series": len(values),
                **{k: float(np.mean([v[k] for v in values])) for k in values[0]},
            }
        )
    selected = Counter()
    for row in admitted:
        for origin in row["origins"]:
            for model in origin["methods"]:
                if "selected" in model:
                    selected[model["name"] + ":" + str(tuple(model["selected"]))] += 1
    return {
        "inventory": len(rows),
        "admitted": len(admitted),
        "excluded": len(rows) - len(admitted),
        "exclusion_reasons": dict(Counter(r["excluded"] for r in rows if r.get("excluded"))),
        "origins": sum(len(r["origins"]) for r in admitted),
        "summary": summary,
        "selection_counts": dict(selected),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, required=True)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    args = p.parse_args()
    raw = args.results.read_bytes()
    document = json.loads(raw)
    receipt = validate(document, args.source_root)
    os.environ.setdefault("NUMBA_CACHE_DIR", str(args.output_root / "numba-cache"))
    enable()
    rows = document["series"] + selected_cases()
    names = {
        "m4_weekly": "M4 Weekly",
        "m3_monthly": "M3 Monthly",
        "selected_cases": "Selected development cases",
    }
    index = {
        "schema": "chronoscope.combination-index/v1",
        "complete": True,
        "identity": document["identity"],
        "protocol": document["protocol"],
        "code_sha256": document["code_sha256"],
        "export_code_sha256": sha(Path(__file__).read_bytes()),
        "packages": document["packages"],
        "selected_case_source_sha256": sha((ROOT / "data/derived/reevaluation.json").read_bytes()),
        "cohorts": [
            {"id": k, "name": name, **cohort([r for r in rows if r["dataset"] == k])}
            for k, name in names.items()
        ],
        "cases": [],
        "sources": {},
        "browser_forecast_decimals": 8,
    }
    for dataset, config in document["datasets"].items():
        source = args.source_root / config["file"]
        archive = source.with_suffix(".zip")
        index["sources"][dataset] = {
            "doi": f"10.5281/zenodo.{config['record']}",
            "license": "CC-BY-4.0",
            "tsf_sha256": sha(source.read_bytes()),
            "zip_sha256": sha(archive.read_bytes()),
            "horizon": config["horizon"],
            "seasonality": config["seasonality"],
        }
    for row in rows:
        path = f"combinations/{row['dataset']}/{row['id']}.json"
        entry = {k: row[k] for k in ["id", "dataset", "source_n"]}
        entry.update(path=path, origins=len(row["origins"]))
        if row.get("excluded"):
            entry["excluded"] = row["excluded"]
        index["cases"].append(entry)
        compact = {k: v for k, v in row.items() if k not in ["seconds", "start_timestamp"]}
        compact["schema"] = "chronoscope.combination-case/v1"
        compact["origins"] = []
        for original in row["origins"]:
            origin = {k: v for k, v in original.items() if k not in ["methods", "warning_categories"]}
            origin["methods"] = []
            for original_model in original["methods"]:
                model = {
                    k: v for k, v in original_model.items() if k not in ["validation", "validation_splits"]
                }
                model["quantiles"] = np.round(model["quantiles"], 8).tolist()
                if "validation" in original_model:
                    model["validation_blocks"] = original_model["validation"][0]["validation_blocks"]
                origin["methods"].append(model)
            compact["origins"].append(origin)
        write(args.output_root / "data/derived" / path, compact)
    evidence = Path("manuscripts/context-memory/evidence/external-evaluation.json.gz")
    payload = gzip.compress(raw, compresslevel=9, mtime=0)
    (args.output_root / evidence).parent.mkdir(parents=True, exist_ok=True)
    (args.output_root / evidence).write_bytes(payload)
    index["audit"] = {
        "path": evidence.as_posix(),
        "sha256": sha(payload),
        "uncompressed_sha256": sha(raw),
        "scope": "Complete external per-origin forecasts, candidate validation scores, temporal splits and weights.",
    }
    write(args.output_root / "data/derived/validated-combinations.json", index)
    write(args.output_root / "admission.json", receipt)
    print(
        json.dumps(
            {
                "ok": True,
                "cases": len(rows),
                "compressed_audit_bytes": len(payload),
                "cohorts": index["cohorts"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
