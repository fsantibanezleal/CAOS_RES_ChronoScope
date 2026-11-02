"""Source-derived eligibility cannot silently remove an unfavorable series or origin."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest


spec = importlib.util.spec_from_file_location(
    "combination_admission", Path(__file__).resolve().parents[1] / "scripts/check_combination_study.py"
)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


def test_adversarial_eligible_series_cannot_be_excluded_as_short_or_unscaled():
    y = np.arange(180, dtype=float)
    for reason in ("nonfinite observations or no eligible origin",
                   "unavailable seasonal MASE scale at an outer origin"):
        with pytest.raises(AssertionError, match="incorrectly excluded"):
            admission.admit_eligibility({"source_n": len(y), "excluded": reason, "origins": []}, y, 13, 52)


def test_adversarial_origin_cannot_be_dropped_or_borrowed_from_the_future():
    y = np.arange(180, dtype=float)
    for origins in ([141, 154], [141, 154, 168]):
        with pytest.raises(AssertionError, match="Incomplete outer schedule"):
            admission.admit_eligibility({"source_n": len(y), "origins": [{"origin": o} for o in origins]}, y, 13, 52)
    assert admission.admit_eligibility(
        {"source_n": len(y), "origins": [{"origin": o} for o in (141, 154, 167)]}, y, 13, 52
    ) == [141, 154, 167]


def test_short_and_constant_sources_have_independently_valid_exclusions():
    for y, reason in ((np.arange(100.), "nonfinite observations or no eligible origin"),
                      (np.ones(180), "unavailable seasonal MASE scale at an outer origin")):
        admission.admit_eligibility({"source_n": len(y), "excluded": reason, "origins": []}, y, 13, 52)
