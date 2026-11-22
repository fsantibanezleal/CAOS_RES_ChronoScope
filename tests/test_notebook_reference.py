"""The teaching reference boundary cannot accept future outcomes or swap a prefix."""
import json
import sys

import pytest

from engine import notebook_reference as reference


def test_adversarial_future_values_cannot_cross_reference_cli(tmp_path, monkeypatch):
    source, output = tmp_path / "in.json", tmp_path / "out.json"
    source.write_text(json.dumps({"history": list(range(100)), "actual": [101],
                                  "seasonality": 12, "horizon": 1, "methods": ["NLinear"]}))
    monkeypatch.setattr(sys, "argv", ["reference", "--input", str(source), "--output", str(output)])
    with pytest.raises(ValueError, match="Only history"):
        reference.main()
    assert not output.exists()


def test_adversarial_result_from_another_prefix_is_refused():
    request = reference._request(list(range(100)), 12, 1, ["NLinear"])
    other = reference._request(list(range(1, 101)), 12, 1, ["NLinear"])
    result = {"input_sha256": reference._digest(other),
              "methods": {"NLinear": {"quantiles": [[1, 2, 3]]}}}
    with pytest.raises(ValueError, match="another prefix"):
        reference._validate_result(request, result)


@pytest.mark.parametrize("path", [[[3, 2, 1]], [[float("nan"), 2, 3]], [[1, 2]], []])
def test_adversarial_invalid_reference_path_is_refused(path):
    request = reference._request(list(range(100)), 12, 1, ["NLinear"])
    result = {"input_sha256": reference._digest(request), "methods": {"NLinear": {"quantiles": path}}}
    with pytest.raises(ValueError, match="quantile paths"):
        reference._validate_result(request, result)


@pytest.mark.parametrize("methods", [[], ["cached forecast"], ["NLinear", "NLinear"]])
def test_adversarial_missing_or_relabelled_methods_are_refused(methods):
    with pytest.raises(ValueError, match="reference methods"):
        reference._request(list(range(100)), 12, 1, methods)
