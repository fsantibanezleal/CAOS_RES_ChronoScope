"""Adversaries for output units, independent of a method's accuracy ranking."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from chronoscopelab import registry
from chronoscopelab.io.schema import FeatureRow, ForecastResult, MethodForecast
from chronoscopelab.io.units import check_forecast_units, require_forecast_units
from chronoscopelab.stages import export


def path(point):
    return {"name": "probe", "point": point, "lower": [v-10 for v in point], "upper": [v+10 for v in point]}


def test_wrong_normalized_output_blocks_but_poor_overlap_and_flat_fit_do_not():
    observed = [433, 450, 484]
    assert check_forecast_units(observed, [path([1, 1])])[0]["violation"] == "prediction_outside_observable"
    assert not check_forecast_units(observed, [path([390, 500])])
    advisory = require_forecast_units(observed, [path([450, 450])])
    assert advisory[0]["violation"] == "constant_prediction" and not advisory[0]["blocking"]


@pytest.mark.parametrize("factor,offset", [(1e-9, 0), (1e9, -3e10), (2, 1000)])
def test_unit_and_origin_changes_preserve_the_verdict(factor, offset):
    observed = [433, 450, 484]
    methods = [path([1, 1]), path([390, 500]), path([450, 450])]
    expected = check_forecast_units(observed, methods)
    transformed = [{k: [factor*v+offset for v in value] if k != "name" else value
                    for k, value in row.items()} for row in methods]
    got = check_forecast_units([factor*v+offset for v in observed], transformed)
    assert [(p["violation"], p["blocking"]) for p in got] == [(p["violation"], p["blocking"]) for p in expected]


@pytest.mark.parametrize("field,value", [("point", float("nan")), ("lower", float("inf")), ("upper", -float("inf"))])
def test_every_path_refuses_nonfinite_outputs(field, value):
    row = path([450, 451])
    row[field][0] = value
    with pytest.raises(ValueError, match="non_finite_prediction"):
        require_forecast_units([433, 484], [row])


def test_empty_mismatched_and_crossed_intervals_refuse():
    for row in (path([]), {**path([450]), "lower": []}, {**path([450]), "upper": [400]}):
        with pytest.raises(ValueError, match="gate refused"):
            require_forecast_units([433, 484], [row])


def test_adversarial_export_refuses_before_creating_any_file_including_redacted_paths(tmp_path):
    result = ForecastResult("probe", 2, 1, (.1, .5, .9), (433, 450, 484),
                            (MethodForecast("broken", "probe", (1, 1), (0, 0), (2, 2)),))
    for source in ("synthetic", "m5"):
        with pytest.raises(ValueError, match="outside_observable"):
            export.run(case=SimpleNamespace(id="probe", source=source), feature=None,
                       result=result, actual=[450, 460], eval_metrics={}, seed=0, run_ms=0,
                       flags=[], derived_dir=str(tmp_path/"derived"), manifests_dir=str(tmp_path/"manifests"))
        assert not list(tmp_path.iterdir())


def test_adversarial_flat_forecast_is_exported_and_recorded_without_altering_callers_flags(tmp_path):
    case = registry.get_case("SEAS_hourly")
    feature = FeatureRow(case.id, 5, 1, 450, 20, 0, 0, 0, 0)
    result = ForecastResult(case.id, 2, 1, (.1, .5, .9), (433, 450, 484),
                            (MethodForecast("level", "probe", (450, 450), (440, 440), (460, 460)),))
    flags = []
    manifest = export.run(case=case, feature=feature, result=result, actual=[450, 460], eval_metrics={},
                          seed=0, run_ms=0, flags=flags, derived_dir=str(tmp_path/"derived"),
                          manifests_dir=str(tmp_path/"manifests"))
    assert flags == []
    assert manifest["flags"][0]["code"] == "forecast-unit-advisory"
    assert manifest["flags"][0]["method"] == "level"
    trace = json.loads((tmp_path/"derived"/case.id/"trace.json").read_text(encoding="utf-8"))
    assert trace["methods"][0]["point"] == [450, 450]


def test_adversarial_artifact_sweep_refuses_a_tampered_existing_forecast(tmp_path):
    source = Path(__file__).resolve().parents[1] / "scripts/check_forecast_units.py"
    spec = importlib.util.spec_from_file_location("artifact_units", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    derived = tmp_path/"data/derived"
    (derived/"manifests").mkdir(parents=True)
    (derived/"probe").mkdir()
    (derived/"manifests/index.json").write_text(json.dumps({"cases": [{"case_id": "probe"}]}), encoding="utf-8")
    case = {"case_id": "probe", "history": [433, 450, 484], "actual": [440, 460], "methods": [path([450, 451])]}
    for name in ("reevaluation.json", "fresh-reevaluation.json"):
        (derived/name).write_text(json.dumps({"cases": [case]}), encoding="utf-8")
    trace = derived/"probe/trace.json"
    trace.write_text(json.dumps(case), encoding="utf-8")
    assert module.sweep(tmp_path)["blocking"] == []
    case["methods"] = [path([1, 1])]
    trace.write_text(json.dumps(case), encoding="utf-8")
    receipt = module.sweep(tmp_path)
    assert len(receipt["blocking"]) == 1
    assert receipt["blocking"][0]["artifact"] == "data/derived/probe/trace.json"
