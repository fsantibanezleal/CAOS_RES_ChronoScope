"""Normative schema checks plus adversarial payload changes against the actual corpus."""
import json
from pathlib import Path

import pytest

from contracts.contract_schemas import errors

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("schema,pattern", [
    ("trace", "data/derived/*/trace.json"),
    ("manifest", "data/derived/manifests/[!i]*.json"),
    ("index", "data/derived/manifests/index.json"),
    ("analysis", "data/derived/*/analysis.json"),
    ("streaming", "data/derived/*/streaming.json"),
    ("nlinear-model", "frontend/public/models/nlinear.json"),
    ("selector", "models/selector.json"),
    ("reevaluation", "data/derived/reevaluation.json"),
    ("reevaluation", "data/derived/fresh-reevaluation.json"),
])
def test_every_committed_boundary_document_matches_its_schema(schema, pattern):
    files = list(ROOT.glob(pattern))
    assert files
    for path in files:
        doc = json.loads(path.read_text())
        assert errors(schema, doc) == [], path


def test_adversarial_numeric_type_and_missing_required_field_are_rejected():
    trace = json.loads((ROOT / "data/derived/TRND_seasonal/trace.json").read_text())
    trace["methods"][0]["point"][0] = "a numerical forecast was replaced by text"
    assert errors("trace", trace)
    manifest = json.loads((ROOT / "data/derived/manifests/TRND_seasonal.json").read_text())
    del manifest["provenance"]["public_artifact_ok"]
    assert errors("manifest", manifest)


def test_selector_is_training_metadata_with_a_valid_default():
    model = json.loads((ROOT / "models/selector.json").read_text())
    assert errors("selector", model) == []
    assert model["default_method"] in [row[0] for row in model["ranking"]]
    assert model["metric"] == "mean_mase_over_training_cases"
