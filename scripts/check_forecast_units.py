"""Recheck shipped point and interval paths without fitting or changing evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("forecast_unit_boundary", ROOT / "data-pipeline/chronoscopelab/io/units.py")
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


def sweep(root: Path = ROOT) -> dict:
    counts = {"cases": 0, "methods": 0, "redacted_uncheckable": 0}
    problems, hashes = [], {}
    index_path = root / "data/derived/manifests/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paths = [root / "data/derived" / e["case_id"] / "trace.json" for e in index["cases"]]
    paths += [root / "data/derived" / n for n in ("reevaluation.json", "fresh-reevaluation.json")]
    for path in paths:
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        document = json.loads(path.read_text(encoding="utf-8"))
        for case in document.get("cases", [document]):
            if case.get("redacted"):
                counts["redacted_uncheckable"] += 1
                continue
            findings = boundary.check_forecast_units(case["history"] + case["actual"], case["methods"])
            counts["cases"] += 1
            counts["methods"] += len(case["methods"])
            problems.extend({**p, "case": case["case_id"], "artifact": path.relative_to(root).as_posix()}
                            for p in findings)
    return {"scope": "15 canonical traces and both 15-case reevaluations; does not cover external combinations or browser paths",
            "counts": counts, "input_sha256": hashes, "blocking": [p for p in problems if p["blocking"]],
            "advisories": [p for p in problems if not p["blocking"]]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="write a detailed receipt outside frozen evidence")
    args = parser.parse_args()
    receipt = sweep()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Forecast units: {receipt['counts']}, {len(receipt['blocking'])} blocking, "
          f"{len(receipt['advisories'])} advisory")
    for problem in receipt["blocking"]:
        print(problem)
    return int(bool(receipt["blocking"] or receipt["counts"]["redacted_uncheckable"]))


if __name__ == "__main__":
    raise SystemExit(main())
