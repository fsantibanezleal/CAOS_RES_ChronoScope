"""Fresh experiment admission rejects partial, disguised and numerically altered evidence."""
import copy
import importlib.util
import json
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
