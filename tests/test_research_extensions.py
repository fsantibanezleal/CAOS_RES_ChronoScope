"""Admission plants against the actual exported research artifacts."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "research_admission", ROOT / "scripts/check_research_extensions.py"
)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


def test_all_original_case_diagnostics_are_admitted():
    assert admission.validate_diagnostics() == 15


def test_source_restrictions_do_not_leak_even_a_short_sequence():
    from chronoscopelab.stages.export import _redact_analysis

    restricted = _redact_analysis({"sequence": {"values": [1.0, 2.0, 3.0], "n": 3}})
    assert restricted["sequence"]["available"] is False
    assert "values" not in restricted["sequence"]


@pytest.mark.skipif(
    not (ROOT / "data/derived/forecastability.json").exists(), reason="Corpus candidate still executing"
)
@pytest.mark.parametrize("plant", ["partial", "partition", "score", "q", "confirmation", "source", "median"])
def test_corrupt_corpus_is_rejected(plant):
    d = json.loads((ROOT / "data/derived/forecastability.json").read_text())
    admission.validate_study(d)
    altered = copy.deepcopy(d)
    if plant == "partial":
        altered["complete"] = False
    elif plant == "partition":
        altered["series"][0]["partition"] = "invalid"
    elif plant == "score":
        altered["summary"]["selection_mean_mase"]["selected"] += 0.1
    elif plant == "q":
        altered["summary"]["associations"][0]["discovery"]["q"] = 0.123456
    elif plant == "confirmation":
        altered["summary"]["associations"][0]["confirmed"] = not altered["summary"]["associations"][0][
            "confirmed"
        ]
    elif plant == "source":
        altered["code_sha256"][next(iter(altered["code_sha256"]))] = "0" * 64
    elif plant == "median":
        altered["summary"]["discovery_medians"][0] += 1
    with pytest.raises(ValueError):
        admission.validate_study(altered)
