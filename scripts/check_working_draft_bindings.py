"""Verify the reviewable working PDFs against their compiled local input receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("context-memory", "product-report", "prequential-streaming-conformal")


def verify(folder: Path, root: Path = ROOT) -> None:
    receipt = json.loads((folder / "build-receipt.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "working-revision" and receipt["published"] is False
    pdf = (folder / "main.pdf").read_bytes()
    assert pdf.startswith(b"%PDF-") and len(pdf) == receipt["pdf_bytes"]
    assert hashlib.sha256(pdf).hexdigest() == receipt["pdf_sha256"], "Working PDF changed"
    sources = receipt["source_files"]
    assert (folder / "tex/main.tex").relative_to(root).as_posix() in sources
    for name, expected in sources.items():
        path = (root / name).resolve()
        assert path.is_relative_to(root.resolve()), "Input escapes the source repository"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"Working PDF input changed: {name}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", action="store_true", help="check the working titles, depth and coverage as well")
    args = parser.parse_args()
    findings = []
    if args.content:
        from check_manuscript_depth import check_doc, clean_title, contract_ids, load, measures, sdd_ids

        methods, claims = sdd_ids(ROOT, findings)
        contracts = contract_ids(ROOT)
    for slug in SLUGS:
        folder = ROOT / "manuscripts" / slug / "next"
        verify(folder)
        if args.content:
            document = load(folder)
            if document is None:
                raise ValueError(f"Missing native LaTeX draft: {slug}")
            coverage = json.loads((folder / "coverage.json").read_text(encoding="utf-8"))
            status = json.loads((folder / "revision-status.json").read_text(encoding="utf-8"))
            title = clean_title(status["title"])
            findings.extend(f"{slug}: {finding}" for finding in check_doc(
                ROOT, document, coverage, methods, claims, contracts, {title: coverage["kind"]}
            ))
            if measures(document) != status["measured_content"]:
                findings.append(f"{slug}: stale working-draft content measurements")
        print(f"Working draft binding: {slug}; independent review and publication remain separate")
    if findings:
        raise SystemExit("\n".join(findings))
    if args.content:
        print("Working manuscripts meet the measured depth and coverage checks")


if __name__ == "__main__":
    main()
