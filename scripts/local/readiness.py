"""Describe the availability of each ChronoScope contract in an admitted tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from check_contracts import parse_catalog, parse_document_glob, split_documents  # noqa: E402

OUTPUT = "data/derived/readiness.json"


def document(root: Path) -> dict:
    catalog = (root / "docs/contracts/catalog.md").read_text(encoding="utf-8")
    _, rows = parse_catalog(catalog)
    contracts = []
    for row in rows:
        missing = []
        for entry in split_documents(row["documents"]):
            negative, pattern, _ = parse_document_glob(entry)
            if not negative and not any(p.is_file() for p in root.glob(pattern)):
                missing.append(pattern)
        contracts.append({
            "id": row["id"],
            "version": row["version"],
            "status": row["status"],
            "state": "missing" if missing else "available",
            "missing": missing,
        })
    return {
        "schema": "chronoscope.readiness/v1",
        "product_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "catalog_sha256": hashlib.sha256(catalog.encode()).hexdigest(),
        "contracts": contracts,
    }


def write(root: Path) -> None:
    value = json.dumps(document(root), indent=2) + "\n"
    (root / OUTPUT).write_text(value, encoding="utf-8", newline="\n")


def validate(root: Path) -> None:
    expected = document(root)
    if any(row["state"] != "available" for row in expected["contracts"]):
        raise ValueError("The research corpus is missing contract documents")
    if json.loads((root / OUTPUT).read_text(encoding="utf-8")) != expected:
        raise ValueError("Readiness is stale; regenerate it from the current catalog and corpus")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write(args.root)
    validate(args.root)
    print("Readiness matches the current catalog and available documents")


if __name__ == "__main__":
    main()
