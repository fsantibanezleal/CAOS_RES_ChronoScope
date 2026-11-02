"""Fresh experiment admission rejects partial, disguised and numerically altered evidence."""
import copy
import importlib.util
import json
import shutil
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
