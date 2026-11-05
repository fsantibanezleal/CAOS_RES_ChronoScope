"""ChronoScope producer admission: immutable released inputs, recomputed common holdouts.

The stage contains the complete source-bound corpus. Historical engine versions remain
historical facts; a product release never relabels frozen paths as newly fitted models.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = (
    "data-pipeline/chronoscopelab/reevaluation.py",
    "data-pipeline/chronoscopelab/model/forecasters.py",
    "data-pipeline/chronoscopelab/model/context_memory.py",
    "data-pipeline/chronoscopelab/cases/forecast_cases.py",
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combination_path(root, name):
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"Missing or redirected combination input: {name}")
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or redirected combination input: {name}")
    for component in (path, *path.parents):
        if component == root:
            break
        if component.is_symlink() or getattr(component, "is_junction", lambda: False)():
            raise ValueError(f"Missing or redirected combination input: {name}")
    return path


def validate_combination_release(stage, source=ROOT):
    """Carry the complete independently scored study; never silently regenerate it."""
    name = "data/derived/validated-combinations.json"
    canonical = combination_path(source, name)
    candidate = combination_path(stage, name)
    if digest(candidate) != digest(canonical):
        raise ValueError("Frozen combination index changed")
    index = read(canonical)
    names = {"data/derived/" + entry["path"] for entry in index["cases"]}
    if len(names) != len(index["cases"]):
        raise ValueError("Combination inventory contains duplicate paths")
    actual = {p.relative_to(stage).as_posix()
              for p in (stage / "data/derived/combinations").rglob("*.json")}
    if actual != names:
        raise ValueError("Combination payload differs from the complete indexed inventory")
    for name in sorted(names):
        if digest(combination_path(stage, name)) != digest(combination_path(source, name)):
            raise ValueError(f"Frozen combination case changed: {name}")
    for name, expected in index["code_sha256"].items():
        if digest(combination_path(source, name)) != expected:
            raise ValueError(f"Combination implementation binding changed: {name}")
    if digest(combination_path(source, "scripts/export_combination_study.py")) != index["export_code_sha256"]:
        raise ValueError("Combination export implementation binding changed")
    selected = combination_path(stage, "data/derived/reevaluation.json")
    if digest(selected) != index["selected_case_source_sha256"]:
        raise ValueError("Combination development-case source binding changed")
    audit = combination_path(stage, index["audit"]["path"])
    if digest(audit) != index["audit"]["sha256"]:
        raise ValueError("Combination full audit archive binding changed")
    return len(names)


def validate(stage):
    cfg = read(ROOT / "scripts/local/workflow.json")
    for name in cfg["stage_inputs"]:
        target = (stage / name).resolve()
        if not target.is_relative_to(stage) or not target.is_file():
            raise ValueError(f"Missing or escaped input: {name}")
        if digest(target) != digest(ROOT / name):
            raise ValueError(f"Frozen source changed: {name}")
    index = read(stage / "data/derived/manifests/index.json")
    document = read(stage / "data/derived/reevaluation.json")
    expected = [r["case_id"] for r in index["cases"]]
    actual = [r["case_id"] for r in document["cases"]]
    if len(expected) != 15 or sorted(actual) != sorted(expected) or len(set(actual)) != len(actual):
        raise ValueError("Common comparison is not the complete unique case inventory")
    expected_hashes = {f"data/derived/{cid}/trace.json": digest(stage / f"data/derived/{cid}/trace.json")
                       for cid in expected}
    if document["trace_sha256"] != expected_hashes:
        raise ValueError("Comparison has stale trace bindings")
    if document["code_sha256"] != {p: digest(ROOT / p) for p in SOURCE_FILES}:
        raise ValueError("Comparison has stale implementation bindings")
    expected_inputs = {p.relative_to(stage).as_posix(): digest(p) for p in sorted((stage / "data/examples").glob("*.csv"))}
    if document["input_sha256"] != expected_inputs:
        raise ValueError("Comparison has stale source input bindings")
    for row, case in zip(index["cases"], document["cases"], strict=True):
        if row["case_id"] != case["case_id"]:
            raise ValueError("Comparison order differs from the source inventory")
        manifest = read(stage / "data/derived" / row["manifest_path"])
        artifact = stage / "data/derived" / manifest["artifact"]["path"]
        if artifact.stat().st_size != manifest["artifact"]["bytes"]:
            raise ValueError("Released artifact byte count differs from its manifest")
        trace = read(stage / f"data/derived/{case['case_id']}/trace.json")
        if case["actual"] != trace["actual"] or len(case["methods"]) != 22:
            raise ValueError("Common holdout differs from its source or methods are incomplete")
        if len(case["history"]) != trace["history_len"] or case["history_length"] != trace["history_len"]:
            raise ValueError("Fitting history is not the contiguous original prefix")
        for i, position in enumerate(trace["history_index"]):
            if abs(case["history"][position] - trace["history"][i]) > 0.000051:
                raise ValueError("Reconstructed history differs from released observations")
        for method in case["methods"]:
            vectors = [method[k] for k in ("lower", "point", "upper")]
            if any(len(a) != case["horizon"] for a in vectors):
                raise ValueError("Incomplete prediction horizon")
            for lo, point, hi in zip(*vectors, strict=True):
                if not all(math.isfinite(x) for x in (lo, point, hi)) or not lo <= point <= hi:
                    raise ValueError("Invalid prediction quantiles")
    sys.path.insert(0, str(ROOT / "scripts"))
    from check_fresh_reevaluation import validate as validate_fresh

    validate_fresh(read(stage / "data/derived/fresh-reevaluation.json"), root=ROOT, artifact_root=stage)
    from check_research_extensions import validate_study, validate_diagnostics

    validate_diagnostics(root=stage)
    validate_study(read(stage / "data/derived/forecastability.json"), root=ROOT)
    count = validate_combination_release(stage)
    print(f"Product admission: diagnostics, fresh comparison, M4 corpus and {count} combination cases")


def main():
    mode, name = sys.argv[1:]
    stage = Path(name).resolve()
    if mode == "generate":
        if stage.is_relative_to(ROOT):
            raise ValueError("Generation requires an external stage")
        sys.path.insert(0, str(ROOT / "data-pipeline"))
        from chronoscopelab.reevaluation import build

        for rel in SOURCE_FILES:
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / rel).read_bytes())
        document = build(stage)
        (stage / "data/derived/reevaluation.json").write_text(
            json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    elif mode != "validate":
        raise ValueError("Expected generate or validate")
    validate(stage)


if __name__ == "__main__":
    main()
