"""Resolve immutable historical source bytes without relabelling a new implementation.

Only complete code-binding maps registered before the provider migration may
use the archive. Other maps must match current files. Admission never executes
archived code; independent numerical parity uses a separately named reference.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

RECEIPT = Path("docs/research/provider-migration-source-archive.json")


def fingerprint(bindings):
    return hashlib.sha256(json.dumps(bindings, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verified_archive(root):
    """Read SHA-bound historical bytes; this function never executes them."""
    root = Path(root).resolve()
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    archive_path = (root / receipt["archive"]).resolve()
    if not archive_path.is_relative_to(root) or hashlib.sha256(archive_path.read_bytes()).hexdigest() != receipt["archive_sha256"]:
        raise ValueError("Historical source archive differs from its receipt")
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(receipt["files"]):
            raise ValueError("Historical source archive inventory differs")
        sources = {name: archive.read(name) for name in receipt["files"]}
    if any(hashlib.sha256(raw).hexdigest() != receipt["files"][name] for name, raw in sources.items()):
        raise ValueError("Historical source archive member changed")
    return receipt, sources


def implementation_sources(bindings, root):
    root = Path(root).resolve()
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else None
    archived = receipt is not None and fingerprint(bindings) in {
        value for row in receipt["experiments"].values()
        for key, value in row.items() if key.startswith("code_binding")
    }
    if archived:
        _, sources = verified_archive(root)
    else:
        sources = {}
    result = {}
    for name, expected in bindings.items():
        path = (root / name).resolve()
        if Path(name).is_absolute() or ".." in Path(name).parts or not path.is_relative_to(root):
            raise ValueError("Unsafe implementation source path")
        if not archived and not path.is_file():
            raise ValueError("Implementation source is absent: " + name)
        raw = sources[name] if archived else path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Implementation source differs: " + name)
        result[name] = raw
    return result
