"""Admit a complete fresh comparison: exact sources, original targets and independently recomputed scores."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"amazon/chronos-bolt-small", "amazon/chronos-2", "google/timesfm-2.5-200m-pytorch", "NX-AI/TiRex-2"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def implementation_dependencies(root, sources=None):
    """Conservatively follow local imports, including imports inside engine functions.

    The frozen experiment also recorded unrelated modules. Those bindings remain
    immutable, but adding an independent experiment must not invalidate this one.
    A newly imported dependency must be present in the recorded inventory.
    """
    package = root / "data-pipeline"
    modules = {}
    paths = ((package / "chronoscopelab").rglob("*.py") if sources is None else
             (root / rel for rel in sources if rel.startswith("data-pipeline/chronoscopelab/")))
    for path in paths:
        parts = list(path.relative_to(package).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        modules[".".join(parts)] = path
    entry = root / "scripts/reevaluate_fresh.py"
    pending = [("", entry)]
    visited = set()
    while pending:
        module, path = pending.pop()
        rel = path.relative_to(root).as_posix()
        if rel in visited:
            continue
        visited.add(rel)
        # Importing a module executes all enclosing package initializers.
        parts = module.split(".")
        for length in range(1, len(parts)):
            parent = ".".join(parts[:length])
            if parent in modules:
                pending.append((parent, modules[parent]))
        namespace = module if path.name == "__init__.py" else module.rpartition(".")[0]
        source = path.read_text(encoding="utf-8") if sources is None else sources[rel]
        for node in ast.walk(ast.parse(source, filename=str(path))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    prefix = namespace.split(".")[:len(namespace.split(".")) - node.level + 1]
                    base = ".".join([*prefix, *([node.module] if node.module else [])])
                else:
                    base = node.module or ""
                names = [base, *(f"{base}.{alias.name}" for alias in node.names)]
            for name in names:
                if name in modules:
                    pending.append((name, modules[name]))
    return visited


def frozen_implementation(document, root, artifact_root):
    """Resolve only the exact archived experiment's original, source-bound bytes.

    The recovery receipt does not assert a historical execution commit. New
    binding inventories continue to require the current implementation below.
    No archive entry is extracted or imported.
    """
    receipt_path = root / "docs/research/fresh-source-archive.json"
    if not receipt_path.is_file():
        return None
    receipt = read(receipt_path)
    fingerprint = hashlib.sha256(json.dumps(document["code_sha256"], sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()
    if fingerprint != receipt["code_binding_sha256"]:
        return None
    for field in ("archive", "artifact"):
        base = root if field == "archive" else artifact_root
        path = (base / receipt[field]).resolve()
        if not path.is_relative_to(base.resolve()) or digest(path) != receipt[field + "_sha256"]:
            raise ValueError(f"Frozen source {field} differs from its recovery receipt")
    with zipfile.ZipFile(root / receipt["archive"]) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(document["code_sha256"]) or len(names) != receipt["files"]:
            raise ValueError("Frozen source archive inventory differs")
        sources = {}
        for rel, expected in document["code_sha256"].items():
            if Path(rel).is_absolute() or ".." in Path(rel).parts:
                raise ValueError("Unsafe frozen source path")
            raw = archive.read(rel)
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError(f"Frozen implementation binding differs: {rel}")
            sources[rel] = raw.decode("utf-8")
    return sources


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
    sources = frozen_implementation(document, root, artifact_root)
    missing = implementation_dependencies(root, sources) - set(document["code_sha256"])
    if missing:
        raise ValueError(f"Fresh implementation binding inventory is incomplete: {sorted(missing)}")
    for key in ("trace_sha256", "input_sha256"):
        if document[key] != baseline[key]:
            raise ValueError("Fresh source inventory differs from the admitted comparison")
    inventories = [({**document["trace_sha256"], **document["input_sha256"]}, artifact_root)]
    if sources is None:
        inventories.insert(0, (document["code_sha256"], root))
    for bindings, base in inventories:
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
    print(f"Historical fresh-fit experiment: {counts[0]} cases, {counts[1]} variants; "
          "original sources bound and all metrics independently match")
