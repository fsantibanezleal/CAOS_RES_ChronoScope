"""Resealing hashes cannot conceal incorrect scientific scores or splits."""
import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("browser_evidence", Path(__file__).resolve().parents[1] /
                                             "scripts/check_browser_linear_evidence.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def copied(tmp_path, name):
    destination = tmp_path / name
    shutil.copytree(checker.EVIDENCE / name, destination)
    return destination


def reseal(directory, name, value):
    (directory / name).write_bytes(gzip.compress((json.dumps(value, sort_keys=True, indent=2) + "\n").encode(), mtime=0))
    result = json.loads((directory / "results.json").read_text())
    result["artifacts"][name] = checker.sha(directory / name)
    write_json(directory / "results.json", result)


def test_complete_stored_evidence_is_independently_scored():
    assert [r["test_series"] for r in checker.validate()] == [400, 800]


def test_adversarial_resealed_forecast_does_not_reproduce_reported_score(tmp_path):
    directory = copied(tmp_path, "v1")
    forecasts = json.loads(gzip.decompress((directory / "forecasts.json.gz").read_bytes()))
    forecasts[0]["methods"]["held_out_ridge"]["point"][0] += 100
    reseal(directory, "forecasts.json.gz", forecasts)
    with pytest.raises(ValueError, match="Evidence mismatch"):
        checker.validate_directory(directory, set())


def test_adversarial_source_cannot_be_removed_from_provenance(tmp_path):
    directory = copied(tmp_path, "v1")
    result = json.loads((directory / "results.json").read_text())
    del result["sources"]["scripts/train_nlinear_onnx.py"]
    write_json(directory / "results.json", result)
    with pytest.raises(ValueError, match="source inventory"):
        checker.validate_directory(directory, set())


def test_adversarial_split_overlap_is_refused_after_resealing(tmp_path):
    directory = copied(tmp_path, "v1")
    series = json.loads(gzip.decompress((directory / "series.json.gz").read_bytes()))
    first = series["training"][0]
    series["validation"][0].update(values=first["values"], sha256=first["sha256"])
    reseal(directory, "series.json.gz", series)
    with pytest.raises(ValueError, match="overlapping"):
        checker.validate_directory(directory, set())


def test_adversarial_confirmation_cannot_change_point_forecasts(tmp_path):
    directory = copied(tmp_path, "confirmation-v1")
    forecasts = json.loads(gzip.decompress((directory / "forecasts.json.gz").read_bytes()))
    forecasts[0]["methods"]["stratified"]["point"][0] += 1
    reseal(directory, "forecasts.json.gz", forecasts)
    with pytest.raises(ValueError, match="changed a point"):
        checker.validate_directory(directory, set())


def test_adversarial_engineering_pass_cannot_override_an_actual_failed_condition(tmp_path):
    directory = copied(tmp_path, "confirmation-v1")
    result = json.loads((directory / "results.json").read_text())
    result["max_normalized_runtime_error"] = 1
    write_json(directory / "results.json", result)
    with pytest.raises(ValueError, match="engineering admission"):
        checker.validate_directory(directory, set())
