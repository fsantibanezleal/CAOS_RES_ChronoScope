"""Alter one actual release input or binding and require the real product admission to refuse it."""
import importlib.util
import json
from pathlib import Path

import pytest


def adapter(repo):
    spec = importlib.util.spec_from_file_location("chronoscope_admission", repo / "scripts/local/producer_bridge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_corpus_is_admitted(repo):
    adapter(repo).validate(repo)


def test_mutated_frozen_input_is_refused(repo, tmp_path):
    import shutil

    stage = tmp_path / "candidate"
    shutil.copytree(repo / "data", stage / "data")
    shutil.copytree(repo / "models", stage / "models")
    trace = stage / "data/derived/TRND_seasonal/trace.json"
    trace.write_bytes(trace.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="Frozen source changed"):
        adapter(repo).validate(stage)


@pytest.mark.parametrize("binding", ["trace_sha256", "code_sha256"])
def test_stale_binding_is_refused(repo, binding):
    path = repo / "data/derived/reevaluation.json"
    doc = json.loads(path.read_text())
    name = next(iter(doc[binding]))
    doc[binding][name] = "0" * 64
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="stale"):
        adapter(repo).validate(repo)


def test_partial_comparison_is_refused(repo):
    path = repo / "data/derived/reevaluation.json"
    doc = json.loads(path.read_text())
    doc["cases"].pop()
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="complete unique case inventory"):
        adapter(repo).validate(repo)


def test_external_stage_is_mandatory():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("chronoscope_workflow", root / "scripts/local/workflow.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(module.Failure, match="outside"):
        module.external(root / "data", root)


def test_owner_specific_prose_in_an_inherited_guard_is_refused(repo):
    import subprocess
    import sys

    script = repo / "scripts/check_owner_names.py"
    clean = subprocess.run([sys.executable, str(script), str(repo)], capture_output=True, text=True)
    assert clean.returncode == 0, clean.stdout
    first = json.loads((repo / "product.json").read_text())["holder"].split()[0]
    target = repo / "scripts/check_web_baseline.py"
    target.write_text(target.read_text() + "\n# " + first + "'s machine-specific exception\n")
    planted = subprocess.run([sys.executable, str(script), str(repo)], capture_output=True, text=True)
    assert planted.returncode == 1 and "check_web_baseline.py" in planted.stdout
