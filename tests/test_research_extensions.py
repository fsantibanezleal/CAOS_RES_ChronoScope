"""Admission plants against the actual exported research artifacts."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "research_admission", ROOT / "scripts/check_research_extensions.py"
)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


@pytest.fixture(autouse=True)
def _sandbox_pipeline_writes():
    """Read-only admission plants need no scientific imports in the lightweight CI job."""
    return None


def test_all_original_case_diagnostics_are_admitted():
    assert admission.validate_diagnostics() == 15


def test_source_restrictions_do_not_leak_even_a_short_sequence():
    from chronoscopelab.stages.export import _redact_analysis

    restricted = _redact_analysis({"sequence": {"values": [1.0, 2.0, 3.0], "n": 3}})
    assert restricted["sequence"]["available"] is False
    assert "values" not in restricted["sequence"]
