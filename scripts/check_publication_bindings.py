"""Verify all three current publication PDFs and canonical sources without network access."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(folder, candidate):
    receipt = json.loads((folder / "publication.json").read_text(encoding="utf-8"))
    pdf = (folder / "main.pdf").read_bytes()
    source = (folder / "tex/main.tex").read_bytes()
    assert receipt["state"] == candidate["state"] == "published"
    assert pdf.startswith(b"%PDF-") and len(pdf) == receipt["bytes"]
    assert hashlib.md5(pdf).hexdigest() == receipt["md5"]
    assert hashlib.sha256(pdf).hexdigest() == receipt["sha256"] == candidate["sha256"] == candidate["reviewed_pdf_sha256"]
    assert b"\r\n" not in source, "Published source must retain the repository's canonical LF bytes"
    assert hashlib.sha256(source).hexdigest() == receipt["source_sha256"] == candidate["source_sha256"] == candidate["reviewed_source_sha256"]
    assert receipt["doi"].encode() in source and receipt["doi"] == candidate["version_doi"]
    assert receipt["version"] == candidate["version"]
    metadata = json.loads((folder / "zenodo.json").read_text(encoding="utf-8"))["metadata"]
    assert metadata["version"].removeprefix("v") == receipt["version"]
    if "publication_source_sha256" in receipt:
        archive = folder / "history" / Path(receipt["publication_source_archive"]).name
        original = gzip.decompress(archive.read_bytes())
        assert hashlib.sha256(original).hexdigest() == receipt["publication_source_sha256"]
        assert original.replace(b"\r\n", b"\n") == source, "Source normalization changed content"
    return receipt["doi"]


def main():
    manifest = json.loads((ROOT / "manuscripts/publication-candidates.json").read_text(encoding="utf-8"))
    assert len(manifest["candidates"]) == 3
    for candidate in manifest["candidates"]:
        folder = ROOT / Path(candidate["pdf"]).parent
        print(f"Publication binding: {verify(folder, candidate)}")


if __name__ == "__main__":
    main()
