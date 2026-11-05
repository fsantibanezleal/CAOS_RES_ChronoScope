"""Custom admission receives the same immutable receipt guarantees as generic readiness."""

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import pytest

from test_local_bootstrap import fixture_repo as fixture_repo
from test_local_bootstrap import workflow as workflow

ROOT = Path(__file__).resolve().parents[1]


def test_custom_admission_returns_a_bound_receipt(workflow, fixture_repo):
    root, config, env = fixture_repo
    config["product_admission"] = True
    (root / "scripts/local/workflow.json").write_text(json.dumps(config), encoding="utf-8")
    stage = workflow.generate(root, config, env)
    admitted = workflow.validate_stage(root, config, stage, sys.executable, env, receipt=True)
    assert admitted["files"] == workflow.payload_hashes(stage, config)
    assert admitted["receipt_sha256"] == workflow.digest(stage / "local-generation.json")
    workflow.promote(root, config, stage, sys.executable, env)
    assert (root / "models/model.json").read_bytes() == (stage / "models/model.json").read_bytes()


def test_adversarial_custom_validator_cannot_mutate_payload_after_checking(workflow, fixture_repo, monkeypatch):
    root, config, env = fixture_repo
    config["product_admission"] = True
    (root / "scripts/local/workflow.json").write_text(json.dumps(config), encoding="utf-8")
    stage = workflow.generate(root, config, env)
    original = workflow.commands

    def mutate_after_validation(*args):
        original(*args)
        (stage / "models/model.json").write_text('{"changed_after_validation":true}', encoding="utf-8")

    monkeypatch.setattr(workflow, "commands", mutate_after_validation)
    with pytest.raises(workflow.Failure, match="changed after admission"):
        workflow.validate_stage(root, config, stage, sys.executable, env, receipt=True)


def test_actual_product_generates_and_admits_a_complete_external_candidate(workflow, tmp_path, monkeypatch):
    root = tmp_path / "actual product with spaces"
    ignored = shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules", "dist")
    for name in ("data-pipeline", "scripts", "docs/contracts", "data", "models", "manuscripts",
                 "docs/research/browser-linear", "docs/guides", "frontend/src/lib", "frontend/public/models"):
        shutil.copytree(ROOT / name, root / name, ignore=ignored)
    for pattern in ("requirements*.txt",):
        for source in ROOT.glob(pattern):
            shutil.copy2(source, root / source.name)
    for name in ("VERSION", "product.json"):
        shutil.copy2(ROOT / name, root / name)
    for name in ("fresh-source-archive.json", "fresh-source-2026-11-01.zip"):
        shutil.copy2(ROOT / "docs/research" / name, root / "docs/research" / name)
    shutil.copytree(ROOT / "app", root / "app", ignore=ignored)
    config = workflow.settings(root)
    monkeypatch.setattr(workflow, "generation_python", lambda *_: Path(sys.executable))
    env = {**os.environ, "CAOS_TEMP_ROOT": str(tmp_path / "external candidates"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    original = workflow.payload_hashes(root, config)
    stage = workflow.generate(root, config, env)
    assert not stage.is_relative_to(root)
    assert workflow.payload_hashes(root, config) == original
    receipt = workflow.validate_stage(root, config, stage, sys.executable, env, receipt=True)
    assert receipt["files"] == workflow.payload_hashes(stage, config)
    assert len(list((stage / "data/derived/combinations").glob("*/*.json"))) == 1802
    for name in config["stage_inputs"]:
        assert (stage / name).read_bytes() == (root / name).read_bytes()


def test_frontend_copies_only_the_admitted_canonical_corpus(tmp_path):
    root = tmp_path / "canonical frontend input"
    (root / "frontend").mkdir(parents=True)
    shutil.copy2(ROOT / "frontend/copy-data.mjs", root / "frontend/copy-data.mjs")
    (root / "frontend/src/lib").mkdir(parents=True)
    shutil.copy2(ROOT / "frontend/src/lib/browserCalibration.json", root / "frontend/src/lib/browserCalibration.json")
    derived = root / "data/derived"
    derived.mkdir(parents=True)
    (derived / "canonical.json").write_text('{"source":"admitted"}', encoding="utf-8")
    untrusted = tmp_path / "unrelated global input"
    untrusted.mkdir()
    (untrusted / "wrong.json").write_text("{}", encoding="utf-8")
    result = subprocess.run(["node", "copy-data.mjs"], cwd=root / "frontend", capture_output=True,
                            env={**os.environ, "CAOS_DATA_ROOT": str(untrusted)}, check=False)
    assert result.returncode == 0, result.stderr
    output = root / "frontend/public/data"
    assert {p.name for p in output.iterdir()} == {"canonical.json"}
    assert (output / "canonical.json").read_bytes() == (derived / "canonical.json").read_bytes()
    shutil.rmtree(derived)
    result = subprocess.run(["node", "copy-data.mjs"], cwd=root / "frontend", capture_output=True,
                            env={**os.environ, "CAOS_DATA_ROOT": str(untrusted)}, check=False)
    assert result.returncode != 0 and b"Canonical data/derived is missing" in result.stderr
