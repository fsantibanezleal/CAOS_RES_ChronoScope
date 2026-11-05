"""Fresh experiment admission rejects partial, disguised and numerically altered evidence."""
import copy
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fresh_admission", ROOT / "scripts/check_fresh_reevaluation.py")
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


@pytest.fixture
def candidate():
    return json.loads((ROOT / "data/derived/fresh-reevaluation.json").read_text())


def test_complete_fresh_execution_has_independently_matching_scores(candidate):
    assert admission.validate(candidate) == (15, 22)


def test_adversarial_fresh_inventory_cannot_omit_a_transitive_engine(candidate):
    candidate["code_sha256"].pop("data-pipeline/chronoscopelab/engines/tirex2_engine.py")
    with pytest.raises(ValueError, match="inventory is incomplete"):
        admission.validate(candidate)


def test_adversarial_independent_module_does_not_relabel_frozen_experiment(candidate, tmp_path):
    shutil.copytree(ROOT / "data-pipeline/chronoscopelab", tmp_path / "data-pipeline/chronoscopelab",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/reevaluate_fresh.py", tmp_path / "scripts/reevaluate_fresh.py")
    # Exercise the strict current-source path with the actual original source
    # bytes, without installing the archive resolver receipt into this fixture.
    originals = admission.frozen_implementation(candidate, ROOT, ROOT)
    for rel, source in originals.items():
        destination = tmp_path/rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8", newline="\n")
    extra = tmp_path / "data-pipeline/chronoscopelab/model/independent_trial.py"
    extra.write_text("def trial():\n    return 7\n", encoding="utf-8")
    assert admission.validate(candidate, root=tmp_path, artifact_root=ROOT) == (15, 22)
    # Even a recorded module outside the import closure cannot change unnoticed.
    recorded = tmp_path / "data-pipeline/chronoscopelab/live.py"
    recorded.write_text(recorded.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source binding differs"):
        admission.validate(candidate, root=tmp_path, artifact_root=ROOT)


def test_adversarial_new_transitive_import_requires_its_own_binding(tmp_path):
    package = tmp_path / "data-pipeline/chronoscopelab"
    (package / "model").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/reevaluate_fresh.py").write_text("from chronoscopelab.model import first\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "model/__init__.py").write_text("", encoding="utf-8")
    first = package / "model/first.py"
    first.write_text("from . import second\n", encoding="utf-8")
    (package / "model/second.py").write_text("from .. import third\n", encoding="utf-8")
    (package / "third.py").write_text("", encoding="utf-8")
    expected = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.py")}
    assert admission.implementation_dependencies(tmp_path) == expected


@pytest.mark.parametrize("defect", ["trial", "case", "method", "frozen", "metric", "target", "source", "checkpoint", "duration"])
def test_adversarial_fresh_admission_refutes_corrupted_candidate(candidate, defect):
    damaged = copy.deepcopy(candidate)
    if defect == "trial":
        damaged["protocol"]["name"] = "single-case fresh trial"
    elif defect == "case":
        damaged["cases"].pop()
    elif defect == "method":
        damaged["cases"][0]["methods"].pop()
    elif defect == "frozen":
        damaged["cases"][0]["methods"][0]["source"] = "frozen released forecast"
    elif defect == "metric":
        damaged["cases"][0]["methods"][0]["metrics"]["mae"] += 0.1
    elif defect == "target":
        damaged["cases"][0]["actual"][0] += 1
    elif defect == "source":
        damaged["source_comparison_sha256"] = "0" * 64
    elif defect == "checkpoint":
        damaged["runtime"]["checkpoint_revisions"].pop("NX-AI/TiRex-2")
    elif defect == "duration":
        damaged["cases"][0]["methods"][0]["fit_inference_seconds"] = -1
    with pytest.raises(ValueError):
        admission.validate(damaged)


def test_adversarial_native_tirex_cannot_map_arbitrary_levels_to_deciles():
    from chronoscopelab.engines.tirex2_engine import decile_columns

    assert decile_columns((0.1, 0.5, 0.9)) == [0, 4, 8]
    for levels in ((0.05, 0.5, 0.95), (0, 0.5, 1), (0.11, 0.5, 0.9)):
        with pytest.raises(ValueError, match="decile"):
            decile_columns(levels)


@pytest.fixture
def frozen_source_fixture(tmp_path):
    for rel in ("docs/research/fresh-source-archive.json", "docs/research/fresh-source-2026-11-01.zip",
                "data/derived/fresh-reevaluation.json"):
        destination = tmp_path/rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, destination)
    return tmp_path


def test_historical_sources_remain_exact_while_the_current_export_adds_a_guard(candidate, frozen_source_fixture):
    sources = admission.frozen_implementation(candidate, frozen_source_fixture, frozen_source_fixture)
    relative = "data-pipeline/chronoscopelab/stages/export.py"
    import hashlib
    assert hashlib.sha256(sources[relative].encode()).hexdigest() == candidate["code_sha256"][relative]
    assert "require_forecast_units" not in sources[relative]
    assert "require_forecast_units" in (ROOT/relative).read_text(encoding="utf-8")
    assert admission.implementation_dependencies(frozen_source_fixture, sources) <= set(sources)


@pytest.mark.parametrize("defect", ["archive-bytes", "source-bytes", "missing-member", "redirect", "artifact"])
def test_adversarial_frozen_sources_refuse_tampering(candidate, frozen_source_fixture, defect):
    root = frozen_source_fixture
    receipt_path = root/"docs/research/fresh-source-archive.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    archive_path = root/receipt["archive"]
    if defect in ("source-bytes", "missing-member"):
        with zipfile.ZipFile(archive_path) as archive:
            sources = {name: archive.read(name) for name in archive.namelist()}
        key = next(iter(sources))
        if defect == "source-bytes":
            sources[key] += b"\n# changed historical source\n"
        else:
            del sources[key]
        with zipfile.ZipFile(archive_path, "w") as archive:
            for name, raw in sources.items():
                archive.writestr(name, raw)
        receipt["archive_sha256"] = admission.digest(archive_path)
    elif defect == "archive-bytes":
        archive_path.write_bytes(archive_path.read_bytes() + b"changed")
    elif defect == "redirect":
        receipt["archive"] = "../escape.zip"
    else:
        (root/receipt["artifact"]).write_bytes(b"{}")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="Frozen"):
        admission.frozen_implementation(candidate, root, root)


def test_a_new_binding_inventory_cannot_claim_the_historical_archive(candidate, frozen_source_fixture):
    changed = copy.deepcopy(candidate)
    changed["code_sha256"]["new/source.py"] = "0"*64
    assert admission.frozen_implementation(changed, frozen_source_fixture, frozen_source_fixture) is None
