"""Adversarial coverage for the fail-closed author-time dimensional inventory."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("unit_constants_gate", ROOT / "scripts/check_unit_constants.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture_source(tmp_path, content="def ratio(normalized):\n    return normalized * 0.5\n", suffix=".py"):
    directory = tmp_path / ("data-pipeline/engine" if suffix == ".py" else "frontend/src/lib")
    directory.mkdir(parents=True)
    path = directory / ("method" + suffix)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def reviewed(current):
    result = copy.deepcopy(current)
    result["identity_review"] = {"status": "reviewed", "justification": "The fixture provider/compiler identity is explicitly reviewed and bound to this source inventory."}
    for record in result["files"].values():
        record.update(review_status="reviewed", review_justification="The fixture source is scoped and its normalized numeric operation was reviewed.")
        for row in record["literals"]:
            row.update(status="reviewed", quantity="Fixture normalized ratio coefficient",
                       unit="normalized-coordinate ratio",
                       justification="The fixture's argument is already normalized; this multiplies its ratio.")
    return result


def test_adversarial_unreviewed_dimensional_floor_refuses(tmp_path):
    path = fixture_source(tmp_path)
    baseline = reviewed(gate.inventory(tmp_path))
    assert gate.findings(gate.inventory(tmp_path), baseline) == []
    path.write_text("def ratio(raw_sigma):\n    return max(raw_sigma, 1e-9)\n", encoding="utf-8")
    problems = gate.findings(gate.inventory(tmp_path), baseline)
    assert any("source changed" in problem for problem in problems)
    assert any("Literal or expression differs" in problem for problem in problems)


def test_adversarial_changed_literal_is_not_grandfathered(tmp_path):
    path = fixture_source(tmp_path)
    baseline = reviewed(gate.inventory(tmp_path))
    path.write_text("def ratio(normalized):\n    return normalized * 0.75\n", encoding="utf-8")
    current = gate.inventory(tmp_path)
    draft = gate.pending_baseline(current, baseline)
    assert any("awaits dimensional review" in problem for problem in gate.findings(current, draft))
    assert draft["files"]["data-pipeline/engine/method.py"]["literals"][0]["unit"] is None


def test_adversarial_baseline_drift_and_generic_justification_refuse(tmp_path):
    fixture_source(tmp_path)
    current = gate.inventory(tmp_path)
    baseline = reviewed(current)
    row = baseline["files"]["data-pipeline/engine/method.py"]["literals"][0]
    row.update(literal="0.25", unit="dimensionless", justification="constant")
    problems = gate.findings(current, baseline)
    assert any("Literal or expression differs" in problem for problem in problems)
    assert any("Missing specific unit" in problem for problem in problems)
    assert any("Insufficient quantity rationale" in problem for problem in problems)


@pytest.mark.parametrize("suffix,source", [
    (".py", "def broken(:\n return 1.0\n"),
    (".ts", "export function broken( { return 1.0;\n"),
])
def test_adversarial_parse_failure_cannot_be_an_empty_pass(tmp_path, suffix, source):
    fixture_source(tmp_path, source, suffix)
    with pytest.raises((SyntaxError, ValueError)):
        gate.inventory(tmp_path)


def test_adversarial_new_numeric_free_source_is_reviewed_too(tmp_path):
    path = fixture_source(tmp_path)
    baseline = reviewed(gate.inventory(tmp_path))
    path.with_name("new_method.py").write_text("def hidden(x):\n    return x\n", encoding="utf-8")
    assert any("Unreviewed source" in problem for problem in gate.findings(gate.inventory(tmp_path), baseline))
    current = gate.inventory(tmp_path)
    draft = gate.pending_baseline(current, baseline)
    assert any("Source awaits scope/dimensional review" in problem for problem in gate.findings(current, draft))


def test_adversarial_git_line_endings_preserve_only_logical_source_identity(tmp_path):
    path = fixture_source(tmp_path)
    baseline = reviewed(gate.inventory(tmp_path))
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert gate.findings(gate.inventory(tmp_path), baseline) == []
    path.write_bytes(path.read_bytes().replace(b"0.5", b"0.75"))
    assert gate.findings(gate.inventory(tmp_path), baseline)


def test_adversarial_integer_rounding_and_typescript_exponents_are_inventoried(tmp_path):
    fixture_source(tmp_path, "export const output = Math.max(rawStd, 1);\nconst tiny = 1e-12;\n", ".ts")
    current = gate.inventory(tmp_path)
    rows = current["files"]["frontend/src/lib/method.ts"]["literals"]
    assert [row["literal"] for row in rows] == ["1", "1e-12"]
    fixture_source(tmp_path, "def output(raw):\n    return round(raw, 4)\n")
    rows = gate.inventory(tmp_path)["files"]["data-pipeline/engine/method.py"]["literals"]
    assert [row["literal"] for row in rows] == ["4"]


def test_adversarial_provider_identity_and_source_removal_refuse(tmp_path):
    path = fixture_source(tmp_path)
    current = gate.inventory(tmp_path)
    baseline = reviewed(current)
    baseline["provider"]["version"] = "different"
    assert "Reviewed provider identity changed" in gate.findings(current, baseline)
    update = gate.pending_baseline(current, baseline)
    assert "Provider/compiler identity awaits review" in gate.findings(current, update)
    other = path.with_name("replacement.py")
    path.replace(other)
    problems = gate.findings(gate.inventory(tmp_path), baseline)
    assert any("source disappeared" in problem for problem in problems)


@pytest.mark.parametrize("field", ["provider", "typescript", "source_hash_policy"])
def test_adversarial_identity_update_cannot_inherit_review(tmp_path, field):
    fixture_source(tmp_path)
    current = gate.inventory(tmp_path)
    baseline = reviewed(current)
    baseline[field] = {"name": "forecastscope", "version": "changed"} if field == "provider" else "changed"
    assert any("identity changed" in finding for finding in gate.findings(current, baseline))
    updated = gate.pending_baseline(current, baseline)
    assert "Provider/compiler identity awaits review" in gate.findings(current, updated)


@pytest.mark.parametrize("suffix", [".tsx", ".jsx", ".js", ".mts", ".mjs"])
def test_adversarial_new_tsx_method_cannot_escape_inventory(tmp_path, suffix):
    fixture_source(tmp_path)
    baseline = reviewed(gate.inventory(tmp_path))
    target = tmp_path / "frontend/src/lib"
    target.mkdir(parents=True)
    (target / ("new_method" + suffix)).write_text("export const amplitude = 1e-9;\n", encoding="utf-8")
    current = gate.inventory(tmp_path)
    assert current["files"]["frontend/src/lib/new_method" + suffix]["literals"][0]["literal"] == "1e-9"
    assert any("Unreviewed source" in problem for problem in gate.findings(current, baseline))


def test_adversarial_production_inventory_requires_every_annotation():
    provider, version = gate.installed_provider()
    current = gate.inventory(ROOT, provider, version)
    baseline = json.loads(gate.BASELINE.read_text(encoding="utf-8"))
    assert gate.findings(current, baseline) == []
