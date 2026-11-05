"""Verify the reviewable working PDFs against their compiled local input receipts."""
from __future__ import annotations

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
    for slug in SLUGS:
        verify(ROOT / "manuscripts" / slug / "next")
        print(f"Working draft binding: {slug}; independent review and publication remain separate")


if __name__ == "__main__":
    main()
