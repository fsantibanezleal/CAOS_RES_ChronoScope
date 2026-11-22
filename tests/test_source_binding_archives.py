"""A migration must preserve immutable experiments without blessing new source maps."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_bindings import RECEIPT, implementation_sources  # noqa: E402


@pytest.mark.parametrize("artifact", ["reevaluation", "forecastability", "validated-combinations"])
def test_historical_experiment_retains_its_original_source_bytes(artifact):
    bindings = json.loads((ROOT / f"data/derived/{artifact}.json").read_text())["code_sha256"]
    sources = implementation_sources(bindings, ROOT)
    assert {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()} == bindings
    assert any("chronoscopelab" in name for name in sources)


def archived_copy(tmp_path):
    receipt = json.loads((ROOT / RECEIPT).read_text())
    for name in (RECEIPT, receipt["archive"]):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return receipt


def test_adding_a_new_binding_cannot_inherit_a_historical_archive(tmp_path):
    archived_copy(tmp_path)
    bindings = json.loads((ROOT / "data/derived/reevaluation.json").read_text())["code_sha256"]
    bindings["new.py"] = "0" * 64
    with pytest.raises(ValueError, match="absent"):
        implementation_sources(bindings, tmp_path)


def test_changed_archive_bytes_are_refused(tmp_path):
    receipt = archived_copy(tmp_path)
    archive = tmp_path / receipt["archive"]
    archive.write_bytes(archive.read_bytes() + b"tampered")
    bindings = json.loads((ROOT / "data/derived/reevaluation.json").read_text())["code_sha256"]
    with pytest.raises(ValueError, match="archive differs"):
        implementation_sources(bindings, tmp_path)


def test_new_implementation_binding_checks_current_bytes_and_rejects_escape(tmp_path):
    (tmp_path / "method.py").write_bytes(b"current implementation")
    bindings = {"method.py": hashlib.sha256(b"current implementation").hexdigest()}
    assert implementation_sources(bindings, tmp_path)["method.py"] == b"current implementation"
    (tmp_path / "method.py").write_bytes(b"different implementation")
    with pytest.raises(ValueError, match="differs"):
        implementation_sources(bindings, tmp_path)
    with pytest.raises(ValueError, match="Unsafe"):
        implementation_sources({"../escape.py": "0" * 64}, tmp_path)
