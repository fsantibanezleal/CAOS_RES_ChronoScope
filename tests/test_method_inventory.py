"""A grouped label cannot hide a measured model or a bundled diagnostic."""
from pathlib import Path
import copy
import importlib.util
import shutil

import pytest

spec = importlib.util.spec_from_file_location(
    "method_inventory", Path(__file__).resolve().parents[1] / "scripts/method_inventory.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_complete_inventory_resolves_to_implemented_methods():
    module.validate(module.catalog())


def test_adversarial_measured_method_cannot_disappear():
    rows = [row for row in module.catalog() if row["artifact_name"] != "NLinear (nf)"]
    with pytest.raises(ValueError, match="incomplete"):
        module.validate(rows)


def test_adversarial_unimplemented_callable_is_refused():
    rows = copy.deepcopy(module.catalog())
    rows[0]["implementation"] = rows[0]["implementation"].split("::")[0] + "::absent_forecaster"
    with pytest.raises(ValueError, match="Unimplemented callable"):
        module.validate(rows)


def test_adversarial_bundled_components_have_independent_identities():
    rows = [row for row in module.catalog() if row["id"] != "analysis/fractal/katz"]
    assert any(row["id"] == "analysis/fractal/higuchi" for row in rows)
    with pytest.raises(ValueError, match="incomplete"):
        module.validate(rows)


def test_adversarial_historical_predictor_identity_is_not_collapsed():
    rows = [row for row in module.catalog() if row["scope"] != "historical-reconstruction"]
    assert any(row["id"] == "forecast/Theta" for row in rows)
    with pytest.raises(ValueError, match="incomplete"):
        module.validate(rows)


def test_adversarial_new_public_analysis_cannot_be_hidden_by_grouping(tmp_path):
    source = module.ROOT / module.ENGINE / "analysis"
    destination = tmp_path / module.ENGINE / "analysis"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
    path = destination / "stationarity.py"
    path.write_text(path.read_text(encoding="utf-8") + "\ndef new_estimator(values):\n    return 0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Uninventoried analysis API.*new_estimator"):
        module.validate_analysis_api(module.catalog(), tmp_path)
