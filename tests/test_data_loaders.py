"""Loader tests: the committed public-safe sample CSVs are valid Contract-1 series and their cases bake.

These test the COMMITTED samples (not the vault, which is not present in CI), so they run anywhere. The vault
loaders themselves are exercised offline by `refresh_samples`.
"""
import csv
from pathlib import Path

from chronoscopelab import registry
from chronoscopelab.io.contract import validate_series

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


def _read_long(name: str):
    with open(EXAMPLES / name, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r["ds"] for r in rows], [float(r["y"]) for r in rows]


def test_electricity_sample_is_a_valid_contract1_series():
    ds, y = _read_long("electricity_sample.csv")
    assert len(y) >= 200
    rec, rej, _flag = validate_series("MT_010", ds, y)
    assert rec is not None and rej is None


def test_beijing_pm25_sample_is_a_valid_contract1_series():
    ds, y = _read_long("beijing_pm25_sample.csv")
    assert len(y) >= 200
    rec, rej, _flag = validate_series("BEIJING_PM25", ds, y)
    assert rec is not None and rej is None


def test_real_cases_reference_public_safe_sources():
    from chronoscopelab.data import provenance as pv
    for case_id in ("REAL_electricity", "REAL_pm25"):
        case = registry.get_case(case_id)
        assert pv.public_artifact_ok(case.source) is True    # CC-BY -> derived artifacts may ship


def test_real_pm25_case_builds_and_is_heavy_tailed():
    spec = registry.build_series(registry.get_case("REAL_pm25"), seed=42)
    assert len(spec.y) >= 200
    # pollution spikes make PM2.5 strongly non-normal (heavy right tail) - a real property the data should show
    from chronoscopelab.analysis import distribution as di
    summ = di.summary(list(spec.y))
    assert summ.normal is False
    assert summ.skewness > 0.5
