"""Corrupt actual corpus artifacts; the lightweight admission must reject each plant."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "corpus_admission", ROOT / "scripts/check_research_extensions.py"
)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


@pytest.fixture(scope="module")
def admitted_corpus():
    path = ROOT / "data/derived/forecastability.json"
    if not path.exists():
        pytest.skip("Complete corpus is still executing")
    d = json.loads(path.read_text(encoding="utf-8"))
    admission.validate_study(d)
    return d


@pytest.mark.parametrize(
    "plant",
    [
        "partial",
        "inventory",
        "duplicate",
        "partition",
        "score",
        "q",
        "confirmation",
        "source",
        "raw_source",
        "median",
        "origin",
    ],
)
def test_corpus_admission_rejects_corruption(admitted_corpus, plant):
    d = copy.deepcopy(admitted_corpus)
    if plant == "partial":
        d["complete"] = False
    elif plant == "inventory":
        d["series"].pop()
    elif plant == "duplicate":
        d["series"][1]["sequence_sha256"] = d["series"][0]["sequence_sha256"]
    elif plant == "partition":
        d["series"][0]["partition"] = "invalid"
    elif plant == "score":
        d["summary"]["selection_mean_mase"]["selected"] += 0.1
    elif plant == "q":
        d["summary"]["associations"][0]["discovery"]["q"] = 0.123456
    elif plant == "confirmation":
        d["summary"]["associations"][0]["confirmed"] = not d["summary"]["associations"][0]["confirmed"]
    elif plant == "source":
        d["code_sha256"][next(iter(d["code_sha256"]))] = "0" * 64
    elif plant == "raw_source":
        d["source_sha256"] = "0" * 64
    elif plant == "median":
        d["summary"]["discovery_medians"][0] += 1
    elif plant == "origin":
        d["series"][0]["origins"][0] += 1
    with pytest.raises(ValueError):
        admission.validate_study(d)
