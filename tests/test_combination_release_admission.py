"""A complete study cannot disappear or change during local artifact promotion."""

from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil

import pytest
from test_bootstrap_regressions import directory_alias

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def admission(tmp_path):
    spec = importlib.util.spec_from_file_location("combination_admission", ROOT / "scripts/local/producer_bridge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    files = {
        "data/derived/combinations/study/series.json": b'{"origins":[1]}\n',
        "data/derived/reevaluation.json": b'{"cases":[1]}\n',
        "scripts/export_combination_study.py": b"# frozen exporter\n",
        "data-pipeline/method.py": b"# frozen method\n",
        "manuscripts/method/evidence/full.json.gz": b"frozen complete audit",
    }
    for name, content in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def sha(name):
        return hashlib.sha256(files[name]).hexdigest()

    index = {
        "cases": [{"path": "combinations/study/series.json"}],
        "code_sha256": {"data-pipeline/method.py": sha("data-pipeline/method.py")},
        "export_code_sha256": sha("scripts/export_combination_study.py"),
        "selected_case_source_sha256": sha("data/derived/reevaluation.json"),
        "audit": {"path": "manuscripts/method/evidence/full.json.gz",
                  "sha256": sha("manuscripts/method/evidence/full.json.gz")},
    }
    (source / "data/derived/validated-combinations.json").write_text(json.dumps(index), encoding="utf-8")
    stage = tmp_path / "stage"
    shutil.copytree(source, stage)
    return module, source, stage


def test_complete_released_study_is_carried_without_fitting(admission):
    module, source, stage = admission
    assert module.validate_combination_release(stage, source) == 1


@pytest.mark.parametrize("name", [
    "data/derived/validated-combinations.json",
    "data/derived/combinations/study/series.json",
    "data/derived/reevaluation.json",
    "manuscripts/method/evidence/full.json.gz",
])
@pytest.mark.parametrize("change", ["delete", "alter"])
def test_adversarial_missing_or_changed_release_payload_is_refused(admission, name, change):
    module, source, stage = admission
    path = stage / name
    if change == "delete":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="combination|Combination"):
        module.validate_combination_release(stage, source)


@pytest.mark.parametrize("name", ["data-pipeline/method.py", "scripts/export_combination_study.py"])
def test_stale_method_or_exporter_binding_is_refused(admission, name):
    module, source, stage = admission
    (source / name).write_bytes(b"changed implementation\n")
    with pytest.raises(ValueError, match="implementation binding"):
        module.validate_combination_release(stage, source)


def test_unindexed_series_cannot_enter_the_admitted_study(admission):
    module, source, stage = admission
    (stage / "data/derived/combinations/study/extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="indexed inventory"):
        module.validate_combination_release(stage, source)


def test_index_cannot_redirect_a_payload_outside_the_stage(admission):
    module, source, stage = admission
    name = "data/derived/validated-combinations.json"
    index = json.loads((source / name).read_text(encoding="utf-8"))
    index["cases"][0]["path"] = "../../../private.json"
    for base in (source, stage):
        (base / name).write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ValueError, match="indexed inventory|redirected"):
        module.validate_combination_release(stage, source)


def test_parent_alias_is_refused_even_when_its_target_stays_inside_the_stage(admission):
    module, source, stage = admission
    alias = stage / "data/derived/combinations/study"
    target = stage / "data/derived/relocated-study"
    alias.rename(target)
    directory_alias(alias, target)
    try:
        with pytest.raises(ValueError, match="redirected"):
            module.validate_combination_release(stage, source)
    finally:
        if os.name == "nt":
            alias.rmdir()
        else:
            alias.unlink()


def test_real_configuration_stages_every_indexed_document_and_full_audit():
    config = json.loads((ROOT / "scripts/local/workflow.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))
    expected = {"data/derived/" + entry["path"] for entry in index["cases"]}
    expected.update({"data/derived/validated-combinations.json", index["audit"]["path"]})
    assert expected <= set(config["stage_inputs"])
