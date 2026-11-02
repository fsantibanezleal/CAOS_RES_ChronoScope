"""Normative new boundaries reject malformed data and preserve inventory identity."""

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_index_validates_and_accounts_for_every_source_identity():
    index = read("data/derived/validated-combinations.json")
    schema = read("docs/contracts/schemas/combination-index.schema.json")
    Draft202012Validator(schema).validate(index)
    assert len({(c["dataset"], c["id"]) for c in index["cases"]}) == 1802
    for cohort in index["cohorts"]:
        entries = [c for c in index["cases"] if c["dataset"] == cohort["id"]]
        assert len(entries) == cohort["inventory"] == cohort["admitted"] + cohort["excluded"]
        assert sum(not c.get("excluded") for c in entries) == cohort["admitted"]


def test_adversarial_index_rejects_a_traversal_path_and_unlicensed_source():
    index = read("data/derived/validated-combinations.json")
    validator = Draft202012Validator(read("docs/contracts/schemas/combination-index.schema.json"))
    bad = copy.deepcopy(index)
    bad["cases"][0]["path"] = "../../private.json"
    assert list(validator.iter_errors(bad))
    bad = copy.deepcopy(index)
    bad["sources"]["m4_weekly"]["license"] = "restricted"
    assert list(validator.iter_errors(bad))


def test_adversarial_case_rejects_missing_quantile_columns_and_retains_parameters():
    row = read("data/derived/combinations/m4_weekly/T1.json")
    validator = Draft202012Validator(read("docs/contracts/schemas/combination-case.schema.json"))
    validator.validate(row)
    model = next(m for m in row["origins"][0]["methods"] if m["name"] == "ValidationMix")
    assert len(model["selected"]) == 3 and len(model["weights"]) == 5
    bad = copy.deepcopy(row)
    bad["origins"][0]["methods"][0]["quantiles"][0] = [1.0, 2.0]
    assert list(validator.iter_errors(bad))
