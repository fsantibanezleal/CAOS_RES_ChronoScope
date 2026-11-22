"""Fetch and verify the three public checkpoints of the retained teaching protocol.

Run with the declared Linux reference interpreter, naming an external cache and
receipt. TiRex-2 uses its separately authorized gated checkpoint/runtime cache.
No latest revision is substituted and no prediction is computed by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(cache: Path, output: Path):
    from huggingface_hub import snapshot_download

    cache, output = cache.resolve(), output.resolve()
    if cache.is_relative_to(ROOT) or output.is_relative_to(ROOT):
        raise ValueError("Checkpoint cache and download receipt must be external")
    protocol = json.loads((ROOT / "data/derived/fresh-reevaluation.json").read_text(encoding="utf-8"))["runtime"]
    result = {}
    for repository, expected in protocol["checkpoint_sha256"].items():
        revision = protocol["checkpoint_revisions"][repository]
        path = Path(snapshot_download(repository, revision=revision, cache_dir=cache,
                                      allow_patterns=["*.json", "*.safetensors", "LICENSE*", "README.md"]))
        hashes = {}
        for filename, digest in expected.items():
            actual = hashlib.sha256((path / filename).read_bytes()).hexdigest()
            if actual != digest:
                raise ValueError(f"Pinned checkpoint bytes differ: {repository}/{filename}")
            hashes[filename] = actual
        result[repository] = {"revision": revision, "sha256": hashes}
        print(f"Verified {repository} at {revision}", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.cache, args.receipt)


if __name__ == "__main__":
    main()
