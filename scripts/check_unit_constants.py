"""Fail closed on unreviewed numeric literals and numerical-source changes.

CONTRACT3b complements the loose runtime observable gate. This inventories Python
AST constants and TypeScript compiler NumericLiteral nodes, including integers.
--update writes pending annotations; it cannot approve a number automatically.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "scripts/unit_constants.json"
BROWSER_SCRIPTS = (
    "scripts/train_nlinear_onnx.py", "scripts/evaluate_browser_linear.py",
    "scripts/confirm_browser_calibration.py", "scripts/check_browser_linear_evidence.py",
    "scripts/plot_browser_calibration.py",
)
SCHEMA = "chronoscope.numeric-units/v1"
TYPESCRIPT_SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def python_literals(source: str, filename: str) -> list[dict]:
    """Read every int/float occurrence, retaining its signed expression and context."""
    tree = ast.parse(source, filename=filename)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    entries = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or type(node.value) not in (int, float, complex):
            continue
        signed = node
        parent = parents.get(node)
        if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, (ast.USub, ast.UAdd)):
            signed = parent
        current, names = node, []
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.insert(0, current.name)
        statement = signed
        while statement in parents and not isinstance(statement, (ast.stmt, ast.arg)):
            statement = parents[statement]
        expression = ast.get_source_segment(source, statement) or ast.dump(statement)
        entries.append({"line": signed.lineno, "column": signed.col_offset,
                        "literal": ast.get_source_segment(source, signed),
                        "scope": ".".join(names) or "<module>",
                        "context": " ".join(expression.split()),
                        "parent": type(parents.get(signed)).__name__})
    return sorted(entries, key=lambda row: (row["line"], row["column"]))


def typescript_literals(files: list[Path], parser_root: Path = ROOT) -> tuple[str, dict]:
    if not files:
        return "not-used", {}
    request = {"parserRoot": str(parser_root), "files": [str(path) for path in files]}
    completed = subprocess.run(["node", str(ROOT / "scripts/unit_constants_ts.mjs")],
                               input=json.dumps(request), capture_output=True, text=True, encoding="utf-8")
    if completed.returncode:
        raise ValueError("TypeScript AST inventory failed: " + completed.stderr.strip())
    response = json.loads(completed.stdout)
    if not isinstance(response.get("compiler"), str) or len(response.get("files", [])) != len(files):
        raise ValueError("TypeScript compiler returned an incomplete inventory")
    return response["compiler"], {Path(row["path"]): row["entries"] for row in response["files"]}


def source_paths(root: Path, provider: Path | None) -> dict[str, Path]:
    paths = {path.relative_to(root).as_posix(): path for path in (root / "data-pipeline/engine").rglob("*.py")}
    paths.update({path.relative_to(root).as_posix(): path for path in (root / "frontend/src/lib").rglob("*")
                  if path.suffix in TYPESCRIPT_SUFFIXES and not path.name.endswith(tuple(".test" + suffix for suffix in TYPESCRIPT_SUFFIXES))})
    for name in BROWSER_SCRIPTS:
        if (root / name).is_file():
            paths[name] = root / name
    if provider is not None:
        paths.update({"forecastscope/" + path.relative_to(provider).as_posix(): path
                      for path in provider.rglob("*.py")})
    if not paths:
        raise ValueError("No active method sources found; an empty inventory is not acceptance")
    return dict(sorted(paths.items()))


def inventory(root: Path, provider: Path | None = None, provider_version: str | None = None) -> dict:
    paths = source_paths(root, provider)
    compiler, ts_entries = typescript_literals([path for path in paths.values() if path.suffix in TYPESCRIPT_SUFFIXES])
    files = {}
    for name, path in paths.items():
        data = path.read_bytes()
        text = data.decode("utf-8-sig")
        rows = python_literals(text, name) if path.suffix == ".py" else ts_entries[path]
        for row in rows:
            row["context_sha256"] = sha(row["context"].encode())
        files[name] = {"sha256": sha(data.replace(b"\r\n", b"\n")), "literals": rows}
    return {"schema": SCHEMA, "source_hash_policy": "UTF-8 source with CRLF canonicalized to LF",
            "provider": {"name": "forecastscope", "version": provider_version},
            "typescript": compiler, "files": files}


def findings(current: dict, baseline: dict) -> list[str]:
    problems = []
    if baseline.get("schema") != SCHEMA:
        return ["Unsupported or missing numeric-units baseline schema"]
    identity = baseline.get("identity_review", {})
    if identity.get("status") != "reviewed" or not isinstance(identity.get("justification"), str) or len(identity["justification"].strip()) < 35:
        problems.append("Provider/compiler identity awaits review")
    for field in ("provider", "typescript", "source_hash_policy"):
        if current[field] != baseline.get(field):
            problems.append(f"Reviewed {field} identity changed")
    actual, approved = current["files"], baseline.get("files", {})
    for name in sorted(actual.keys() - approved.keys()):
        problems.append(f"Unreviewed source: {name}")
    for name in sorted(approved.keys() - actual.keys()):
        problems.append(f"Reviewed source disappeared: {name}")
    for name in sorted(actual.keys() & approved.keys()):
        observed, recorded = actual[name], approved[name]
        if recorded.get("review_status") != "reviewed" or not isinstance(recorded.get("review_justification"), str) or len(recorded["review_justification"].strip()) < 35:
            problems.append(f"Source awaits scope/dimensional review: {name}")
        if observed["sha256"] != recorded.get("sha256"):
            problems.append(f"Numerical source changed since review: {name}")
        rows = recorded.get("literals", [])
        identities = [(r.get("line"), r.get("column")) for r in rows]
        if len(identities) != len(set(identities)):
            problems.append(f"Duplicate reviewed occurrence: {name}")
        if len(rows) != len(observed["literals"]):
            problems.append(f"Numeric occurrence inventory changed: {name}")
        for index, row in enumerate(observed["literals"]):
            where = f"{name}:{row['line']}:{row['column']}"
            if index >= len(rows):
                problems.append(f"Unreviewed literal {row['literal']}: {where}")
                continue
            annotation = rows[index]
            if any(annotation.get(key) != value for key, value in row.items()):
                problems.append(f"Literal or expression differs from reviewed baseline: {where}")
            if annotation.get("status") != "reviewed":
                problems.append(f"Literal awaits dimensional review: {where}")
            for field in ("quantity", "unit", "justification"):
                value = annotation.get(field)
                if not isinstance(value, str) or not value.strip() or value.lower().strip() in {
                    "unknown", "dimensionless", "constant", "numeric", "todo", "n/a", "1"}:
                    problems.append(f"Missing specific {field}: {where}")
            if len(str(annotation.get("justification", ""))) < 35:
                problems.append(f"Insufficient quantity rationale: {where}")
    return problems


def pending_baseline(current: dict, previous: dict) -> dict:
    """Scaffold a review; preserve annotations only for byte-identical source files."""
    result = json.loads(json.dumps(current))
    result["identity_review"] = previous.get("identity_review", {"status": "pending", "justification": None}) if (
        all(current.get(key) == previous.get(key) for key in ("provider", "typescript", "source_hash_policy"))) else {"status": "pending", "justification": None}
    for name, record in result["files"].items():
        old = previous.get("files", {}).get(name, {})
        if old.get("sha256") == record["sha256"]:
            record["literals"] = old.get("literals", [])
            record["review_status"] = old.get("review_status", "pending")
            record["review_justification"] = old.get("review_justification")
        else:
            record["review_status"] = "pending"
            record["review_justification"] = None
            for row in record["literals"]:
                row.update(status="pending", quantity=None, unit=None, justification=None)
    return result


def installed_provider() -> tuple[Path, str]:
    spec = importlib.util.find_spec("forecastscope")
    if spec is None or spec.origin is None:
        raise ValueError("Install the pinned ForecastScope method provider before auditing its actual source")
    return Path(spec.origin).parent, importlib.metadata.version("forecastscope")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--update", action="store_true", help="Write pending entries; never approve them")
    parser.add_argument("--report", action="store_true", help="Print every finding instead of the first twenty")
    args = parser.parse_args()
    try:
        provider, version = installed_provider()
        current = inventory(ROOT, provider, version)
        previous = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
        if args.update:
            current = pending_baseline(current, previous)
            args.baseline.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            previous = current
        problems = findings(current, previous)
    except (OSError, ValueError, SyntaxError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Numeric units gate FAILED: {error}")
        return 1
    if problems:
        print(f"Numeric units gate FAILED: {len(problems)} findings")
        for problem in problems if args.report else problems[:20]:
            print("  " + problem)
        return 1
    total = sum(len(record["literals"]) for record in current["files"].values())
    print(f"Numeric units gate PASS: {total} reviewed literals, {len(current['files'])} sources; ForecastScope {version}; TypeScript {current['typescript']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
